# 2026-10-06 协作记录：vision_client 首次构建的 Windows 环境适配

> 标签：#vision #工具链
> 平台：ZCode ｜ 模型：GLM-5.3-Flash
> 相关 commit：本条随 README 命令修正同 commit 入库

## 1. 任务与初始提示词

按 `src/vision_client/README.md` 的离板构建入口复现 EXE 构建：`pwsh -File sim/scripts/build_vision_client.ps1 -Python python`。

## 2. 模型第一版方案

照 README 原样执行。

## 3. 失败现象

两次失败：
1. `python --version` 无任何输出——`where python` 命中 `C:\Users\<user>\AppData\Local\Microsoft\WindowsApps\python.exe`（微软商店占位 stub，非真实解释器）；构建脚本内 `import cv2` 报 ModuleNotFoundError。
2. `powershell -File ...` 报"在此系统上禁止运行脚本"（执行策略拦截）。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | ModuleNotFoundError + where python 指向 WindowsApps | 商店 stub 占用了 python 命令；真实解释器为 Python 3.13.5（py 启动器可达） | 构建脚本传 `-Python py` | pip 正常拉取依赖（cp313 轮子齐） |
| 2 | "在此系统上禁止运行脚本" | PowerShell 执行策略拦截 .ps1 文件加载 | 改 `powershell -ExecutionPolicy Bypass -File`（仅本次调用放行，不改系统策略）；pwsh 7 未安装，但脚本语法兼容 Windows PowerShell 5.1，无需装 pwsh | ✅ 三关全 PASS |

## 5. 最终结论

本机可复现命令：

```
powershell -ExecutionPolicy Bypass -File sim\scripts\build_vision_client.ps1 -Python py
```

输出三关：依赖装进仓库内 `sim/build/vision-client-deps` → `PASS: preview mock renderer packaged runtime` → `PASS: packaged EXE HTTP mock preview + unreachable route rejects, no UVC/board access`。`src/vision_client/README.md` 构建命令已同步此口径。

## 6. 经验沉淀

- 触发条件：Windows 全新环境首次跑仓库内 PowerShell 构建脚本。
- 排查步骤：`where python` 辨 stub（无输出 = 占位程序）；执行策略用单次 `-ExecutionPolicy Bypass`，不污染系统配置；先试 Windows PowerShell 5.1 再决定要不要装 pwsh 7。
- 适用范围：换题换板成立（任何 Windows 仓库脚本入口）；若队友机器存在同款 stub，`-Python py` 同样适用。
