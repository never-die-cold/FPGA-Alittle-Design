# 编译与检查记录

检查日期：2026 年 10 月 30 日。
文档版本：v0.1（LaTeX 版初稿）。源码基线：`dev/submission-slim`，提交 `a631fd2`。

## 编译环境

本机无系统级 TeX 安装。
TinyTeX v2026.10 取自 `E:\Projects\Project-Mozart\competition-materials\.build\latex-runtime\TinyTeX-v2026.10.zip`，解压到本仓库 `others/TinyTeX/`（`others/` 已被 `.gitignore` 排除，不入库）。
该 TinyTeX 缺中文字包，另从 tlmgr 使用的同一镜像 `tlnet.yihui.org/archive/` 手工补装 `ctex`、`xecjk`、`zhnumber`、`fandol`、`xpeek` 五个包，并用 `mktexlsr` 重建索引。

常规环境无需上述绕行：任一 TeX Live 2026 安装（含 `ctex` 与 `fandol`）即可编译。
本次为让 tlmgr/编译在本会话可运行，另做了一处本地补丁：`others/TinyTeX/tlpkg/TeXLive/TLWinGoo.pm` 的 `reg_country` 加容错（本会话进程无 HKCU 注册表访问权限，语言检测失败不再中止）。该补丁只影响 `others/` 下的工具副本。

## 编译

标准入口（与 Mozart 参考件相同的 latexmk 配置）：

```sh
cd docs/tech-report/latex
latexmk -r latexmkrc main.tex
```

本会话实际执行的等价命令（连跑三遍收敛目录与引用）：

```sh
xelatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build main.tex
```

结果：退出码 0，产物 19 页。`build/main.pdf` 约 2.0 MB。

最终 `build/main.log` 检查结果：

| 项目 | 结果 |
| --- | --- |
| LaTeX 错误 | 0 |
| 未定义引用 | 0 |
| 缺字 | 0 |
| Overfull / Underfull | 0 / 0 |
| 字体警告 | 0 |
| Rerun 提示 | 0（仅 rerunfilecheck 宏包横幅） |

内容规模：13 张表、7 幅图（均为仓库内实拍照片或 `make_tech_report_figures.py` 生成的配图，本次未使用图片占位框）。

## 静态检查

本机无 TeX 时的替代门禁，随源码入库，可重复运行：

```sh
python docs/tech-report/latex/check_tex.py
```

检查项：花括号平衡、环境配对、`\code{}` 内 `\_` 误用、`\code{}` 外裸下划线、`$` 配对、`\input` 与 `\includegraphics` 目标存在、`\ref` 有 `\label`、`\label` 唯一并被引用（未引用仅提示）。
本次结果：10 个文件，ERROR 0 项；8 条“章节 label 未被引用”提示（`sec:*` 标签保留供交叉引用，属正常）。

## 环境异常与绕行（如实登记）

本会话中，`xelatex` 在仓库路径（`docs/tech-report/latex/` 及 `E:\Projects` 下新建目录）无法创建日志文件，报 `I can't write on file 'main.log'`；同一目录下 `cmd`、`bash` 与各文件工具均可正常写入，最小用例可复现，`others/` 下新建目录则正常。
为取得真实编译证据，将字节相同的源码与配图镜像到 `others/texprobe2/` 编译，产物 `main.pdf` 与 `main.log` 回拷到本目录 `build/`。
源码为准，镜像仅构建副本，不入库。
解除条件：在常规 Windows 用户会话直接运行上述 latexmk 命令验证无此限制后，删除本条。

## 内容与版式

- 正文依次为作品概述、系统组成与软硬件划分、自研 RISC-V 核、视觉预处理流水线、CNN 协处理器、数据与工业闭环、完成情况与验收边界、总结，附录为复现入口、术语与素材清单。
- 所有图表均有标签并在正文引用；表格使用 booktabs 三线表。
- 性能数字均标注口径日期，来源为 `plan.md`、`report/module1-closure.md`、`report/project-final-status-2026-10-26.md` 与对应 `data/logs/` 证据目录。
- 未做逐页视觉人工复核（本会话无图像输入）。提交前建议人工翻阅一次 PDF。

## 素材缺口

- 网页端实机运行截图待补。桌面 EXE 形态已于 2026-10-28 退役，故未复用仓库里的旧界面截图（`fig_exe.png`）。
- 团队与成员信息、学校信息待补。
- 图片素材登记见附录表 `tab:materials`。
