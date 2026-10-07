# 保持三级的 Part C PC/flush 优化证据

- 额度刷新后的续工入口：`docs/partC-pc-depth-resume.md`；先查真实退出码和进程，勿重复启动。
- 分支/起点：dev/rtl@3c6b794，运行含未提交修改。
- 实际源码：source_manifest.json（含新增 tb），逐文件及聚合 SHA256。
- 首跑：all.log 为原始 stdout/stderr；all.exit.txt=1。RISC-V 与 vision RTL
  均 PASS，最后 vision Python 创建本地 HTTP socket 时被沙箱拒绝（PermissionError）。
- 第二次：all-unsandboxed.log 保留聊天中断前输出（无转发档 PASS）；
  后台进程已退出，没有完整退出码，不算全量通过。
- 第三次：经工具批准，run_all.sh 在沙箱外脱离会话执行相同完整 all；
  all-final.log 保存原始输出，all-final.exit.txt 保存实际退出码：**0，全量 PASS**。
  launcher.pid、all-final.started.txt 记录进程和开始时间；源码保持不变。
- 失败用例独立重跑：vision-http-retry.log，HTTP mock 合约 PASS，退出码 0。
- results.json 记录首跑四档实测与锚点核对；static.log 为语言/扫描/差异检查原始结果。
- 数据独立核对：`python3 data/logs/2026-10-06-partC-pc-depth/check_results.py all.log`；
  最终重跑：`python3 data/logs/2026-10-06-partC-pc-depth/check_results.py all-final.log`，PASS。
  检查源码指纹、四档原锚点、
  CRC/retired、分类守恒、RAW 差与 BHT hit+miss=lookup，不代替完整回归退出码。
- 复现：仓库根目录 `bash sim/scripts/run_iverilog.sh all`。
- 专项入口：`pc_control`（768 组旧公式等价）、`if_stage`（12 项保持/flush/复位）、
  `id_ex`（12304 项，包含全部 B 型偏移）、`bht_flow_off/bht_flow_1/bht_flow`。
- 全量日志保留已有 timescale/readmemh 警告，以及 vision 门禁自检的预期 FAIL 注入；
  不能以整份 all.log 不含 FAIL 作为判据，应检查对应自检 PASS 与总退出码。
- 优化前 BHT2 @11.520 ns：用户转述 WNS=-0.334 ns，17 级，Data Path=11.860 ns。
  原失败不被覆盖；本轮没有获取验证线原始报告。
- 优化后 Vivado：未验证，最低复测点 11.520 ns，四档另测 10 ns，见交接单 §5。
- 没有新增流水寄存器；没有修改 BHT 表更新或 muldiv 状态机；尚未 commit/push。

## 首跑已完成的四档功能锚点（不是 Vivado 时序结论）

| 档 | cycles | retired | CRC | lookup / hit / miss |
|:---|---:|---:|:---|:---|
| v1_nofwd | 19057438 | 10106386 | 8799 | 0 / 0 / 0 |
| v1_fwd | 17114141 | 10106386 | 8799 | 0 / 0 / 0 |
| v1_fwd_bht1 | 16335562 | 10106386 | 8799 | 1854101 / 1587055 / 267046 |
| v1_fwd_bht2 | 16232079 | 10106386 | 8799 | 1854101 / 1690538 / 163563 |

四档与修改前锚点完全相同；固件 OBS 中 `errors=1` 为既有 golden 配置所记录的值，
没有修改或隐去，不能据此宣称通过官方 CoreMark 认证。最终完整 all 同样匹配此表，退出码 0。
