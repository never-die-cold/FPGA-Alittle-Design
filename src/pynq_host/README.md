# src/pynq_host —— PYNQ 上位机

PS 侧负责配置与结果通信、ARM 软件基线、黄金参考和指标采集；Jupyter 保留为板端调试与复现入口。最终工业操作界面为 Windows EXE，由 `watercopper` 负责：采集卡视频和网口识别结果统一展示，见根目录 [项目主计划](../../plan.md) §1.3。

## 当前实现与规划边界（2026-10-12）

已有 `vision_regs.py`／`vision_demo.py`／`m2_onboard.py`／`onboard_smoke.py` 配置及板端诊断；
`data/golden/vision/localize/reference.py`／`arm_localize.py` 与打包工具提供定位／裁剪黄金参考，不等于实时部署。
`vision_mock_service.py` 提供明确标注 MOCK 的服务；D6 字段白名单已随 PR #67 合并。
`vision_protocol.py` 已支持严格 MOCK/LIVE v1.2 校验；`vision_mock_service.py --live` 提供合成 LIVE 替身。
`vision_live_service.py` 已实现 FILE 后端、每轮捕获/引擎调用/报文；FILE 恒 `prototype=true`，前端 PROTOTYPE 徽标已实现。
10/15 起，FILE 原型自动轮询直接在内存中检查，只原子更新 `<root>/<session前8位>/latest_packet.json`；
手动 `POST /v1/check` 携 `trigger_ref` 时，完整产物保存到同会话的 `check-<check_id六位>/`。
`--archive-every-round` 启用逐轮完整归档。分类器在会话中复用，修改权重后须重启服务。
非原型后端仍须逐轮保存 C04 Q3 capture 证据；当前真实硬件后端尚未实现。
它没有真实 HDMI/DDR/MMIO/CNN 后端，`/v1/config` 仅推进软件配置号，不证明 R12 硬件应用；见[整合证据](../../data/logs/2026-10-12-pr-review/README.md)。
工单由服务启动参数提供，HTTP配置仅接收control；在线工单编辑未实现；请求重试幂等已按 C04 §2.4 草案实现（服务 16 条 trigger_ref 回放，待 NC/JL 确认）。
下列 notebook／通用工具仍是规划，不能由 mock 或训练演练推断已实现。

本轮新增 `roi_preprocess.py`、`inspection_model.py`、`inspection_rules.py`、
`inspection_replay.py`、`inspection_artifacts.py`、`inspection_run.py`：共享 ROI、
交付 FP32 权重加载、工单候选判定、文件回放与完整性检查已离板验证并随 PR #67 合并。
这是本机 FILE_REPLAY，不是板端服务；原始数据集缺失，阈值和正式精度未验收。
复现、证据与尚未实现项见[离板检查说明](../../docs/runbooks/offline-inspection.md)。

后续新增 `model_reference.py`、`numpy_reference.py`、`model_audit.py`、
`reference_tensors.py`、`reference_package.py`：交付原型的 BN 折叠、独立逐层对拍、
预算审计及可移交的 FP32 软件参考包已离板验证并随 PR #67 合并；
见[模块三逐层参考](../../docs/runbooks/module3-prototype-reference.md)。`src/coprocessor/` 另有完整 INT8 整网参考、算子 RTL 与诊断黄金；正式 INT8 模型和 MMIO/DMA 后端尚未实现，见[计算链现状](../coprocessor/README.md)。

10/13 新增 `c01_capture.py`：custom DDR 单帧候选所有权驱动，完整转移自动停机后 invalidate 并复制；七组离板异常测试通过，未接入 LIVE 服务。板端入口 `sim/scripts/c01_ddr_onboard.py` 的两次实测均启动前失败并安全恢复，最终驱动修正尚待返板，见[DDR证据](../../data/logs/2026-10-13-ddr-single-frame/README.md)。
10/15 新增 `c01_park_capture.py` 备选驱动，显式 `C01_CAPTURE_MODE=park` 才启用；仅通过离板替身，
实际 IRQ/槽/写完成绑定及 N03 仍待验证，见[所有权候选说明](../../docs/contracts/c01-ddr-frame-ownership-v0.md)。

后续新增 `dataset_manifest.py`、`dataset_audit.py` 和仓库 CLI：720p 采集清单、
会话/精确重复像素/实物编号泄漏、覆盖统计和来源声明已用测试夹具验证，理解题及补测已通过。
这些工具的测试夹具证据见[数据集审计](../../docs/research/fastener-dataset-audit.md)，不验收真实标签或模型精度。10/12 离板证据记录为 14 组（含当时尚未提交的构建输入审计）并退出 0；10/13 记录为 15 组。当前 `run_vision_python.sh` 入口为 **21 组**，`run_inspection_python.sh` 为 **19 组**；新增组以脚本和各自证据为准，不把历史 15 组当当前全量。

- `demo.ipynb`：板端调试与复现 notebook
- `benchmark.ipynb`：基线对比与指标采集（CPI、延迟、帧率、加速比）
- `golden_ref.py`：软件黄金参考实现（OpenCV / 纯 Python 推理）
- `metrics.py`：数据自动采集与报告生成（→ `data/`）
- 真实硬件识别后端未实现；FILE/LIVE 骨架已有，不把软件会话/配置号当硬件状态。NC 的实机服务责任与 WC 的适配/服务实现工作见[三人清单](../../docs/project-closeout-three-person-checklist.md)。
- EXE 在 `src/vision_client/`，已有 LIVE 类别/工单展示、批次、CSV 和 FILE_REPLAY；真实硬件联调、检查快照查看和目标机发布仍待完成。

