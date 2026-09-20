# PYNQ-Z2 从零复现指南（setup）

> 范围：SD 卡烧录 → 上电启动 → 网络（SSH / Jupyter）→ base overlay 验证。
> 依据：2026-09-20 首次上板验证（联网 / Jupyter / base overlay / 板载 LED 全过）；
> 标准流程与实测细节如有出入，以 `board/logs/` 实测记录为准。

## 1. 硬件与配件

- PYNQ-Z2（XC7Z020-1CLG400C）× 1 —— **全队共用**，使用前群内报备（见 `board/README.md`）
- microSD（≥8GB）+ 读卡器、网线、Micro-USB 线、12V 电源（或 USB 供电）
- 关键引脚/时钟事实见 `board/README.md`（PL 板载时钟 125 MHz = H16 等）

## 2. 烧录 PYNQ 镜像

1. 获取 PYNQ-Z2 v3.x 镜像（本机已有备份示例：`E:\pynq_z2_v3.1`）
2. 用 balenaEtcher：选择镜像 → 选择 SD 卡 → Flash（写入后校验）
3. 完成后安全弹出读卡器

## 3. 上电启动

1. 板卡启动模式跳线置 **SD 启动**（按板卡丝印）
2. 插入 SD 卡；接网线（校园网）；接电源
3. 上电后等待系统启动（约 1 分钟）；可接 HDMI 观察启动信息

## 4. 网络访问（2026-09-20 实测）

| 服务 | 地址 |
|:---|:---|
| SSH | `ssh xilinx@10.50.216.93`（PYNQ 默认用户 `xilinx`，默认密码 `xilinx`，登录后建议修改） |
| Jupyter | `http://10.50.216.93:9090`（PYNQ 默认端口 9090） |

- 若 IP 变化：在校园网管理端查询设备地址，或接 HDMI/串口终端后执行 `ip addr`
- 仅在校园网内可达；远程使用需与板卡同网段

## 5. base overlay 验证（issue #1 验收口径）

在 Jupyter 新建 notebook（或 SSH 后进 `python3`）执行：

```python
from pynq import Overlay
ol = Overlay("base.bit")
print("overlay loaded:", ol.is_loaded())     # 期望 True
```

板载 LED 点灯：base overlay 的 LED 由 PS 侧控制，调用方式随 PYNQ 版本略有差异
（示例仅为参考：`ol.leds[0].on()`）。首次实测的点灯代码与截图待补入本节或
`board/logs/` 最新记录——**以实测为准，不照抄未验证的 API**。

## 6. 常见问题

| 现象 | 排查 |
|:---|:---|
| 找不到 IP | 检查网线与校园网口；HDMI 终端看启动日志；确认 SD 启动跳线 |
| Jupyter 打不开 | `ping 10.50.216.93`；确认 9090 端口与同网段 |
| 启动失败/文件系统损坏 | 重烧镜像（第 2 节），换一张 SD 卡交叉验证 |

## 7. 使用后

- 按 `board/README.md` 共用约定归还并群内报备
- 每次实测在 `board/logs/` 留记录（模板见 `board/logs/README.md`）
