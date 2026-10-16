# C01 park 驱动暖机清除与保护复制：首次板端打通（2026-10-16）

接续 `../2026-10-15-c01-direct-capture-stage/` 的停机错误位定性。基线 `dev/model@491d628` +
各会话未提交改动。本目录不改受控源码之外的部分；**本步编辑了 `src/pynq_host/c01_park_capture.py`
与 `sim/vision/test_c01_park_capture.py`**（见 §驱动更新），`git diff --check` 通过。

## 板端事实（五轮实验递进）

全部在 `/home/xilinx/vision_m2/` 试验目录跑，video 为树莓派相机→HDMI IN（60 fps 精确）。

| run | 结果 | 关键记录 |
|---|---|---|
| park 入口首跑（settle 固定 1 s） | 失败：计数器 0→0 | 候选下载后视频锁定 >15 s（10-15 已知事实的再现） |
| park 入口二跑（settle 循环版未上传成功+保底） | 失败：`capture lock/fault invalid` | 启动 DMA 后 `_check_source` 的 0xC 全掩码不满足 |
| warmup 观察器 | 失败但拿到原始数据 | **启动瞬态**：rej+1/epoch+1/ovf=1 单间隔自愈；cap4 bit3 锁存；SR 0x14810;停止后-3s 时 rej=1/epoch=1 |
| 稳态观察器 | PASS（steady_5s） | seq 60fps 精确推进（DDR 真实在写）；运行中 W1C 清后 3 s 不回弹；park 当前槽批准 ~2.1 s；**停止瞬态 ~180 间隔**（rej+1/epoch→182） |
| park walk v3 | 失败：warmup 6 s 超时 | errors=0x810（首清除后 bit14 不再重现、bit4/11 仍锁存；bit12 IRQ 虽置位但不在 ERRORS 掩码内）不满 exact-match `==0x4810`，W1C 未触发，位保持 |
| **park walk v4** | **PASS** | 规则放宽为 `errors & 0x4810` → 首个 W1C 后 **50 ms 内 park 批准**；三步走全部 ~0.05 s；**双副本字节级一致**（SHA `19088a66…`，mean BGR [113,124,123]）；恢复 smoke PASS |
| **更新驱动类复跑**（正式字节） | **PASS** | 换新试验目录 `c01-8b702ebb0b284fa3a408491e13e644e3`，park 驱动 `953dec24…`；`warmup_1/park_0/park_1` 全部成功；invalidate 0.3ms+copy 20ms；`pixel 6c1507e6…` mean [111,122,121] min2 max255 PNG `e195c1be…`；恢复 smoke PASS（配置 2） |

硬件语义结论（WC/JL 评审证据汇总）：

1. 启动 S2MM → 精确一个溢出间隔的自愈瞬态（reject+epoch+1），随后 **cap4 bit3“曾有错误”锁存**
   整个 overlay 实例；`seq` 在 run 期间精确 60 fps。旧判据 `cap4 & 0xC`（含 bit3）恒假。
2. 停机期 SR bit4/11/14 电平型（10-15 记录）；**RS=1 后 W1C 可清且不再回弹**——bit14 首个
   W1C 即清，bit4/11 启动瞬态三点内仍保持，瞬态结束后的 W1C 永久清掉。
3. park 槽位批准在错误位清后的 ≤100 ms 内完成（v2 的 ~2.1 s 是错误位未清导致 FSMD 被锁着的假象）。
4. 提交停止的停止瞬态：~180 个溢出间隔/3 s（每帧间隔一次），cap4 pending 自清、lock 恢复、
   seq 在停机后仍继续计数（~34fps 直至 pending 清了再恢复 60fps——观察窗内未回满）。
5. 首个启动瞬态**只有一次**（epoch 恒 1；稳态 5 秒零新增事件）→ 在暖机批准点重定基线是安全的。

## 驱动更新（本步编辑）

`src/pynq_host/c01_park_capture.py`（新 SHA `953dec24…`）：

- 新增 `_check_source(pending_ok=False)` 覆盖：判据 = lock(bit0) 且 pending(bit2) 清；
  **bit3 不再参与**，启动容许 pending（暖机窗口）。
- 新增 `_refuses_new_events(cap)`：重定基线后 epoch/ovf/loss 死判据（零容差）。
- `_running(warmup)`：warmup 期间 pending 容忍 + `errors & HALT_STICKY` **重复 W1C**
  （`W1C_PARK = 0x4810|0x1000|0x2000`）；post-warmup 事件照旧拒。
- `_wait_park`：批准条件补 `cap4 pending 清`；warmup 批准点把 `cap_before` 重定为
  批准时刻 cap（启动瞬态吸收，注释明示）。

`sim/vision/test_c01_park_capture.py`（寄存器/5 用例）：rig 模型含启动瞬态（首次 post-arm
读 pending 置位→自清）、bit3 锁存、epoch/ovf+1、重复 HALT_STICKY（warm_sticky 需 2 次 W1C）、
double_transient（新事件→拒绝）、copy_pending（pending 持续→拒绝）、lock 失重判定。
5/5 PASS；`bash sim/scripts/run_vision_python.sh` **34 组全 PASS、GATE_EXIT=0**。

## 板端复现

