# NC 本轮成果与相机故障记录（2026-10-20）

- 日期/执行者：2026-10-20，NC主控；用户配合认证、Pi关机/CSI排线检查与改接线。
- 版本：dev/riscv@5f8abe25906d918f15809c888a7d3c1182aa3e08 + 本轮未提交工具/证据；不commit/push/切分支。
- 方法/命令：仓库pynq_serial_command.ps1、run_pynq_baseline.ps1、capture_uvc_raw.py、run_pynq_watch.sh、build_vision_client.ps1、nc_ssh_session.py；完整参数与真实退出码见各原始日志及pi-ssh/*.request.json。
- 总结：EXE与取证工具已交付；原vision加载/寄存器冒烟通过；相机未出图，600秒观测FAIL，完整NC演示未完成。
- 产物：本目录原始串口日志、逐帧PNG/像素SHA、SSH原始响应、EXE构建日志与包指纹、差异与未跟踪清单。
- 边界：未实现首个CNN硬件输出；原型PARK/PS NumPy不代表硬件推理。用户无备用排线/相机，本轮停止继续排查并保留现状。

## 验收状态

| 项目 | 本轮结论 | 证据 |
| --- | --- | --- |
| N01只读基线与版本 | 查询完成；原vision文件哈希与归档相符，不能代签视频功能 | baseline/、n01-readonly-initial.txt |
| 原vision加载/寄存器 | 两轮load/smoke均exit0，恢复后配置1被帧首确认 | vision-load-first.txt、vision-smoke-first.txt、vision-recovery-load.txt、vision-recovery-smoke.txt |
| UVC与逐帧证据 | 单会话24次读取、24张PNG逐张无损回读、BGR像素SHA齐；实际内容是终端/黑屏 | uvc-*/metadata.json、frame-*.png、对应.log |
| 相机内容 | FAIL：IMX708可枚举，却持续frontend timeout；无真实相机图像 | pi-ssh/0002..0005.response.json |
| 600秒观测 | FAIL：WATCH_EXIT_CODE=9，结束BUSY；期间有人为源扰动，不能作干净连续流验收 | watch-600-final-read.txt |
| N02其余用例 | PYNQ冷启动未执行；源中断有短暂恢复但末尾BUSY；完整overlay画面恢复未通过 | watch-600-progress-*.txt、uvc-after-watch-failure/、uvc-restored-console/ |
| EXE成品 | 构建与自带打包/HTTP模拟联调/回放检查全通过，exit0；真实UVC预览900帧exit0 | exe-build.log、exe-build-exit.txt、exe-video-only.* |
| 实网ring/完整EXE演示 | 未完成：相机故障；未运行本轮板端/v1/check，不把模拟测试当板端闭环 | status-before.json只记录初始服务状态 |

## 成品入口

- EXE：sim/build/vision-client/dist/vision_preview/vision_preview.exe；完整分发目录含_internal，不单拷EXE。
- ZIP：sim/build/vision-client/vision-preview-5f8abe2-nc.zip（忽略生成物）；exe-zip-sha256.txt与exe-package-manifest.json记录指纹。
- EXE真实UVC截图：exe-video-only.png；标VIDEO ONLY，640×480，终端画面，不是识别或720p EXE验收。
- 720p取证：python sim/scripts/capture_uvc_raw.py --output-dir <仓库内新目录> --frames 24 --save-all。
- 持续监视：run_pynq_watch.sh在板端新目录运行；watch-remote-path.txt与upload-watch*.txt给出实际部署路径/SHA，5秒预检已通过。
- SSH：用户在本机运行python sim/scripts/nc_ssh_session.py并私下输入密码；后续主控通过新生成的sim/build/nc-ssh-*/请求/响应目录操作。每次启动新目录保留历史，不存密码/不新增登录key/不监听端口；本轮连接已关闭。

## 故障定位依据

