# board —— 上板工程与实测输出

PYNQ-Z2 上板运行工程、启动脚本与实测输出记录。

模块一核＋最小 SoC 已完成收口，见[核收口报告](../report/module1-closure.md)。
模块二 HDMI RTL＋已验证视频链路已完成（RTL／链路级），见[10/03 视频记录](../data/logs/2026-10-03-vision-onboard/README.md)
和[10/07 真实相机恢复](../data/logs/2026-10-07-pi-pynq/README.md)；全项目 M2／CNN／工业闭环未完成。

## 板卡信息

- 板卡：PYNQ-Z2（XC7Z020-1CLG400C）× 1，**全队共用**
- 状态：✅ 2026-09-20 到货并完成上板验证（联网 / Jupyter / base overlay / 板载 LED）；SD 卡烧录完毕（PYNQ 镜像），已建立校园网 SSH 远程访问
- 远程访问（2026-09-20 建立）：校园网内 `ssh xilinx@<板卡内网IP>`（PYNQ 默认用户 `xilinx`）；Jupyter 为 PYNQ 默认端口 9090（`http://<板卡内网IP>:9090`）
- 关键硬件事实（写 XDC 用）：PL 板载时钟 125 MHz（引脚 H16）、4 个用户 LED、4 按键、2 拨码、HDMI IN/OUT 各一（均直连 PL）、板载 Micro-USB JTAG（Digilent SMT2）；官方引脚约束以 TUL master XDC 为准
- 共用约定：上板前在群里报备（谁、做什么、预计时段），错峰使用；每次实测按下方约定留记录

## 规划内容

- `setup.md`：从零复现指南（SD 卡烧录 → 部署 → 运行演示）——✅ 2026-09-20 建立
- `hardware.md`：演示硬件与 HDMI 接线（最终链路、配件清单、720p/HDCP 限制、验线步骤）——✅ 2026-09-20 建立
- `scripts/program_soc.tcl`／`program_soc.bat`：已有 JTAG 下载入口；默认路径修正本轮另批审核，暂显式传入对应位流路径
- 视觉加载／smoke／demo：见[板端操作说明](../src/pynq_host/ONBOARD.md)；自动开机加载未实现
- `logs/`：每次上板实测的原始输出日志（按日期归档）——✅ 目录与记录模板已建（`logs/README.md`）
- `media/`：演示照片与视频索引——🚧 待建

## 约定

- 每次实测记录：日期、硬件连接、bitstream 版本（commit hash）、结果
- 实测数据是评分硬依据，日志不删不改，只追加

> 当前已有上述实机证据；板端现用 vision.bit 与本地修复版指纹未闭环，现用位流长时间／冷启动／断连恢复待验证。下载成功不能单独代替功能观察。
