# NC 离板文件准备核查

- 日期/执行人：2026-10-20，nc_artifacts agent；仅离板读取，未打开串口、相机、JTAG 或网络服务。
- 版本：`dev/riscv@5f8abe25906d918f15809c888a7d3c1182aa3e08`；本轮复核时工作区含其他 agent 的未提交记录（`nc-board`/`nc-n02-prep`/`nc-ring-prep` 与 `data/logs/README.md`），`src/` 与 `sim/` 无改动。
- 命令：仓库根目录读取既有 runbook/脚本，并用 `python`/`certutil` 重算哈希；未运行任何上板入口。
- 结果：本地恢复归档与板端现有文件字节一致；当前 PL 解析到的设计不是归档 vision 设计。因此**需要恢复，但只需 `load`，不需要重新拷贝 bit/hwh**。
- 产物：仅本 README；不复制 bit/hwh，不修改公共索引，由主控统一收尾。
- 边界/未完成：N01/N02、24 帧逐帧证据、UVC 实采、EXE 实机、硬件 CNN 均未由本 agent 验证；本文件不含任何本 agent 产生的上板证据。

## 拿什么恢复原 vision

恢复源：`data/evidence/2026-10-10-onboard-bit-provenance/vision-2026-10-03-after-fix.xsa`。

| 内容 | 字节数 | 本次 SHA256 |
| --- | ---: | --- |
| XSA | 499890 | `69ac73e04d39df52e5230345bd5e4ffca183c1dc12f8581a5b6c65f27783dead` |
| 内部 vision.bit | 4045769 | `4f0c491a6383d8a11f87cd2de260027f519dbd466942d0b1b6e36198e39d5be5` |
| 内部 vision.hwh | 313989 | `c0adfd3656c2fdb0468de356dc8232857580286d48977c41d6ee61edc3b7b5a5` |

```powershell
python -c 'import hashlib,zipfile; p="data/evidence/2026-10-10-onboard-bit-provenance/vision-2026-10-03-after-fix.xsa"; z=zipfile.ZipFile(p); print("xsa_sha256",hashlib.sha256(open(p,"rb").read()).hexdigest()); [(print(n,len(z.read(n)),hashlib.sha256(z.read(n)).hexdigest())) for n in ("vision.bit","vision.hwh")]'
```

来源说明见归档同目录 README：可对应到历史板端字节；该归档没有构建时完整源码快照，不能宣称由当前 HEAD 干净重建（PROVENANCE GAP）。
历史板端路径为 `/home/xilinx/vision_m2/vision.bit` 和同名 `.hwh`。

## 板端现有文件已经等于归档（本轮新增核对）

对上 `data/logs/2026-10-20-nc-board/baseline/artifacts.txt`（主控 2026-10-20T13:00:02Z 读取）：

| 板端路径 | 板端 SHA256 | 与归档 |
| --- | --- | --- |
| `/home/xilinx/vision_m2/vision.bit` | `4f0c491a…` | 相同 |
| `/home/xilinx/vision_m2/vision.hwh` | `c0adfd36…` | 相同 |
| `/home/xilinx/vision_m2/m2_onboard.py` | `679befc3…` | 与 `src/pynq_host/m2_onboard.py` 相同 |
| `/home/xilinx/vision_m2/vision_regs.py` | `1b30a62d…` | 与 `src/pynq_host/vision_regs.py` 相同 |

结论：**恢复不需要传文件**，只需要在板端把已有 `vision.bit` 重新 `load`。这也说明 `send_pynq_file.ps1` 不是该用途的入口——它只允许新建 `/home/xilinx/vision_m2/c01-[0-9a-f]{32}/文件`（`sim/scripts/send_pynq_file.ps1:5`），会直接拒绝覆盖原 vision。

## 当前 PL 不是归档 vision 设计（本轮新增，恢复判据）

- `/sys/class/fpga_manager/fpga0/state` = `operating`：PL 已配置，有某个位流在运行；`firmware` 为空。
- `PL.bitfile_name` = `None`、`PL.timestamp` = `None`：PYNQ 不知道该配置来自哪个文件。
- 板端 `PL.ip_dict` 是基础/视频设计命名：`switches_gpio`、`btns_gpio`、`rgbleds_gpio`、`leds_gpio`、`audio_codec_ctrl_0`、`video/hdmi_in/*`、`video/hdmi_out/*`、`video/axi_vdma`、`trace_analyzer_pi/*`、`trace_analyzer_pmodb/*`。
- 归档 `vision.hwh` 的 7 个模块是 `/converter`、`/high`、`/pipe`、`/ps7`、`/rx`、`/snapshot_ila`、`/tx`。

两边模块名完全不相交（仅 `ps7`/`ps7_0` 同名根），所以**当前 PL 不是归档 vision 设计**；尽管文件字节已一致，仍需执行一次 `load` 才可能让 vision 上线。板端 PID 669 `park_live_server_v7.py`（端口 8765）在这个 PL 下运行，其是否依赖 vision overlay 无法离板判定。

```powershell
# 复核归档 hwh 模块名（本轮实际执行）
python -c "import zipfile,xml.etree.ElementTree as ET; z=zipfile.ZipFile('data/evidence/2026-10-10-onboard-bit-provenance/vision-2026-10-03-after-fix.xsa'); x=ET.fromstring(z.read('vision.hwh')); [print(m) for m in sorted(set(e.get('FULLNAME') for e in x.iter() if e.tag.endswith('MODULE') and e.get('FULLNAME')))]"
```

