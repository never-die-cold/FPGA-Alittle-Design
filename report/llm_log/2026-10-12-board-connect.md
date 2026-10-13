# 2026-10-12 用户返回后的板卡连接

用户授权继续连接已接好硬件的板卡，并确认已在独立 PowerShell 完成串口 sudo 认证、电脑以太网直连树莓派。本步使用已有仓库脚本，不改 RTL、不改网络、不提交或推送。

COM12 登录成功；认证后 `sudo -n true` 返回 0。保存系统、文件哈希和初始 PL 状态后，恢复板端原 `/home/xilinx/vision_m2/vision.bit`。load 与 smoke 均 PASS，帧首应用配置号为 1。电脑 USB Video 采集 24 帧、1280×720 BGR，PNG 回读一致；目视为天花板灯具。开始/结束 boot_id 一致，最终 PL 路径及 pipe/ps7 已确认，串口释放。

原始命令、初次认证失败、无匹配进程导致的 grep 退出 1、随后成功结果及限制均保留在 [证据目录](../../data/logs/2026-10-12-board-connect/README.md)。文件改动范围仅 `data/logs/` 与 `report/llm_log/`。

本步是连接和原 vision 短基线检查。PYNQ SSH、完整 N02/N03 验收、正式实物数据采集尚未完成；安全 DDR、CNN RTL、核内工业固件和工业 LIVE 闭环仍未实现/未接入。未以短采集替代项目闭环验收。
