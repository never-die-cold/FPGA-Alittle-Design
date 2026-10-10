# 2026-10-10 云端融合拉取与本机复验

本轮拉取把队友线的成果合入 dev/exe（PR #66 已把我们此前的 EXE 工作并入 main；随后
main 叠加了模型/离线检查流水线与 Q01 报文白名单修复，dev/exe 已同步至 b51d46b）。

## 本机复验（Windows 11 / Python 3.13.5）

- 我们线的 8 项 Python 回归全 PASS（vision_regs/localize/protocol/rounds/records/export/
  arm_localize/arm_localize_package）
- 打包五关全 PASS（build.log / build_v12.log）：selftest（含视口绿框与 CJK 字体断言）+
  HTTP mock 联调 + **FILE REPLAY 两条（队友新增）**+ 打包渲染
- 模型线测试中依赖 torch 的（inspection_model/inspection_replay）在本机跳过（训练环境专属）

## 报文契约 v1.2（同批交付）

- `vision_protocol.py`：mode=MOCK/LIVE 双轮廓（MOCK 保持 Q01 严格白名单；LIVE 放行
  class/score/decision）；status ∈ LOCATION_ONLY/CHECK_PASS/CHECK_FAIL/RECHECK；
  decision 结构与 verdict 一致性校验；prototype 布尔标记（离线产物代实时结果时必带）
- `test_vision_protocol.py`：新增 LIVE 正/负例 20+ 项（三条 PASS 行）
- 决策单 D6 回写（v1.2 冻结），Q01"不开放 LIVE/分类/工单判定"限制解除
