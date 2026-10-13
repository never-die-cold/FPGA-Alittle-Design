# PYNQ 测试原图的电脑软件诊断（2026-10-12）

基线 `dev/model@3e2e1c9`。用户明确本次只是测试，距离、背景和光照不作为最终标准；没有冻结参数或写入正式数据集。本步只调用现有仓库流程，无代码修改、提交或推送。

## 输入与复现

- 输入来自 [本次 N03 base 板端取帧](../2026-10-12-n03-base-return/README.md)，完整 1280×720 uint8 BGR。原 PNG 的字节/像素双哈希已与板端一致，未经改写。
- 输入 SHA256=`7e08be8bf54c40a0d19dd798ab8aaddfa68eda4e66f81b4e8ed0eb4c0016e015`；结束时再次核对未变。
- FP32 原型 `models/cnn-border-fill-best.pt` SHA256=`70fe3dc35bb592481f43e2086efe46b4ca5d2788d53a2b318d23a7169f7ecec6`；不是正式 INT8 模型。
- [input-hashes.txt](input-hashes.txt) 保留输入/模型指纹；代码和环境哈希见 [result.json](runs/test-real-board-001/result.json)。

在仓库根目录用现有主机 Python 3.12 执行：

```powershell
python src/pynq_host/inspection_run.py data/logs/2026-10-12-n03-base-return/board-raw.png data/logs/2026-10-12-real-frame-prototype/runs --weights models/cnn-border-fill-best.pt --request-id test-real-board-001 --order 2 1 1 --min-score 0.8 --max-targets 10
python src/vision_client/preview.py --replay data/logs/2026-10-12-real-frame-prototype/runs/test-real-board-001/result.json --headless --save data/logs/2026-10-12-real-frame-prototype/viewer.png
```

工单 2/1/1 为本图目视测试假设，非用户签署 GT；0.8 为已有候选值，非校准阈值。原始 [inspection-console.txt](inspection-console.txt) 与 [viewer-console.txt](viewer-console.txt) 均退出 0。

## 实际结果与定位缺口

- 原始输出：`FILE_REPLAY: RECHECK targets=36 actual=None`。退出 0 只表示软件处理成功，业务结果不通过。
- 图中可见两件螺栓、一件螺母、一件垫圈；定位阶段产生 36 个候选，超过临时 max_targets=10，触发 `target_limit`。
- `targets=[]`、actual/delta/missing/extra 均为 null，分类 predict 未执行；不能据此报告 FP32 分类准确率，也没有通过放行。
- [viewer.png](viewer.png) 已目视核对：FILE REPLAY、PROTOTYPE/RECHECK、OFFLINE FILE/OFFLINE SNAPSHOT 明确，计数显示未知，未当作 LIVE 或硬件推理。
- [localization-candidates.json](localization-candidates.json) 保存现有 `detect_boxes` 的候选框，退出 0；其中有 `[0,0,1280,501]` 大框及多个小块。没有改变定位参数来凑成四件。
- 额外候选复现：将 `sim/vision` 加入 Python 导入路径，`cv2.imread` 同一 PNG 后直接调用 `localization_opencv.detect_boxes(image)`；默认 color_threshold=22、min_area_ratio=0.00008。候选诊断不作精度验收。
- 源码依赖四角 Lab 中位数背景、颜色距离和形态学连通域。木纹、光照变化和角落蓝色物体可能影响背景估计，属于待对照验证的推断；本轮没有证明唯一原因。
- 窗口计时 232.754ms 为电脑上的定位/规则路径，不含模型冷加载/文件 IO，且本次未执行分类推理，不能当完整推理或板端性能。

## 待办

WC 定位链需用此失败原图复现候选大框/碎片，再补背景和照明对照；保留原始失败，不放宽数量上限绕过 RECHECK。本图不是正式训练或独立 test 数据。
N06 板端软件诊断、真实精度、正式数据/模型仍未验收。安全 custom DDR、CNN、核工业固件和真实 LIVE 闭环仍未实现/未接入。

Git 工作区和暂存检查原始结果保存为 `diff-check.*`、`staged-diff-check.*`。
