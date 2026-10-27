# 2026-10-27 共存位流与真实检查链

- 基线：dev/riscv / bc37c08 + 工作区既有改动；快速模式，不提交。
- 输入：用户交接的 19:02 routed DCP；不复用其他构建的 gate_summary 或旧 bit。
- 目标：从现有 DCP 生成独立 bit，实板确认视频与 CNN 共存，再接真实散放场景。
- 入口：sim/scripts/finish_cop_product.tcl；后续实际命令、结果和指纹在本目录保存。
- 状态：进行中；原帧显示/采集配置的 PL 分析输出没有消费者，不能宣称 PL 高斯/缩放已接入此包。
- 边界：旧帧、模拟结果与历史独立 CNN PASS 不代替本轮共存上板结果。

## 本次实际结果

- `finish_cop_product.tcl` 从指定 routed DCP 导出独立新包，bit b2690b0a…，HWH 5b54d888…；完整指纹见 build-fingerprints.json。
- 本次重新分析：WNS +1.184 ns、WHS +0.005 ns；与交接时提供的数字分开记录；8192 IMEM 字逐一匹配。
- 新包 roi_001 硬件输出 [-12,-30,41]、margin53、score6837，matches_expected=true，见 board-golden-roi001-r2.txt。
- `live-api-r1` 两次新捕获及相同 trigger_ref 的幂等回放通过。首轮超限没有执行 CNN，第二轮确实执行；不得把两轮 API 成功都写成硬件计算通过。
- 结果槽错位：roi-integer-compare-r1.json 将同一 ROI 与 payload 整数参考比较，槽0全零，槽1=ROI0等，最后槽覆盖；这不是单纯分类训练问题。
- `COMMIT_RESULT` 修复的三目标用例旧版失败、新版通过。multitarget-build-r2-console.txt 记录 Vivado 子进程启动失败；修复版未上板。
- 现有 EXE 连接真实 UVC 与 HTTP，生成检查记录。工单由 2/3/4 更新为用户确认的 2/4/4；原记录不改写。
- 物理 Esc 中止界面操作；手动按钮核验和 CSV 导出尚未完成。定位/分类训练待换环境，最终 M2/M3/M4 未验收。

## 交付范围

仓库保留关键文本、ROI 字节、第二轮原帧及一张 EXE 固定记录截图。
完整临时运行目录、重复 UVC 图像、持续刷新的窗口截图和 Vivado 中间文件保留本地。
JSONL 里其余截图引用指向本地完整记录目录，本次精选归档没有包含所有重复截图。
每项入库文件的 SHA256 见 delivery-manifest.json；这些指纹记录的是本轮候选与失败证据，不代表生产验收。
复现入口和板端路径见[交接](../../../docs/runbooks/pynq-coexist-handoff-2026-10-27.md)。