## 板端脚本可按仓库源码判定（本轮新增）

`m2_onboard.py`、`vision_regs.py` 的板端哈希与 `src/pynq_host/` 同 HEAD 文件逐字节相同，因此下列行为由仓库源码确定，不必上板试错：

| 子命令 | 实际行为（源码位置） |
| --- | --- |
| `env` | 打印 python/pynq 版本与三个文件是否存在；缺文件只打印 MISSING，不报错 |
| `load` | `Overlay(vision.bit)` 下载 overlay，打印 ip_dict 与基址；找不到 `0x40000000` 段则 `FAIL` 退出 1 |
| `smoke` | 读 R11/R12 → `GRAY` 预设 → `commit(timeout=1.0)`；超时打印 NOVIDEO 并 `exit 3`；否则校验 R12 == 提交号 |
| `demo` | `import vision_demo` 后跑参数序列（GRAY/GAUSS/GAUSS_SOBEL/GRAY_SOBEL + OSD 框 + SNAPSHOT） |

**新增风险**：`demo` 依赖 `vision_demo.py`，而板端哈希清单只覆盖 `vision.bit/hwh/m2_onboard.py/vision_regs.py`，`vision_demo.py` 是否在 `/home/xilinx/vision_m2/` 未经验证。缺该文件时 `demo` 抛 ImportError（退出 1，不是规范的 FAIL 文案），演示前需`ls` 确认。

预设名核对：`demo` 用到的 `GRAY`/`GAUSS`/`GAUSS_SOBEL`/`GRAY_SOBEL`/`GAUSS_SNAPSHOT` 都在 `vision_regs.PRESETS` 里（0x0/0x1/0x9/0x8/0x3），不会因 KeyError 中断；缺的只是 `vision_demo.py` 这个文件本身。

地址段核对：归档 `vision.hwh` 里恰有一段 `0x40000000–0x4000FFFF`（挂在 `/ps7` 下），与 `AXI_REGS_BASE` 一致，所以 `load` 的布局检查预期通过。若上板时反而报“ip_dict 中无 0x40000000 段”，说明板端 bit/hwh 配对被换过，应停下核查，不要继续启动服务。

## 可交给主控的既有入口

| 入口 | 用途与限制 |
| --- | --- |
| `sim/scripts/run_pynq_baseline.ps1 -Port COM12 -OutputDirectory <仓库内新目录>` | 八项只读查询（system/uptime/identity/network/os/artifacts/environment/loaded），无 boot_id，需另读 `/proc/sys/kernel/random/boot_id`；目录必须不存在且位于仓库内 |
| `sim/scripts/pynq_serial_command.ps1 -Port COM12 -Command <单行板端命令> -LogPath <仓库内新文件>` | 保留真实退出码；124 = 超时（远端是否完成未知），不可直接并发下一项；`LogPath` 必须是新文件 |
| 板端 `python3 /home/xilinx/vision_m2/m2_onboard.py load` | 重载原 vision；主控先停止服务/DMA 并确认可切换 |
| 板端 `python3 /home/xilinx/vision_m2/m2_onboard.py smoke` | 写配置并等帧首；退出 3 为 NOVIDEO，不算通过；需激活 PYNQ/XRT 环境 |
| `python sim/scripts/capture_uvc_raw.py --output-dir <仓库内新目录> --frames 24` | 连续读 24 次但只保存**最后一帧**（`sim/scripts/capture_uvc_raw.py:55-67`），只留该帧像素 SHA；不能充当 24 原帧/逐帧 SHA 证据；要求输出目录为仓库内不存在的新目录，且帧必须是 1280x720x3 |
| `sim/scripts/list_dshow_video.ps1` | DirectShow 枚举入口；设备序号需本轮核实，不沿用历史序号 |

板端环境历史入口为 `source /etc/profile.d/xrt_setup.sh && source /etc/profile.d/pynq_venv.sh`；是否需要 sudo 及认证由主控确认。
历史重试命令最后 `echo SMOKE_OK=...` 会掩盖 smoke 失败，应分开执行 load/smoke 并保留各自退出码。
`deploy_vision_onboard.sh` 固定取 `sim/build/hdmi-project/vision.bit` 与 `.gen/sources_1/bd/vision/hw_handoff/vision.hwh`（`sim/scripts/deploy_vision_onboard.sh:17-18`），本工作区无该目录，不能假定归档 XSA 会被它采用。

## 工具与缺口

- `python` = `...\Python312\python.exe`；`cv2` 5.0.0、`numpy` 2.5.1 可导入。
- PATH 上找不到 `ffmpeg`、`vivado`（也不含 `pwsh`，会话内由绝对路径启动）；这不等于磁盘未安装，也不阻碍 OpenCV 既有采集入口。
- 旧 runbook 的 `sim/build/c01-hdmi-1791713720540454/capture-1791713720540454.{bit,hwh,xsa}` 三文件在本工作区均不存在。
- C01 为可选诊断，不以另一个 first-build 旧包替换候选；若需重建/找回，先核对正确版本及安全门。
- 原 vision XSA 已在库，当前无需重新综合或下载任何包即可继续 N01 只读核查。
