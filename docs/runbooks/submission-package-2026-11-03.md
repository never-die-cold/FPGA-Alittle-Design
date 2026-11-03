# 2026-11-03 源码交付包说明

当前默认交付物已改为 `build/artifacts/edgesight-code-20261103.zip`：
严格使用官方自主选题指南 §3.3.5.4 的七个目录，排除所有 DOCX/PDF/演示文稿和海报、旧技术报告。
保留必要的 Markdown 说明、技能包及协作记录；原 `models/`、`results/` 移入 `data/`，
工程笔记移入 `report/`，现用板端包位于 `board/runtime-r9/`。
解压后先运行 `python sim/scripts/prepare_submission_workspace.py`，恢复旧脚本依赖的原路径；
源代码内容不改写。包内 README 和 `build/submission/manifest.json` 为新版导航及清单。
以下为先前完整仓库快照模式的边界记录，可用 `--layout snapshot` 重新生成，勿把旧快照当代码专用包。

本包为当前工作区快照，包含尚未提交的修复，不是仅从 HEAD 导出的旧版本。
源码基线、分支、修改状态和逐文件 SHA256 见包内 `SUBMISSION/manifest.json`；
已跟踪文件的修改补丁见 `SUBMISSION/worktree.patch`，新增源码以实际文件交付。
现有文档中的历史记录保留原貌；本说明补充本次打包边界。

## 内容与边界

- 全部当前 Git 跟踪文件及未忽略的新源码，包括 RTL、固件、板端 Python、网页、测试脚本、依赖声明与已有证据。
- 额外纳入 `sim/build/cnn-r9-board-package/`：现用位流、HWH、r9 参数、加载工具及黄金向量。
- `sim/build/cnn-r9-live-20261103/` 保留 FP32、量化参数与训练报告；r8 初始权重和原始标注/ROI 同时纳入，沿用原路径。
- 原始 r6 开发包及历史证据仍保留。未部署的 r7/r10/r11 等实验输出不纳入，r8 仅作为 r9 训练起点。
- 不含 Git 历史、缓存、未选中的构建输出、`others/` 本地杂项和旧 `docs/tech-report/latex/` 草稿。
- **队友本地的最终技术文档、海报及最终演示视频需另行合并提交，本包不包含这些文件。**

## 使用入口

解压后先进入 `FPGA-Alittle-Design/`。PC 网页入口：

```text
python src/web_client/serve.py --endpoint http://192.168.50.99:8765
```

打开 `http://127.0.0.1:8000`，选择 USB Video；工单由用户在网页输入并应用后再 RUN。
训练标注中的场景数量仅属于训练元数据，不得用作运行工单。

板端服务入口为 `src/pynq_host/cop_product_service.py`；本次使用 r9 包、
`--background-mode local-fast --color-threshold 25 --min-score .8`，启动不预设 `--order`。
部署和启动前须完成板卡视频初始化，并按实际上传路径指定 `--package` 与新建的 `--root`。
`sim/build/filming-reboot-resume-r2/` 是当次启动证据，内含绑定历史 boot_id 的脚本，不能作为通用启动脚本直接执行。

## 验证口径

`sim/build/filming-after-boot-check.log` 记录重启恢复后 1 轮 HTTP 200、accepted=true、RECHECK，
只证明当次真实检查链路可响应，不代表工单通过或分类正确。
`sim/build/filming-guard-rounds.log` 保留此前 8 轮记录；之后发生系统失联并人工重启，长期稳定性未验收。
r9 新增标签为助手复核，训练/PTQ 的 39/39 是训练拟合，不能作为独立精度。
旧 9 件开发场景中 r9 INT8 为 7/9，低于 r6 的 8/9；因此本包是现场演示候选，不代表模型泛化已提升。
逐帧精确关联、正式独立精度与工业整机验收未完成；最近修复后的软件全量回归未重跑。
本包校验只检查文件完整性，不替代功能验证。

从原仓库重新打包并校验（不会连接或改动板卡）：

```text
python sim/scripts/package_submission.py
git diff --check
```

当前默认输出 `build/artifacts/edgesight-code-20261103.zip`，同时生成 SHA256 与校验结果。
已存在的包不会覆盖，可用 `--output build/artifacts/另一个英文文件名.zip` 创建新快照。
