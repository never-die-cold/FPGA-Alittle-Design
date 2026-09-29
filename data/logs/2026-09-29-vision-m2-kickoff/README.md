# 2026-09-29 模块二开工：rgb2gray / line_buffer / gaussian_3x3 单元回归

> 目的：模块二（HDMI 预处理流水线）第一批 RTL 单元验证。由 never-die-cold（模块二 RTL 负责）在 src/vision/ 落地，tb 与黄金参考逐像素对拍。
> 结论：三模块 3/3 PASS，像素级 0 错误。

## 环境

| 项 | 值 |
|:---|:---|
| 基线 | main `e41fdc3`（模块二为新增文件，工作区未提交；与 dev/rtl 无耦合） |
| iverilog | Icarus Verilog 13.0 (stable) (v13_0)，MSYS2 UCRT64 |
| 黄金参考 | `data/golden/vision/rgb2gray/`、`data/golden/vision/gaussian3x3/`（`gen_*.py` 生成，脚本自带定点 vs 浮点自检） |
| 命令 | `bash sim/scripts/run_vision_iverilog.sh all` |
| 原始日志 | 本目录 `vision-all-fe80857-worktree.log` |

## 结果

| tb | 结果 | 说明 |
|:---|:---|:---|
| tb_rgb2gray | PASS | 128 px 逐像素对拍，0 错误 |
| tb_line_buffer | PASS | 同步读、同拍同址先读后写（旧值）、异址写读互不干扰 |
| tb_gaussian3x3 | PASS | 128 px 逐像素对拍（含四边复制边界与首行/末行钳位），0 错误 |

## 模块要点（实现口径 v0.1，详见 src/vision/design_v0.md §3.1）

- `gaussian_3x3`：双行缓存按行号奇偶轮替，输出行落后输入 1 行；末行在帧尾 vblank 冲刷（底邻居钳位为自身，约定 vblank >= WIDTH+8 拍，真实 HDMI 远大于此）；列方向三级读链自然产生 {左,中,右} 三列，左右边界用中列钳位；依赖 line_buffer 同拍同址先读后写语义读取"正在被写入的 buffer"的旧行。
- 高斯核 [1 2 1;2 4 2;1 2 1]/16 全移位加实现，无乘法器/除法器。
- 单元级帧格式为紧凑测试格式（WIDTH=16, HEIGHT=8 参数化），接 HDMI 真实时序时仅需参数放大 + 上游解码模块归一化到该流约定。

## 遗留

- scaler / sobel / osd_overlay / axi_regs / vision_top 未开工（scaler 依赖模块三网络输入尺寸拍板，vision_top 依赖 HDMI 通路选型，见 design_v0.md §5 开放问题）。
- 本批文件未 commit；与今日 verify 线产出（docs/partB-verify-plan.md 等）一并待用户确认后提交。

## 变更记录

| 日期 | 变更 | 作者 |
|:---|:---|:---|
| 2026-09-29 | 首版：模块二首批三模块单元回归 3/3 PASS | never-die-cold（模块二 RTL） |