```bash
# 新试验目录（UART receiver 拒绝覆盖已有文件，必须每轮新建 c01-<hex32>）
sudo bash: mkdir -p $NEW && cp $OLD/{capture.bit,capture.hwh,c01_capture.py,c01_status_onboard.py,c01_ddr_onboard.py} $NEW/
# 上传（板端 SHA 校验）：
sim/scripts/send_pynq_file.ps1 -File src/pynq_host/c01_park_capture.py          → c01_park_capture.py
sim/scripts/send_pynq_file.ps1 -File data/logs/…/inputs/c01_park_onboard_diag.py → c01_park_entry2.py
sudo bash -c 'cd $NEW && source /etc/profile.d/xrt_setup.sh && source /etc/profile.d/pynq_venv.sh && python3 -u c01_park_entry2.py'
```

## 链路第一步：真实相机帧 → 板上定位 → v1.2 LIVE 原型包（同日追加）

新跑（`c01-park-locate-run.txt`）沿用正式 park 驱动完成复制后，把帧转 BT.601 灰度
（cv2）并调用 golden 定位器 `reference.locate`（threshold 96 / min_area 8 / max 16）：

- **packet**（printed 完整）：frame_id=35（stream_seq）、config_id=0、148 reg—5 targets、
  status=`RECHECK_BORDER`（全部触边）、mode=LIVE、prototype=true —— 无 class/decision
  （CNN 未接入，诚实口径）。
- `locate_seconds`=11.95 —— golden 定位器是对 921.6k 像素的纯 Python BFS；降采样/
  numpy 化/复用 arm_localize 缓存是下一优化点。
- **本轮启动无瞬态**（cap epoch/rej/ovf 全 0、bit3 未置位）→ 10-15/16 的"启动一次溢出"
  是条件性的；宽判据（lock+pending+epoch 增量）对两种形态都成立。
- capture 复位后再检查：候选下载后视频锁定一角 1.0s 内完成（较昨晚 >15s 的历史不同
  —— 下次启动时长可变）。

链路的下一环需要：(a) 板端 CNN —— torch（互联网或 UART 装包不现实）或 CNN-SoC
续构（C03 J02）；(b) EXE/LIVE —— PC↔PYNQ 网络可达（当前 eth0 未接线）；(c) 工位构图
（Pi 相机正对含紧固件的工位区域）。这些是用户侧物理/评审动作待确认。

## 板上真 CNN 与判定链（owner 授权代做全链，同日再追）

owner 直接授权把 WC/JL 相关动作本会话代做（诚实口径记录），随后完成两层：

1. **FP32 权重包**：`inputs/export_cnn_board_package.py` 以 `PrototypeClassifier` 同一严格元数据
   契约加载冻结模型 `models/cnn-border-fill-best.pt`，经 `model_reference.folded_layers`
   （BN 折进 conv，未改参考实现自身）导出 `cnn_board_package.npz`（140856 B，
   sha `1440e3fd…`，checkpoint sha `70fe3dc3…`）。UART 上传 PASS。
2. **板端 numpy CNN**：`c01_board_cnn_v6.py` 纯 NumPy 复现 conv2d/ReLU/GAP/linear
   （sliding_window_view + einsum，同 `numpy_reference` 口径），四张 golden crop
   （gradient / dark_disk / bright_hexagon / mid_noise）与 PC torch 逐元素 softmax
   差 ≤2e-5 全一致（`MATCH-PC-SOFTMAX: True`；dark_disk 差 4.8e-7、hexagon ~1e-9 内）。
   四类样本类别实际覆盖 bolt/washer/nut，torch ` FastenerCNN` 无量化原版为预言机。
3. **judge 语义**：`src/pynq_host/inspection_rules.py:judge`（expected/actual/delta/
   missing/extra/reasons 全按 v1.2 形状）以"演示工单 2/2/2、min_score=0.8"可行标识跑。

## 全链首跑：真实相机 → 采集 → 定位 → 裁剪 → 板上 CNN → 判定（`c01-park-classify-run.txt`）

frame_id=47、6 目标全部送 `crop_resize` 64×64（golden 16.16 lerp）→ NumPy CNN
（无 torch）→ 每个 target 得 class/score（当前场景下全 bolt，诚实输出不修饰 →
这些是暗色长条/深色桌面遮挡非真实紧固），judge 得 verdict=RECHECK（reasons 含
`touches_border`，场景未构图所致）→ v1.2 LIVE packet 输出。capture/locate/crop/
classify/judge/restore 全段 PASS，启动瞬态照常由判据吸收（epoch=1）。**环上剩：**
- **RISC-V 判定环**：仍需 C03 J02（MMIO/DMA/cop_top 集成 + 工业固件）——本轮 PS 侧
  `judge` 已按契约语义代置，prototype=true 诚实标注；等 SoC 集成位流与固件源码落库。
- **EXE 环**：PC↔PYNQ 网线由用户重接（Pi 只走 HDMI，网线不 повыш影响视频），接通后我方
  轮询 eth0 拉起 LIVE service + EXE 端联调。

## 边界

- **N03 官方验收仍在 WC/JL 评审之后**——本记录是驱动语义 + 观测管线的实机定型，不建议签字。
- 三处脚本修正历史已记录（`c01_park_onboard_diag.py` 三版：settle 循环/PARK_SHA 同步/TRIAL 指向新目录）。
- `sim/scripts/c01_ddr_onboard.py`（+11 行 park mode 入口）与 `test_c01_ddr_onboard`（11 用例）
  已跑绿，配合新 park 驱动语义依然一致。
