# Frozen r6: new placement of the existing specimens

- Date: 2026-10-28; source HEAD `cfbded8`, with the working-tree scripts recorded by the manifest.
- User has only the previously sampled specimens. This is a new-layout holdout, not an unseen-specimen test. r6 was frozen before this capture; this image is excluded from training, calibration and model selection.
- Capture: `python sim/scripts/capture_uvc_raw.py --output-dir data/logs/2026-10-28-r6-holdout-layout04/uvc --frames 72`.
- Compare: `python sim/scripts/check_real_scene_models.py --frame data/logs/2026-10-28-r6-holdout-layout04/uvc/raw.png --output data/logs/2026-10-28-r6-holdout-layout04/comparison --weights data/evidence/2026-10-28-cnn-r6/fp32.pt --package data/evidence/2026-10-28-cnn-r6 --reference-package data/evidence/2026-10-28-cnn-r6/reference --truth-counts 3 3 3`. Reproduction requires a new output directory.
- User-confirmed labels: bolt 1/6/7, nut 0/4/8, washer 2/3/5. Localization found all nine separated objects. FP32 and INT8 agree 9/9; each classifies 8/9 correctly. Both misclassify washer 3 as nut. Class recalls: bolt 3/3, nut 3/3, washer 2/3.
- Artifacts: lossless original `uvc/raw.png`, numbered view and exact quantized ROI bytes in `comparison/`, human truth and correctness in `reviewed-result.json`, board numeric expectations in `board-vectors/`.
- Raw frame SHA256: `2d6b68c379cbc0e09e4ce5d52ac895292acb3a180aff9815ed57593b7c3117bc`. Payload SHA256: `ffc2620df59ab0292a4130d6741fb71b73d972696198a992a21a63877d2b12fa`.
- Numeric vector generation: `python sim/scripts/prepare_cnn_board_vectors.py --model sim/build/real-roi-ptq-20261028-r6 --comparison data/logs/2026-10-28-r6-holdout-layout04/comparison --output data/logs/2026-10-28-r6-holdout-layout04/board-vectors`. Exact hardware comparison is recorded separately in the multi-target board run.
- Outstanding: unseen-specimen validation and formal production accuracy acceptance are not implemented. A correct integer/hardware match does not turn an incorrect class prediction into a correct one.
