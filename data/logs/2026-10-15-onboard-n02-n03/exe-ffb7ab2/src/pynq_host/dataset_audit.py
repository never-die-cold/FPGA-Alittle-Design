"""Leakage and coverage checks; structure PASS does not certify labels or accuracy."""
from collections import Counter
from dataset_manifest import CLASSES, ORIENTATION_COMBOS, load_manifest

SOURCE_KINDS = ("TEST_FIXTURE", "PUBLIC", "DECLARED_PYNQ")


def audit_dataset(root, source_kind, max_targets=10):
    if source_kind not in SOURCE_KINDS:
        raise ValueError("dataset source kind must be explicitly declared")
    manifest = load_manifest(root, max_targets)
    owners = {name: {} for name in ("session", "source_sha256", "pixels_sha256", "specimen_id")}
    specimen_classes, missing_specimens, missing_orientations = {}, 0, 0
    coverage = {split: {"frames": 0, "targets": 0, "empty_frames": 0,
                       "classes": dict.fromkeys(CLASSES, 0), "lights": Counter(),
                       "backgrounds": Counter(), "spacing": Counter(), "frame_target_counts": Counter(),
                       "orientations": Counter(), "class_orientations": Counter(),
                       "orientation_lights": Counter()}
                for split in ("train", "val", "test")}
    for frame in manifest["frames"]:
        split, targets = frame["split"], frame["targets"]
        identities = [(name, frame[name]) for name in ("session", "source_sha256", "pixels_sha256")]
        for target in targets:
            identity = target["specimen_id"]
            if identity:
                identities.append(("specimen_id", identity))
                if specimen_classes.setdefault(identity, target["class"]) != target["class"]:
                    raise ValueError("specimen has conflicting class labels")
            else:
                missing_specimens += 1
            if not target["orientation"]:
                missing_orientations += 1
        for name, identity in identities:
            if owners[name].setdefault(identity, split) != split:
                raise ValueError(f"cross-split leakage: {name}")
        row = coverage[split]
        row["frames"] += 1
        row["targets"] += len(targets)
        row["empty_frames"] += int(frame["empty_scene"])
        row["lights"][frame["light"]] += 1
        row["backgrounds"][frame["bg"]] += 1
        row["spacing"][frame["spacing"]] += 1
        row["frame_target_counts"][str(len(targets))] += 1
        for target in targets:
            row["classes"][target["class"]] += 1
            token = target["orientation"] or "unlabeled"
            row["orientations"][token] += 1
            row["class_orientations"][f"{target['class']}/{token}"] += 1
            row["orientation_lights"][f"{target['class']}/{token}/{frame['light']}"] += 1
    total_frames = len(manifest["frames"])
    total_targets = sum(row["targets"] for row in coverage.values())
    return {"schema_version": 2, "mode": "DATASET_STRUCTURE_AUDIT", "status": "STRUCTURE_PASS",
            "source_kind": source_kind, "capture_origin_authenticated": False, "label_accuracy_verified": False,
            "manifest_sha256": manifest["manifest_sha256"], "max_targets": max_targets,
            "frame_count": total_frames, "target_count": total_targets, "coverage": coverage,
            "gt_checked": manifest["gt_checked"],
            "missing_classes": {split: [name for name, count in row["classes"].items() if not count]
                                for split, row in coverage.items()},
            "missing_orientation_combos": {split: [combo for combo in ORIENTATION_COMBOS
                                                   if not row["class_orientations"].get(combo)]
                                           for split, row in coverage.items()},
            "missing_orientation_labels": missing_orientations,
            "all_orientations_labeled": bool(total_targets) and missing_orientations == 0,
            "duplicate_pixel_frames_within_splits": total_frames - len(owners["pixels_sha256"]),
            "missing_specimen_ids": missing_specimens,
            "all_specimen_ids_present": bool(total_targets) and missing_specimens == 0,
            "near_duplicate_check_implemented": False, "frames": manifest["frames"]}
