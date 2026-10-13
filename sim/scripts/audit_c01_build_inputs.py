"""Verify retained C01 build inputs, then report drift from the current checkout."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(manifest, root, recover_to=None):
    manifest, root = Path(manifest).resolve(), Path(root).resolve()
    entries = json.loads(manifest.read_text(encoding="utf-8-sig"))["files"]
    if not entries:
        raise ValueError("empty build input manifest")
    if recover_to is not None:
        recover_to = Path(recover_to).resolve()
        if root not in recover_to.parents:
            raise ValueError("recovery directory must be inside repository")
        recover_to.mkdir(parents=True, exist_ok=False)
    matches, changed, missing, seen, recovered = [], [], [], set(), []
    for entry in entries:
        relative = Path(entry["path"].replace("\\", "/"))
        if relative.is_absolute() or ".." in relative.parts or str(relative) in seen:
            raise ValueError("invalid or duplicate input path")
        seen.add(str(relative))
        saved = manifest.parent / "inputs" / relative
        original = saved.read_bytes()
        if (hashlib.sha256(original).hexdigest() != entry["sha256"]
                or len(original) != entry["bytes"]):
            restored = original.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            if (recover_to is None or hashlib.sha256(restored).hexdigest() != entry["sha256"]
                    or len(restored) != entry["bytes"]):
                raise ValueError("retained input changed: " + relative.as_posix())
            original = restored
            recovered.append(relative.as_posix())
        if recover_to is not None:
            target = recover_to / "inputs" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as output:
                output.write(original)
        current = root / relative
        if not current.is_file():
            missing.append(relative.as_posix())
        elif digest(current) == entry["sha256"]:
            matches.append(relative.as_posix())
        else:
            changed.append(relative.as_posix())
    if recover_to is not None:
        with (recover_to / "manifest.json").open("xb") as output:
            output.write(manifest.read_bytes())
    return {"manifest": str(manifest), "manifest_sha256": digest(manifest),
            "retained_inputs_verified": len(entries), "current_matches": matches,
            "current_changed": changed, "current_missing": missing,
            "exact_crlf_recovered": recovered, "recovery_directory": str(recover_to),
            "limit": "input integrity/drift only; not bit-to-source or board acceptance"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--recover-to", type=Path,
                        help="new repo directory; restore CRLF only when manifest SHA/bytes match")
    args = parser.parse_args()
    if args.root.resolve() not in args.output.resolve().parents:
        raise ValueError("audit output must be inside repository")
    result = audit(args.manifest, args.root, args.recover_to)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2)
        output.write("\n")
    print("PASS: retained C01 input integrity;", result["retained_inputs_verified"],
          "files; current changed=", len(result["current_changed"]),
          "missing=", len(result["current_missing"]),
          "exact CRLF recovered=", len(result["exact_crlf_recovered"]))


if __name__ == "__main__":
    main()
