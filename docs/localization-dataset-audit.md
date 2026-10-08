# Localization Prototype Dataset Audit

Date: 2026-10-07. Purpose: select public data for an initial OpenCV/CNN comparison before the project has physical fasteners.

## Findings

| Dataset | Verified contents | Use in this prototype |
|---|---|---|
| [Solidworks Hackathon](https://www.kaggle.com/datasets/aswindeivam/solidworks-hackathon) | Kaggle reports CC0. Archive contains 10,000 1024×1024 training images, 2,000 unlabeled test images, 24,982 labeled boxes, and bolt, nut, washer, locating-pin classes. | Best source for object crops and class coverage. Images place parts in fixed 2×2 slots; boxes are fixed 224×224 slot boxes. Do not use its raw localization metrics as evidence for free placement. |
| [Bolts and Washers](https://www.kaggle.com/datasets/ahmedmohamedab/bolts-and-washers) | Kaggle reports MIT. 250 color 1920×1080 images: 225 train, 15 validation, 10 test; labels are Bolt, Bottle, Washer. There are 122 Bolt, 35 Bottle, and 363 Washer boxes. About 100 source-name groups do not cross the provided splits. | Closest reviewed scene layout: parts are scattered on boards/tables. Nut is absent, the test split is small, and a reviewed scene contains visible unannotated parts. Use only for qualitative external checks unless annotation completeness is audited. |
| [The Fasteners](https://www.kaggle.com/datasets/alexandrparkhomenko/the-fasteners) | Kaggle reports CC0. 92 1600×1200 images across ten numeric folders; individual parts are photographed on a blue mat. No bounding boxes or semantic mapping for the numeric folder names. | Possible visual reference for isolated-part segmentation. Too small and ambiguous for the main detector comparison. |
| [NPU-BOLT](https://www.kaggle.com/datasets/yartinz/npu-bolt) | Kaggle reports CC0 and describes 337 natural-scene bolt-joint images with about 1,275 targets. Labels refer to bolt heads/sides/nuts and blur. | Optional stress reference for background and viewpoint variation. It depicts installed structural joints, not loose tabletop parts. |
| [Industrial Fasteners, Bolts, and Washers](https://github.com/lonlonago/Industrial-Fasteners-Bolts-and-Washers-Detection-Data-Set-VOC-YOLO-Format-2357-Images-in-6-731f7b47) | Listing describes 2,357 images and six classes, but says the complete data require an $89 payment. | Not downloaded or purchased. |

## Prototype data decision

1. Use the Solidworks training set to extract bolt, nut, washer, and locating-pin crops. Split original source images before extracting crops or composing scenes.
2. Compose those crops at randomized positions and scales over varied backgrounds to create free-placement scenes with known boxes. This supports implementation and controlled OpenCV/CNN comparison, but remains synthetic evidence.
3. Use Bolts and Washers as an external scene set only after checking all visible target instances against its annotations. Report bolt/washer results separately; its bottle class is a non-target distractor, and it has no nut examples.
4. Do not describe public or synthetic results as real-object acceptance. Final accuracy and support conditions require images from the project camera and actual parts.

## Runtime readiness and remaining limits

The bundled Python 3.12.14 runtime has NumPy and Pillow, but no OpenCV or PyTorch. An isolated environment is now available at `work/venvs/localization-prototype` with Python 3.12.14, PyTorch 2.5.1 CPU, torchvision 0.20.1 CPU, OpenCV 4.10.0, NumPy 1.26.4, and Ultralytics 8.3.17. CUDA is unavailable. No PYNQ-Z2 access or real fastener images are available in this workspace, so board timing and real-scene acceptance remain unverified.

The project plan separates 720p60 display input from analysis throughput. The analysis frame rate and whether it processes every source frame remain unfrozen; report measured speed without claiming a 60 fps requirement.
