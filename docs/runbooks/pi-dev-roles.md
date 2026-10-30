# 树莓派视频源与开发辅助工具

树莓派为 PYNQ 提供 HDMI 视频源；产品分析与工单检查运行在 PYNQ 的 PL/PS/RISC-V 上。接线、独立供电和上电顺序见 [硬件说明](../../board/hardware.md)，相机预览、720p 配置和自启动见[相机操作手册](pi-camera-preview-runbook.md)。

数据集像素从 PYNQ 采集，采集与标签要求见[采集规程](fastener-data-collection-protocol.md)。

## 定位参考与联调

- ARM 定位便携包的生成、自测与基准运行见 [arm-localize-runbook.md](arm-localize-runbook.md)。`sim/scripts/make_arm_localize_pkg.py` 是现役组包入口。
- 需要远程接口联调时，可在树莓派仓库副本中运行：

```bash
python3 src/pynq_host/vision_mock_service.py --host 0.0.0.0 --port 8765
```

该服务只提供标为 MOCK 的合成报文。网页端真实数据接线状态见 [前端说明](../../src/web_client/README.md)。

合成 HDMI 回放素材可由 `sim/scripts/make_replay_scene.py` 生成，用于换源、断联和重复画面测试；不用于识别精度统计。旧角色分工和 EXE 操作步骤保留在 Git 历史 `a631fd2`。
