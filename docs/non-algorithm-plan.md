# 非识别算法工作包看板

更新日期：2026-10-12。范围排除CNN/定位/训练/量化算子实现，维护启动、接口、EXE与发布依赖；软件原型不替代真实硬件验收。

## 基线与状态

当前已合并基线为`3e2e1c9`（PR #69/#70/#71），旧dev/bench/Part C分叉不再是当前整合待办。本工作区另有未提交NC离板修复/输入审计，证据见[离板记录](../data/logs/2026-10-12-nc-offline/README.md)。执行分工以[三人清单](project-closeout-three-person-checklist.md)为准。

| 工作包 | 状态 | 依赖 | 版本与证据 |
|---|---|---|---|
| HDMI显示/捕获候选 | 显示链路已验证；C01捕获RTL/BD/候选位流与显示/状态诊断已有 | 原vision源码追溯、custom DDR完整副本和完整N02/N03验收 | [C01基线](c01-capture-implementation-baseline.md)；UVC正常不证明取帧安全 |
| 树莓派相机预览 | 开机预览有历史证据；完整HDMI恢复仍未验收 | 当前源/接收时序与EDID | `sim/scripts/pi-camera-preview.service`；[真实相机记录](../data/logs/2026-10-07-pi-pynq/README.md) |
| PYNQ 开机加载 | ⬜ 未实现 | 已验证 bit、XRT/PYNQ 环境、systemd 启动顺序 | 尚无“重启后未手动加载且出图”的证据 |
| HDMI启动/恢复 | 特定配置手动恢复有证据；完整冷启动/长测/物理拔插仍未验收 | Pi CEA720p60、采集卡共存与实际位流 | [N01现场记录](../data/logs/2026-10-10-onboard-n01/README.md)；不能用另一位流代签 |
| RISC-V核验收 | 核与最小SoC已收口 | 后续协处理器接入不退化 | [核收口报告](../report/module1-closure.md)；MMIO/工业固件仍未接入 |
| 板端控制/结果接口 | v1.2 MOCK/LIVE与FILE服务骨架已实现 | 真实取帧/MMIO/CNN、R12应用回执、HTTP请求级幂等 | [协议](vision-sync-protocol-decisions.md)；软件config_id不代表硬件生效 |
| Windows EXE | 视频/轮次、重连撤框、LIVE类别/分数/工单横幅、PROTOTYPE已离板验证 | 检查快照查看、真实硬件/目标机复验 | [客户端说明](../src/vision_client/README.md)；轮次叠加不是逐帧同步 |
| 工单/记录/发布 | 文件候选规则、手动有效轮幂等记录、v2/CSV/异常截图已有 | 核侧工单判定、真实闭环与最终发布 | [离板检查](offline-inspection.md)；记录去重不等于网络重试幂等 |

## 实施门槛

1. P0：NC按N01–N03复验实际位流与取帧；WC交DDR槽所有权/缓存适配，不能用stream_seq推测槽完成。PYNQ自动加载仍是独立待办。
2. P1：接真实后端时固定session/config/capture与硬件版本，配置须经R12确认。保留原核四档回归；新核MMIO按C03实现并同步核契约。
3. P2：复用已有规则/记录/CSV，补HTTP请求重试幂等、检查快照查看、真实工业场景与最终发布复验；不把“显示判定”写成“核已判定”。
4. C02/C03已冻结，C01完整取帧与C04应用语义仍待验收/评审。cop_*是分析快照接口，ILA不是PS像素读口；地址按真实BD与冻结契约核对。
5. 每例保存原始证据与实际版本；MOCK/FILE/PROTOTYPE不并入硬件识别统计，视频正常与DDR帧槽安全分别验证。

## 节点与未实现项

沿用主计划节点：10 月 12 日优先收口启动、视频、核验收、控制接口和 EXE 原型；10 月 20 日完成非算法工单与记录闭环；10 月 26 日完成发布材料和复现清单。模块三识别结果及准确率仍是外部依赖，不因节点到期改记为完成。

当前明确未实现/未验收：PYNQ自动加载、完整HDMI恢复/长测、custom DDR所有权/完整取帧、真实硬件HTTP/MMIO/CNN后端及R12回执、核工单固件、网络请求级幂等、检查快照查看与目标机最终发布。LIVE协议、文件规则与批次/CSV已实现，不能继续列为从零待办。
