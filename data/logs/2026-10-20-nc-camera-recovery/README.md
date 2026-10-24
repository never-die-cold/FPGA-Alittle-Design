# NC Raspberry Pi camera recovery probes

- Date/operator: 2026-10-20, NC/Codex. Host date is authoritative; Pi clock reports October 6.
- Source: `dev/riscv@5f8abe25906d918f15809c888a7d3c1182aa3e08`, dirty working tree. No commit, push or RTL change.
- Device: Pi 4 Model B Rev 1.5, IMX708 Camera Module 3, kernel `6.18.50+rpt-rpi-v8`; boot `a48c8956-92a9-4a9e-beb4-0ec6827af9d4`. Pi HDMI is directly connected to the capture card during these probes.
- Entry points: `sim/scripts/pi_camera_matrix.sh`, `pi_camera_recovery.sh`, `pi_camera_native.sh`. Run on the Pi with a **new** directory under `/home/edgesight/FPGA-Alittle-Design/data/logs/`, preview service stopped and no other camera owner. Each contains its own bounded capture and acceptance checks. Remote scripts were deployed under matching `*_20261020.sh` names; exact commands and results are in `ssh/*.request.json` and `ssh/*.response.json`.
- Results: camera recovery **FAIL**, not a hardware damage diagnosis. RAW at all three supported modes and manual still capture timed out with zero bytes. Holding runtime power on did not recover frames. The first libcamera test-pattern attempt reset the control to zero, so it does not prove a sustained pattern test. The subsequent native V4L2 probe verified pattern 2 (`Solid Color`) before and after, matching sensor/video formats, and successful STREAMON; it still produced zero bytes and zero `unicam_capture0` interrupts. V4L2 returned exit 0 with `select timeout`; zero-byte output is correctly rejected.
- Artifacts: archived SSH requests/responses `0004`–`0014`; full per-case Pi logs were retrieved after reboot into `pi-probes/`. Transfer archive `pi-probes.tar.gz` (7,482 bytes) SHA256 `e59b4a2669fe505ac08da693adab2cb921cc71311a413190acd4dd1b8d06d931` matches the remote hash. It is retained to verify transfer provenance; zero-byte `.raw` files are failed diagnostic outputs, never dataset images. No image from these probes is accepted as a real camera frame.

## Driver rebind failure and recovery boundary

Request `0012` tried an IMX708 unbind/bind lifecycle reset. The bind write reported **Segmentation fault**, script exit 2. The printed `SENSOR_DRIVER_BOUND=1` only checked a sysfs link; it does **not** establish a functioning camera driver. Request `0013` returned device/module/configuration inventory, but `0014` failed to complete within its 20-second transport limit; its completion is unconfirmed and the SSH helper closed. Do not assume the remote command stopped. A clean Pi reboot and reauthentication were requested. Do not keep hot-rebinding this kernel.

The repository rebind script now refuses `6.18.50+rpt-rpi-v8` before mutation. Historical deployed version SHA256: `1687bf85c6565fcc189d7bf0a0e4f867204677d89c4a99f43b53476e3a12c425`. The source in request `0012` preserves that failed version exactly.

## Source fingerprints

| Script | SHA256 |
| --- | --- |
| `pi_camera_matrix.sh` | `11f93ca426de96b38ea63df0ca8f07ee1560b4377c96208d8a67fca7daafde00` |
| `pi_camera_recovery.sh` | `c4b54e7b409b708c9a2bbbe2e727b7701abd8de9605e525a497aa61aeab27ec3` |
| Initial `pi_camera_native.sh` deployed in `ssh/0010.request.json` | `9a0742e60f1dee8099c7b7b3c5011225548db8b99e872e5730e3b00e8e022c60` |
| Current native probe, with live receiver status/debug restoration | `1196f37b3d187ed3f1cbd2793539a6d46194ec8f99637eb7e388621759ae80ec` |
| Guarded `pi_camera_rebind.sh` | `321c122cd942c023d6f045a33c8a204c589144e02f140bfcca84df424af27162` |

## Unfinished

Recover a real camera JPEG, inspect it, restore and verify HDMI preview, then retest the intended Pi/PYNQ/capture path. No bitstream, kernel, boot configuration, SSH keys or package upgrades were installed.

## Clean reboot and live receiver check

User rebooted; new boot is `49493451-8f43-49cd-a0d1-e12c64a3b22c`, new authenticated session in `reboot-49493451/ssh/`. Preview started automatically as PID 663 and still timed out; stopped for exclusive diagnostics. Packages pass `dpkg -V`; package-history query returned no matching changes. Previous boot has no persistent journal, so the exact exception trace remains unavailable. New boot's taint 1024 corresponds to staging modules in its boot log, not proof of a new kernel exception. Picamera2 is not installed; no packages were installed for this test.

Native capture retained test pattern 2 before/after, STREAMON succeeded, sensor and capture formats matched 4608×2592 packed Bayer. Live receiver reported **Detected resolution: 0×0**, IRQ count remained zero, capture output remained zero bytes; probe exit 1. Its wrapper exit 0 only means the later `dmesg` read completed, not that capture passed. Power, pattern and debug controls were restored (`RESTORE_FAILED=0`). User confirmed independent power and original short ribbon. A physical inspection of the camera-board connector is pending; do not infer which component is broken.

PC UVC opening failed with `USB Video at DirectShow index 1 did not open` on this reboot. This failed open supplies no new image evidence and cannot diagnose the camera by itself. Preview service remains enabled but stopped at the end of these probes; SSH remains open for ongoing recovery.

## 2026-10-24 入库归档

原始文件归档为 `evidence.tar.gz`，用途是保留本轮取证并减少跟踪文件数；本地展开文件另存 `sim/build/2026-10-24-merge-review/original-evidence/`，由本目录 `.gitignore` 排除后续展开文件。原始失败结论不变，本次未复跑硬件。

- 包内文件：82；压缩包字节：51355。
- SHA256：`2768234c94ea4e11cab12b787256b2da321477ec31215b4d3cc96816cd21c587`；逐文件路径/字节/SHA256 见 `ARCHIVE-MANIFEST.json`。
- 来源：上述 2026-10-20 现场原始文件；2026-10-24 归档时逐文件与工作区字节比较一致。
- 从仓库根目录恢复后，原文所有相对路径仍可使用：

```powershell
python -m tarfile -e data/logs/2026-10-20-nc-camera-recovery/evidence.tar.gz data/logs/2026-10-20-nc-camera-recovery
```
