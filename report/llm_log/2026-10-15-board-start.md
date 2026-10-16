# 2026-10-15 协作记录：返板串口认证与视频基线恢复

> 标签：#vision #工具链
> 平台：Codex；未新增代码提交，HEAD `891cba2`。

## 1. 任务与初始提示词

用户表示已连接板卡，开始上板工作；确认树莓派相机经 HDMI 输入 PYNQ，
PYNQ HDMI OUT 接 USB 采集卡。按仓库开工清单先核查 N01 与原 vision 短基线。

## 2. 模型第一版方案

复用仓库串口、基线和 UVC 入口，保留原有未提交改动，不改 RTL。
先读取版本/哈希/PL 元数据，再完成 sudo 认证并恢复原 vision。

## 3. 失败现象

- 初始采集卡可读 24 帧但内容黑；PL 文件名/时间为 None，列出 base IP。
- `sudo -n true` 提示需要密码；用户终端未配置 `pwsh` 命令。
- agent 打开独立认证窗口后，用户另开同一入口，COM12 访问被拒绝。

## 4. 纠错轨迹

| 反馈 | 纠正 | 结果 |
| --- | --- | --- |
| pwsh 无法识别 | 改用 Windows 自带 powershell.exe | 入口可用 |
| COM12 拒绝访问 | 核对并关闭 agent 自己启动的 PID 42656，释放串口，取消遗留 sudo 提示；只保留用户一个认证入口 | COM12 实际打开成功；用户报告认证 PASS |
| sudo 状态未知 | 重新执行仓库串口入口验证 sudo，保存原始输出 | 退出 0，boot_id 不变 |
| 初始黑屏 | 加载已核对 SHA 的原 vision，执行有界 smoke，再读 UVC | load/smoke 均 PASS；24 帧及 PNG 回读一致，目视为真实紧固件桌面 |

## 5. 最终结论

原 vision 视频短基线恢复。最终 PL 路径为 `/home/xilinx/vision_m2/vision.bit`，
IP 为 pipe/ps7，boot_id 前后一致；精确命令、SHA、画面和退出码见
[证据](../../data/logs/2026-10-15-board-start/README.md)。
未修改 RTL/脚本，未提交。完整 N02/N03、C01 DDR、正式定标/采集仍待验收；
CNN 存储/MMIO/DMA、首网硬件输出、核工业固件和真实硬件 LIVE 尚未接入。

## 6. 经验沉淀

串口认证只允许一个入口持有 COM 口；agent 打开交互窗口后不应同时
指示用户再开同一入口。出现拒绝访问时先释放已知持有者，避免要求重启板卡。
可读 UVC 帧和 PNG 无损回读不证明画面内容、DDR 所有权或 CNN 硬件结果正确。