## LIVE 服务捕获后端（W04/N06 诊断包，2026-10-13）

`vision_live_service.py` 的捕获后端三类，`prototype` 由后端**结构性**决定（C04 §3.2，无开关）：
- `FileCaptures`（FILE，离线夹具）：恒 `prototype=true`；
- `C01Captures`（`c01_backend.py`，custom DDR 单帧所有权）：`prototype=false`，板上驱动与
  未验证断言清单见 [c01-ddr-frame-ownership-v0.md](../../docs/contracts/c01-ddr-frame-ownership-v0.md) §7；
- `BaseOverlayCaptures`（`base_captures.py`，base overlay 实时取帧）：`prototype=false`。

N06 诊断包接线（NC 执行；板端脚本提供 overlay 与 read，取帧样板见 `sim/scripts/n03_board_capture.py`）：
`captures = BaseOverlayCaptures(<同步包装的 hdmi_in.readframe>)` →
`make_server(root=…, captures=captures, engine=file_engine(models/cnn-border-fill-best.pt, order, 0.8, 10), order=order)`；
EXE `--source 0 --endpoint http://<板IP>:8765` 联调。板端需 pynq-venv 的 python3 + OpenCV + torch；
FP32 软件推理来源记录在产物 `result.json` 的 provenance，不当作 CNN 硬件验收。
服务失败（无视频/超时/所有权错误）转 HTTP 503 且不产 `packet.json`；离板替身测试
`test_base_captures.py`、`test_c01_backend.py`（视觉栈现 **21 组**；检查链 **19 组**）；
快照核对器 `round_artifacts.py`（C04 §2.3，待 NC 确认）。

## 协处理器 PS 驱动与模拟硬件（2026-10-20）

按 C03 §13 接入 `vision_live_service`，**未上板**：

- `cop_regs.py`：C03 §4 寄存器常量、`cop_judge` 镜像、`FW_DECISION` 编解码；
- `cop_mmio_sim.py`：镜像 §4/§5 的假寄存器模型（配置原子提交、busy 拒 commit、
  sticky DONE/ERROR/TIMEOUT + W1C、RESULT_SEQ 最后提交、watchdog、ABORT/SOFT_RESET、
  CRC/短包/旧结果/目标错误注入）；
- `cop_driver.py`：PS 驱动。只依赖 `read32/write32` + DMA 面；提交、等终态、结果窗
  `RESULT_SEQ` 双读、`FW_DECISION` 逐字段复算、PS 判定“不得比固件更宽松”、
  同 `JOB_ID` 去重、超时/错误清状态重试；`PynqDmaPlane` 故意未实现（J08 数据面）；
- `cop_engine.py`：定位 → `scene-gray-border-padding-v1` ROI → sim INT8 → 驱动 →
  `inspection_rules.judge`；每轮写 `cop_trace.json`（帧像素哈希、ROI 字节哈希、
  cfg/result seq、FW/PS 判定、耗时）；`round_artifacts.load_snapshot` 可核对整条链。

服务入口：

```bash
python src/pynq_host/vision_live_service.py --root <dir> --capture-dir <png dir> \
  --order 1 1 1 --min-score 0.8 --engine cop-sim --sim-classes bolt,nut,washer
```

`/v1/status` 增 `engine` 字段（`FILE`/`COP_SIM`）；`prototype` 仍由捕获后端决定。
`cop-sim` 是模拟计算，分类器是脚本/图像派生的合成结果，`S_input=1/127` 仅为 sim 量化，
**不是**识别精度或板上证据。提交/完成/取结果/恢复与 JL 待办见
[PS 驱动使用档](../../docs/contracts/coprocessor-ps-driver-v0.md)；一轮证据
`bash sim/scripts/run_cop_sim_round.sh`。

## 板卡访问

- 校园网内 SSH：`ssh xilinx@<板卡内网IP>`（2026-09-20 建立，SD 卡已烧录 PYNQ 镜像）；notebook 在板卡 Jupyter（默认端口 9090）上运行

## 约定

- 所有 notebook 从头运行（Restart & Run All）必须无报错
- 采集脚本通用部分尽量与题目解耦，作为通用 PYNQ Skill 的原料

> 状态（2026-10-03）：M2 离板软件栈已闭环并完成首次实机验证——`vision_regs.py`（寄存器映射 +
> commit/wait_applied 原子配置协议，R11 提交/R12 确认）真实 MMIO 上板 PASS（配置号 0→2 帧首确认），
> `vision_demo.py` 实机演示序列 PASS（65 次 commit 全确认）；`vision_protocol.py`/`vision_mock_service.py`
> （定位报文契约 + 本地 HTTP mock，供 EXE 联调）；Windows EXE 原型已接真实采集卡源
> （`vision_preview.exe --source 1`，横幅正确无假框）。证据见
> [../../data/logs/2026-10-03-vision-onboard/README.md](../../data/logs/2026-10-03-vision-onboard/README.md)。
> 板端分步自检 `m2_onboard.py`（env/load/smoke/demo）、断连监视 `onboard_smoke.py watch`
> （STREAM/STALL/BUSY 事件 + WATCH-SUMMARY，含 watch-mock 离板自测）、
> 接线见 [ONBOARD.md](ONBOARD.md)。10/03 修复配置断连复测与[10/07 相机恢复](../../data/logs/2026-10-07-pi-pynq/README.md)有证据；现用位流追溯与长时间／冷启动／断连复验仍待补，不混用不同位流结论。
> `board/adv7611_init.py` 仅为外接接收器示例（PYNQ-Z2 无 ADV7611，不用于本板）。