1. 相机服务显示running不代表有帧，日志反复Camera frontend has timed out。
2. 服务重启、Pi断电检查两端CSI排线后仍超时。Pi相机独立nopreview拍照也失败。
3. 主控独立640×480、5fps拍照经过15秒有界保护后退出124，NO_JPEG；SSH命令本身的退出已确认，不等同于串口124的远端完成未知。
4. 用户改成Pi HDMI直连采集卡后，复启相机再采24帧仍为终端；故障不依赖经过PYNQ的路径。
5. 本次Pi启动get_throttled=0x0，未见其欠压/降频标志；不能完全排除相机端供电。
6. 优先怀疑CSI排线/接触、接口或相机数据通路；未换已知好线/相机，尚不能判定具体损坏件，也未证明所有驱动问题均已排除。

## 留场状态与注意事项

- 接线最终为Pi HDMI→采集卡→PC，旁路PYNQ；PC网口接Pi192.168.50.2；PYNQ仍由COM12控制。
- PYNQ boot_id全程为9d7a5170-2b47-4a53-8b1e-8ec3fc418369；本轮只给Pi断电，没有执行PYNQ冷启动。
- PYNQ已恢复原vision、smoke通过；实际可见图像未恢复。原型服务PID669在空闲时停止，没有在途PARK捕获或UNSAFE-STOP。
- Pi服务曾在0006停止；最终0007查询发现已再次active/running、enabled，PID2575。因此不能声称结束时相机服务已停；主控未再更改，保留该真实状态。
- 0007最终检查因发现活跃相机进程退出2，表示留场检查不满足“无活跃相机”，不是另一次拍照结果；临时SSH随后关闭，final-state.json为connected=false。
- Pi与PYNQ日历分别停在Oct06/Sep22，本轮日期以PC为准，运行中没有校时。
- 两次现场读取命令漏PYTHONPATH/base的错误均保留；修正后读到busy=True/applied_config_id=977，不能把调用错误算硬件故障。
- 初始root路径c01目录查询错误不代表目录缺失；实际位于vision_m2/c01-*下。

## 改动、验证与后续

- 改capture_uvc_raw.py：增加--save-all，保存每帧并无损回读/记录哈希；默认末帧行为保留。
- 新增run_pynq_watch.sh：持久有界监视与真实退出码日志；新增nc_ssh_session.py及test_nc_ssh_session.py：一次认证直接排查、断连状态保护。
- SSH首版已真实执行0001..0007命令；运行源码SHA单列保存。后续新增无退出状态(-1)保护与新会话目录，2项仓库测试通过；未再次建立真实SSH验证新启动目录。
- worktree-diff.patch为跟踪改动快照（排除自动生成索引）；新文件内容在工作区，untracked-files.json列路径/SHA；execution-files.json记录入口脚本指纹。修改这些记录后统一刷新索引。
- 用户要求快速模式，理解题留到本轮最后；不commit。
- 有备件后：先关Pi并断电换已知好CSI排线→独立拍照→直连预览→恢复经PYNQ链路→干净600秒/N02四例→实网ring/EXE。不能把本轮失败项记成已完成。

## 2026-10-24 入库归档

为减少跟踪文件数，251 个原始文件压缩为 `evidence.tar.xz`；本地原文件另存 `sim/build/2026-10-24-merge-review/original-evidence/`，由本目录 `.gitignore` 排除后续展开文件。本次未复跑硬件，历史失败结论不变。

压缩包用途是保留上述 2026-10-20 现场取证；来源、包 SHA256、逐文件路径/字节/SHA256 见 `ARCHIVE-MANIFEST.json`。归档时逐文件复算哈希一致。gzip 单包超过 8 MB，采用 xz 压缩减少重复图像开销，无需大文件例外。

从仓库根目录恢复后，原文所有相对路径仍可使用：

```powershell
python -m tarfile -e data/logs/2026-10-20-nc-board/evidence.tar.xz data/logs/2026-10-20-nc-board
```
