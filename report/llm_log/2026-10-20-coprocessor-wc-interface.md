# [2026-10-20] 协作记录：K1 产出 WC 一页纸接口，解锁软件侧提前开工

> 标签：#coprocessor #接口契约 #文档 #mock
> 平台：Codex（VS Code 扩展 v0.162.0-alpha.17.2）｜ 模型：GPT-5
> 相关 commit：`b8496fe`

## 1. 任务与初始提示词

「出闸轮」K1：只从 C03 与 `design_v1` §17 摘录，产出 `docs/coprocessor-wc-interface.md`。
必须覆盖寄存器地址表、一次完整时序（写 START → 轮询 DONE → 读结果 → W1C）、busy/非法写/
超时/重复请求/旧结果的约定、16 B 结果字段，以及 mock 可顶替的地址；禁止把 `score_q15`
写成概率，禁止承诺未实现的寄存器。K1 完成即单独 commit，不等 K2–K5。

## 2. 模型第一版方案

按 4 KiB 窗口逐 offset 摘录 C03；明确 START 的写者是 RISC-V，PS/WC 只能 ABORT/SOFT_RESET；
把 `score_q15` 定义为归一化整数 logit margin（LIVE 上报 `score_q15/32767.0`）；
mock 只顶替同一窗口的已定义 offset，不改权限、不把 PS 地址写死为核侧 `0x8001_0000`。全文 64 行。

## 3. 失败现象

1. 首次全回归在既有前置用例全部 PASS 后退出 1：系统 `python` 缺 NumPy，属环境入口问题，
   不是 RTL 失败。
2. 换冻结环境后再次退出 1：固件构建链自检自动回退到 `riscv64-unknown-elf-gcc`，`.dis` 构建失败。
3. 首次 `git commit` 被只读 `.git` 拦下：`index.lock: Read-only file system`，未产生 commit。
4. 固件自检用 Linux 工具链重生成了已跟踪的 `src/riscv_fw/cop_job.dis`。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 系统 python 缺 NumPy，退出 1 | 环境入口问题，非 RTL | 改用 `COPROCESSOR_PYTHON=sim/build/vision-venv-full/bin/python` | 越过该点 |
| 2 | 回退 `riscv64-unknown-elf-gcc` 失败 | 交叉前缀不对 | 显式 `RISCV_CROSS=riscv64-unknown-elf-` | `.dis` 构建与故障注入自检 PASS |
| 3 | `index.lock: Read-only file system` | `.git` 无写权限 | 申请一次受控 Git 写权限 | K1 单独提交 `b8496fe` |
| 4 | `cop_job.dis` 被测试改写 | 生成物混入候选 | 按 HEAD 内容恢复，仅暂存 K1 文档 | `git status` 只剩 K1 |
| 5 | 整网段长时间无输出 | 正常长计算区间 | 不把“仍在跑”写成 PASS，继续等待 | `pattern`/`zero` 各 73,795 元素匹配，退出 0 |

## 5. 最终结论

`docs/coprocessor-wc-interface.md` 64 行，已单独提交 `b8496fe`。验证命令使用显式
`RISCV_CROSS=riscv64-unknown-elf-` 与冻结 Python：`run_coprocessor_iverilog.sh all` 退出 0；
`pattern` `logits=01fd01 class=0 margin=0`、`zero` `logits=04fd02 class=2 margin=2`，
各 73,795 元素逐元素匹配。实体 BRAM、整机/板级仍 UNVERIFIED；K2–K5 未开始。

## 6. 经验沉淀

- 触发条件：一键回归在别处 PASS、却在解释器/交叉工具链入口退出非零。
- 排查步骤：先区分「环境入口失败」与「RTL/断言失败」；固定解释器与交叉前缀重跑，
  并保留首次失败记录与退出码。
- 适用范围：换机器、换 WSL 发行版仍成立；不要用放宽判据来“修”环境问题。
#skill候选
