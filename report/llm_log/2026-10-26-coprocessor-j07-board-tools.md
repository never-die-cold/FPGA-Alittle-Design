# [2026-10-26] 协作记录：J07 视频摸底、板端回传与 ROI 验收工具

> 标签：#coprocessor #J07 #ROI #板端证据 #工具链
> 平台：Codex（VS Code 扩展）｜ 模型：GPT-5
> 相关 commit：`1f99409` `bbb082c` `971d784` `e412e1d` `f5728a8` `6fbae3a` `3c596ca` `6be9c3f` `5c95789`

## 1. 任务与初始提示词

J07 摸底：评估视频接入架构/资源/CDC，不实现视频板顶；把 NC 板端回传变成可校验证据；
定义 ROI 数据集交接格式并做结构审计；收紧板端预检为“精确证据”；关闭 J07 台账并明确
唯一有效包与 OPEN。禁止把结构 PASS 当成标签/来源审核，也不得把旧包当有效交付。

## 2. 模型第一版方案

- `docs/coprocessor-video-integration-plan.md`：HDMI PL 取帧 vs PS USB/UVC、HP0 共享 vs 独立 HP。
- `tools/cop_payload_loader.py`：板端断言要求精确 clock/first-status/golden，不接受“近似正确”。
- `tools/summarize_board_run.py` + 回归：解析 NC 回传 JSON/串口日志，拒绝时钟、首读、错误码、
  序号、结果不匹配，只给数据结论。
- `tools/check_roi_dataset.py` + 合成夹具：校验尺寸/通道/bbox/split 覆盖/分布/逐文件 SHA256。
- `docs/roi-dataset-handoff.md`：ROI 目录、清单与来源字段；`plan.md`/NC 交接更新包台账。

## 3. 失败现象

1. 松散预检会把“能读寄存器”当成板端通过；必须要求精确 40 MHz、首次 STATUS=1、golden 全匹配。
2. 回传摘要若只比对大小/argmax，会漏掉时钟、序号、错误码与旧结果；必须逐项拒绝。
3. ROI 数据集可能出现缺 bbox、split 不覆盖、分布异常或文件被篡改；结构审计必须逐文件哈希。
4. J07 完整 720p 帧缓存放不进片上：保守相加 DSP 136/220、BRAM36 113.5/140，必须用 DDR；
   VDMA 帧槽所有权与 frame/ROI/result 身份未原子绑定，可能静默分类旧帧。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 预检只读寄存器 | 不是精确证据 | 要求 clock/首读/golden 精确匹配 | preflight 负例拒绝 |
| 2 | 回传摘要可能宽松 | 弱比对掩盖旧结果 | 逐项校验并只给 data-only verdict | `board_run_summary` PASS |
| 3 | ROI 目录结构不齐 | 缺来源/分布/SHA 校验 | 审计器 + 3 类 3 split 合成夹具 | `roi_dataset` PASS |
| 4 | 720p 缓存放不下 | 资源边界未写 | 计划明确 DDR + 身份绑定风险 | 文档记录 |

## 5. 最终结论

```text
PASS: roi_dataset synthetic 3-class/3-split fixture; dimensions, channels, bbox, split coverage,
      distribution, and per-file SHA256 audited; invalid samples rejected
PASS: board_run_summary accepts exact clock/status/golden data and rejects clock, first-status,
      error, sequence, and result mismatches; verdict remains data-only
```

`all` 退出 0，最后一条 zero 73,795 元素逐项一致。J07 只完成架构/资源/CDC 摸底，没有实现视频板顶。
唯一有效包为 `dist/cop-board-gate-5653d5911b76.tar.gz`（tar SHA256
`a342287dbce47e3d1f24e22b757243f97626d11336be248e88aed3fc805178af`），仍为 PROVISIONAL、
板上 UNVERIFIED。OPEN-BT-4 保持；OPEN-K2-1 已关闭；本轮未新增 OPEN。

## 6. 经验沉淀

- 触发条件：板端回传/数据集交接需要变成可复现证据。
- 排查步骤：预检要求精确值而非“能读”；摘要只接受数据结论并逐项拒绝；数据集审计覆盖
  结构、分布、来源与逐文件哈希；先写资源/所有权边界再谈实现。
- 适用范围：任何硬件回传与数据集交接；换视频源或板卡需重定资源与身份绑定。
#skill候选
