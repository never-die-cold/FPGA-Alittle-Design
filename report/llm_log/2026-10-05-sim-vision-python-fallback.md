# [2026-10-05] 协作记录：sim 工具——vision Python 解释器回退修复

> 标签：#工具链 #vision #bug修复
> 平台：Codex（VS Code 插件，WSL）＋ OpenCode ｜ 模型：Codex = GPT-6 Astra（gpt-6-astra）；OpenCode = deepseek-flash（deepseek/deepseek-flash）
> 相关 commit：本次提交（`sim/scripts/run_vision_python.sh`）

## 1. 任务与初始提示词

修复视觉线 Python 门禁脚本的环境依赖：`run_vision_python.sh` 原先硬编码解释器 `python`，在只有 `python3` 的环境（如本 WSL）会直接失败，导致 `run_iverilog.sh all` 的视觉 Python 门禁报 `python: command not found`。

## 2. 模型第一版方案

把解释器选择改为顺序探测：

```bash
if [ -n "${VISION_PYTHON:-}" ]; then PY="$VISION_PYTHON"
elif command -v python  >/dev/null 2>&1; then PY=python
elif command -v python3 >/dev/null 2>&1; then PY=python3
else echo "ERROR: 找不到 python/python3；可用 VISION_PYTHON 指定解释器"; exit 1
fi
```

保留 `VISION_PYTHON` 显式覆盖，其余自动回退，找不到才报错退出。

## 3. 失败现象（真实偏差与未决项，如实记录）

1. 仅有 `python3` 的环境里，脚本固定用 `python` → `command not found`，视觉 Python 门禁无法运行。
2. 未决：本修复只解决解释器定位，不改变视觉 Python 用例本身的内容与判据。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | `all` 中视觉 Python 门禁报 `python: command not found` | 环境只有 `python3`，脚本硬编码 `python` | 增加 `VISION_PYTHON`/`python`/`python3` 探测与报错 | ✅ 门禁可在两种环境运行 |

## 5. 最终结论

`run_vision_python.sh` 现在优先用 `VISION_PYTHON`，否则回退 `python`→`python3`，都没有才明确报错。跨环境（Windows/`python` 与 WSL/`python3`）均可运行视觉 Python 门禁，不再因解释器缺失而误判为视觉回归失败。

## 6. 经验沉淀

- 触发条件：CI/仿真脚本依赖某个解释器或命令名，而在不同环境（Windows/MSYS2、WSL）名称不一致。
- 排查步骤：不要硬编码可执行名；用 `command -v` 顺序探测，并保留一个显式覆盖变量（如 `VISION_PYTHON`）；全部缺失时给出清晰错误而非静默失败。
- 适用范围：换平台/换 shell 均成立，是通用脚本健壮性清单项。 #skill候选
