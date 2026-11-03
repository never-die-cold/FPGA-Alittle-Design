"""Official open-topic layout, keeping source bytes intact and recording relocations."""
from pathlib import PurePosixPath

GUIDE = "https://gitee.com/Vickyiii/fpgachina26-amd/blob/master/TRACK_GUIDE_2026.md"
ROOTS = {"src", "sim", "build", "board", "data", "skill", "report"}
OFFICE = {".doc", ".docx", ".pdf", ".ppt", ".pptx", ".xls", ".xlsx", ".odt", ".tex"}
MOVES = (
    ("sim/build/cnn-r9-board-package/", "board/runtime-r9/"),
    ("sim/build/cnn-r9-live-20261103/", "data/models/live-r9/"),
    ("sim/build/cnn-r9-board-vectors/", "data/golden/live-r9/"),
    ("sim/build/cnn-r8-live-20261103/", "data/models/r9-training-start/"),
    ("models/", "data/models/baselines/"),
    ("results/", "data/development/results/"),
    ("docs/", "report/engineering-notes/"),
)


def destination(name):
    path = PurePosixPath(name)
    if path.suffix.lower() in OFFICE or name.startswith(("docs/poster/", "docs/tech-report/", "docs/img/")):
        return None
    if name in {"README.md", "LICENSE"}:
        return name
    if name in {"AGENTS.md", "plan.md", ".gitignore", ".gitattributes"}:
        return "report/repository-notes/" + path.name
    for old, new in MOVES:
        if name.startswith(old):
            return new + name[len(old):]
    if name.startswith("sim/build/"):
        return "data/development/filming-r9/" + name[len("sim/build/"):]
    return name if path.parts[0] in ROOTS else None


def arrange(entries):
    mapped, origins, excluded = {}, {}, []
    for old, data in entries.items():
        new = destination(old)
        if new is None:
            excluded.append(old)
            continue
        if new in mapped:
            raise ValueError("archive path collision: " + new)
        mapped[new], origins[new] = data, old
    mapped["report/repository-notes/original-readme.md"] = mapped.pop("README.md")
    origins["report/repository-notes/original-readme.md"] = origins.pop("README.md")
    mapped["README.md"] = README.encode("utf-8")
    return mapped, origins, excluded


README = f"""# EdgeSight code package

This package follows AMD open-topic guide section 3.3.5.4: [official guide]({GUIDE}).

```text
edgesight/
  README.md
  LICENSE
  src/      RTL, RISC-V firmware, PYNQ software, web client
  sim/      testbenches and verification scripts
  build/    reproducible build scripts, reports, package manifest
  board/    board setup and runtime-r9 deployment package
  data/     test fixtures, golden references, model parameters
  skill/    reusable skills
  report/   collaboration records and Markdown engineering notes
```

No Word, PDF, slide deck, poster, or final design-report artifact is included.
The package contains the current uncommitted source fixes. Source bytes are preserved.
Hashes and original-to-package paths: `build/submission/manifest.json`.

Before using legacy tests, training defaults or links that reference original repository
paths, run `python sim/scripts/prepare_submission_workspace.py` once after extraction.
It copies relocated dependencies back to their original paths without changing source.
Current model: `data/models/live-r9/`; ready board package: `board/runtime-r9/`.

PC web: `python src/web_client/serve.py --endpoint http://192.168.50.99:8765`,
then open http://127.0.0.1:8000. Apply the user-entered work order before RUN.
Board entry: `src/pynq_host/cop_product_service.py`, with the actual uploaded `--package`
and a new `--root`; filming flags: `--background-mode local-fast --color-threshold 25 --min-score .8`.
No work order is preset on startup. Complete board video initialization first.

Software checks: `bash sim/scripts/run_offboard.sh software` (required tools must be installed).
RTL checks: `bash sim/scripts/run_iverilog.sh all`. The latest full software suite was not rerun.
The recovered board responded to one real check with HTTP 200 / RECHECK; this is not an
accuracy verdict. Long-run stability and independent classification acceptance remain open.
r9 fits its 39 training/calibration samples but scores 7/9 on the older development layout
(r6: 8/9). Assistant-reviewed labels are not independent validation.
Final technical report, poster and video are separate deliverables held by the team.
"""
