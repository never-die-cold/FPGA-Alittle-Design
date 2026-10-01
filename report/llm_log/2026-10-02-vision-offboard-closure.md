# 模块二离板收口与文档一致性普查（2026-10-02）

执行：ZCode/GLM（接手 GPT/codex 离板冲刺断点）。用户授权：模块二除板上操作外全部干完、
多 commit、开 PR、同步分支；随后追加指令：全库文档标准统一检查。

## 1. 接手时的事实核查

- GPT 断点结论「物理 HDMI 构建还在跑」与事实不符：driver.log 显示布线完成、时序约束
  全满足、DRC 0 Error、bitgen 成功；仅 write_hw_platform 报 Common 17-69。教训：
  **接手断点先读原始日志再下结论**，门禁拒绝不等于全部失败（该日志含预期内 ERROR 文本）。
- 全量回归复跑退出 0（16 核测试 + 门禁 8 例 + 22 视觉 tb + 3 Python），XSim 23 PASS；
  接手复检日志 riscv-recheck.log / xsim-recheck.log 入库。

## 2. 技术决策记录

1. **commit 拆分原则**：按功能内聚拆 10 个提交（cop_buf → 原子配置 → vision_top →
   video_pipeline → 门禁 → Python 栈 → EXE → Vivado → 文档 → XSA 修复），文件级归属
   从属（如 axi_regs 同含拆分握手与原子提交时归主功能 commit），中间 commit 不承诺
   逐点可 bisect，最终态由全量回归背书。
2. **cop_buf 所有权语义**：writing 门控写使能 + 回放中/本拍启动回放的银行禁作写银行 +
   读启动即消费 + in_vs 覆写先撤销 valid 并计 drop_count。修复前失败日志刻意保留
   （copbuf-before.log），门禁拒绝即证据。
3. **原子配置契约**：R11 提交/busy（busy 重复提交 SLVERR）、R12 已应用编号回绕；
   config_bridge 请求/确认 toggle + ASYNC_REG + 稳定总线 max_delay 约束——**不用异步
   clock group 掩盖数据总线**（推翻 9/30 决策单 D10 的 2FF/帧首锁存吸收口径，10/5 评审追认）。
4. **XSA 修复**：工程模式 write_hw_platform 只认 impl_1 run 目录内 bit；build_hdmi.tcl
   改 launch_runs -to_step write_bitstream 后复制到 $out；对既有工程按同流程补导出成功
   （vision.xsa 含 .hwh，PYNQ Overlay 必需）。修复段对真实工程验证，全流程重跑留待下次全量构建。
5. **文档口径修正**（本轮普查）：板上无 ADV7611（dvi2rgb/rgb2dvi 定案）同步到 plan.md、
   根/docs README、design_v0 §2/§3/§5、10/5 评审单豁免批注；scaler 57.5 MHz 风险关闭
   （94.9 MHz + 全链 post-route +0.330）；A5 延迟 gauss+sobel 49→50；寄存器映射升 v1.1；
   tb 计数口径统一为「22 tb（Icarus+XSim 同判据）」。历史日志/评审单原文不回改，只加批注。

## 3. 理解题欠账（understand-gate）

跨两轮冲刺仍挂账：13ace18 的 3 道（rd_addr 空闲分支 / cap pend 感知 / x_acc 复位值）
+ 本轮待出 3 道（cop_buf 所有权竞争窗口 / config_bridge request-acknowledge 复位序 /
axi_regs aw_hold 与 bvalid 交互）。PR 描述已声明按 workflow §2 复核；**合并前补课落 llm_log**。

## 4. 证据

- 回归：data/logs/2026-10-02-vision-offboard/README.md（索引全表）
- PR：#48（dev/vision→main）、#49（codex/vision-offboard→main，同内容叠放）；均未合并
- 分支：main/dev/rtl/dev/bench/dev/verify 同在 8408ecc；dev/vision 快进 4c3139a
