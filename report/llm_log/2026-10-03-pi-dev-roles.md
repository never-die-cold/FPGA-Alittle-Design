# 树莓派 4B 开发期角色：方案批准与执行记录

日期：2026-10-03。分支 codex/vision-offboard。AI 产出（ZCode/GLM）。

## 决策

用户提出「用手头树莓派 4B 分担算力」。经评估与用户拍板：

1. **方向 = 开发联调辅助**，不进产品分析路径（plan.md §1.3 冻结板卡完成
   预处理/定位/分类；M3 验收要求识别结果来自板卡分析）。
2. **角色 R1–R4**：交叉基准 / EXE mock 宿主 / 回放源（等 micro-HDMI 线）/ CM3
   正式演示源（原定角色）。runbook 见 `docs/pi-dev-roles.md`。
3. **系统卡策略**：Pi 使用项目专用 microSD（另购），系统 Raspberry Pi OS Lite
   32-bit（bookworm）——32 位使 platform=armv7l 与 PYNQ A9 同口径，
   `compare_arm_localize_bench.py` 零改动；所有系统配置（相机使能、config.txt
   锁 720p60）只落在该卡。文档按用户要求只写此中性口径。

## 本批改动（commit 前待理解题确认）

- `src/pynq_host/vision_mock_service.py`：`__main__` 暴露 `--host`（默认
  127.0.0.1 不变）；docstring 注明远程联调用途与 mock 口径。
- `sim/scripts/make_replay_scene.py`（新增）：纯标准库生成 720p PGM 场景 +
  ffmpeg concat 清单；场景序列 normal×2(重复帧段)/extra/normal/missing/empty
  映射 M3 验收用例。
- `docs/pi-dev-roles.md`（新增）：红线五条 + R1–R4 runbook + 环境约束。
- `board/hardware.md` §5：加开发期角色一行（中性口径）。

## 验证证据

- `bash sim/scripts/run_vision_python.sh` 7/7 PASS（含 HTTP mock 契约测试）。
- mock `--host 0.0.0.0 --port 18899` 冒烟：/v1/status、/v1/latest 正常应答。
- 回放素材：4 PGM（921616B=15B 头+921600 像素）；像素抽查
  corner=240 / part1 内 (140,140)=28=(20+(60%13)) / (125,124)=20=(20+13%13) /
  场外=240，与纹理公式逐位一致；concat 清单含重复帧段与末条补齐。
- PC 无 ffmpeg，mp4 组装验证留 Pi 侧执行（runbook 已写）。

## 待办

- 用户：烧卡（Raspberry Pi OS Lite 32-bit + SSH）、提供 IP/凭据 → 执行 R1 跑分
  （组包→selftest→bench→compare 字节级对照→三方表入档）。
- 线到货后：R3 实测（组装 mp4 → Pi 播放 → PYNQ IN 换源/EDID/重复帧验收）。
- 理解题 3 道已出（见当日会话）；10-04 按用户指令提交，见下节提交记录。

## 提交记录（2026-10-04）

- 用户指令「分commit提交，合并PR，同步各分支」放行本批 commit。
- 理解门槛状态：10-03 出 3 道理解题；10-04 以选择题形式重出（mock `--host`
  行为语义 / 重复帧段构造方式 / R1 红线边界），**当日未收到作答，按用户明确
  指令提交**；问答若后续补答，追加至本文件。
- 提交拆分：① `vision_mock_service.py --host`（代码）② `make_replay_scene.py`
  （代码）③ `pi-dev-roles.md` 文档 + `hardware.md` 链接 + 本记录。
- 提交前复验：`bash sim/scripts/run_vision_python.sh` **7/7 PASS**（2026-10-04 重跑）。
