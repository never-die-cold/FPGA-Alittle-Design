# N03 base 取帧与显示共存短诊断（2026-10-12）

基线 `dev/model@3e2e1c9`。用户授权继续测试，并明确本次距离、背景、光照等不作为最终标准。本目录仅为临时测试证据，不进入正式数据集，不冻结 N04 条件。无 RTL/脚本修改、提交或推送。

## 仓库入口与结果

1. `powershell.exe -NoProfile -ExecutionPolicy Bypass -File sim/scripts/run_n03_board_capture.ps1 -CheckOnly -LogPath <仓库内路径>`：PASS，串口命令 2688 字节，未打开串口。
2. `powershell.exe -NoProfile -ExecutionPolicy Bypass -File sim/scripts/run_n03_coexist.ps1 -Port COM12 -OutputDirectory <本目录的新路径>`：PASS，退出 0。进程内 PATH 指向主机 Python 3.12，没有改动全局环境。脚本哈希见 [script-hashes.txt](script-hashes.txt)。
3. [board.txt](board.txt)：加载 PYNQ base，MODE=`1280×720,24bpp,fps=60`，COLOR=BGR。此处 fps 为驱动报告模式，不是本次实测吞吐。
4. 2 次 warmup、1 次保存完整副本、6 次重复读取均完成并释放；FRAME=`(720,1280,3) uint8`，strides=`(3840,3,1)`，副本连续，读取加复制 `24.352ms`（不含 PNG 编码/传输）。
5. [host-status.txt](host-status.txt)：20 秒共存窗口内 UVC 24 帧完成，BOARD_EXIT=0、UVC_EXIT=0、UVC_FINISHED_BEFORE_CLEANUP=True。[board.txt](board.txt) 记录 HDMI OUT/IN closed、CLEANUP COMPLETE。
6. [restore-smoke.txt](restore-smoke.txt)：base 清理后恢复原 `m2_onboard.py load`，等待 5 秒再 smoke，均 PASS；`busy=False, applied_config_id=1`，退出 0。
7. [uvc-restored](uvc-restored/raw.png)：恢复后 UVC 再读 24 帧成功，退出 0。共存窗口与恢复画面均已目视核对，有木纹背景和四个零件；没有色卡或动态标识，不声明独立颜色/无混帧验收。

## 板端原图与传输复核

- 板端新文件：`/home/xilinx/vision_m2/n03-base-a668ca233d4c44e49ee189192e580c59.png`，1432893 字节。
- 串口传输使用 `sim/scripts/pynq_serial_command.ps1`，以 PNG BEGIN/END 标记包住 `base64 <板端新文件>`；完整命令及退出 0 见 [png-transfer.txt](png-transfer.txt)。不改网络，不改板端图像。
- 复核入口：`python sim/scripts/recover_n03_png.py --board-log <本目录>/board.txt --transfer-log <本目录>/png-transfer.txt --output <仓库内新PNG>`；[原始输出](png-recovery-console.txt) PASS，退出 0。
- [board-raw.png](board-raw.png) 的字节 SHA256=`7e08be8bf54c40a0d19dd798ab8aaddfa68eda4e66f81b4e8ed0eb4c0016e015`。
- 解码像素 SHA256=`c5f445b879bf64fb5f27a9a1e91e33bd3e704a459d93b7740087b85b34149d5a`，与板端副本一致；[metadata](board-raw.metadata.json) 记录 shape/dtype 和像素范围 20..255。
- 已目视检查板端原图：木桌上两件螺栓、一件螺母、一件垫圈，非全零图；与共存窗口 UVC 场景一致。两路不代表同一个 capture_id 或同一视频帧。
- 第一次沙箱复核未能启动 Python，保留 [原始错误](png-recovery-console.sandbox-launch-failed.txt) 和 [说明](png-recovery-launch-note.txt)；`png-recovery.stale-shell-exit.txt` 的 0 是陈旧 shell 值，不能视为 Python 成功。随后主机环境执行已有恢复入口通过。

## 结束状态与验收边界

[final-state.txt](final-state.txt) 退出 0；boot_id=`2d61ca6a-03dc-4628-88e3-1203ac8b0e3c`，与此前 [N02](../2026-10-12-n02-extended/README.md) 和恢复前后相同。实际运行 `/home/xilinx/vision_m2/vision.bit`，IP=`pipe,ps7`；COM12 已释放。

结束时原 vision.bit/hwh 哈希保持 `4f0c491a…`/`c0adfd36…`。同次只读检查的 base.bit SHA256=`d9aec0ff1cddeaf109dd08b1510c2ed38b4804bd29ef7648ee80eac8f06de505`，base.hwh=`94dee45319dfecb22d9684eb565916e62f910eb999650c9a99fda51bdc9158fe`。完整值见结束日志；这不是 base 构建源码锚定。

判定：本次 base 完整 BGR 副本、PNG 双哈希、短重复读取释放和 20 秒显示共存诊断通过；不标记完整 N03 或正式采集验收。base 与自定义整片位流互斥，不证明自研核/CNN运行。
待测：色卡/动态无混帧、长期共存、断源与冷启动恢复；N04/N05 正式定标和数据未完成。未实现/未接入：安全 custom DDR 所有权适配、CNN RTL、核工业固件和真实 LIVE 闭环。

Git 差异检查的原始输出与退出值见 `diff-check.*`、`staged-diff-check.*`。
