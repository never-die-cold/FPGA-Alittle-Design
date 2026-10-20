# DeepSeek 工作结果独立轻量核查

- 日期：2026-10-19（Asia/Shanghai）。
- 源码：`dev/riscv @ faf7ca9196c14080b3c0fdf26645f214a0585b24`；审查差异基线 `7d6355b`。
- 任务：以静态检查和现有证据核对为主，限制重跑成本；不改变既有测试产物和源文件。
- 结果：指纹 23/24 匹配；PR 差异空白检查退出 0；短仿真工具未启动成功，无本轮仿真 PASS。
- 产物：`fingerprints.log`、`diff-check.log`、`targeted.log/exit_code`、`native-targeted.log/exit_code`；报告在
  [`report/llm_log/2026-10-19-deepseek-independent-review.md`](../../../report/llm_log/2026-10-19-deepseek-independent-review.md)。
- 边界：不跑全仓 all、整网、CoreMark、视觉全量、综合和板验；静态反例没有新增 TB 仿真确认。

## 文件指纹复算（PowerShell，仓库根目录）

```powershell
$count=0; $bad=0
foreach ($line in (Get-Content docs/runbooks/coprocessor-j04-handoff.md)) {
  if ($line -match '^\d+\s+([a-f0-9]{64})\s+(.+)$') {
    $count++; $expected=$Matches[1]; $path=$Matches[2]
    $actual=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $expected) { $bad++; "MISMATCH $path expected=$expected actual=$actual" }
  }
}
"FILES=$count MISMATCHES=$bad"
git diff --check 7d6355b..faf7ca9
```

原始结果：`FILES=24 MISMATCHES=1`，唯一不匹配项为 `src/riscv_fw/Makefile`。
`cop_job.hex/dis` 分别与原证据 `04df8821…` / `0abcb4ad…` 匹配。

## 两个短用例的仓库入口

```bash
export PATH=/ucrt64/bin:/usr/bin:/c/Users/ASUS/AppData/Local/Programs/Python/Python312:$PATH
export COPROCESSOR_PYTHON=python RISCV_CROSS=riscv32-unknown-elf-
bash sim/scripts/run_coprocessor_iverilog.sh task_ctrl
bash sim/scripts/run_coprocessor_iverilog.sh config_regs
```

本轮通过 `C:\msys64\usr\bin\bash.exe -c` 尝试执行上述两项，bash 在运行测试前即失败：
`NtCreateDirectoryObject(...): 0xC0000022`，退出 `-1073741502`，约 0.375 秒。
随后直接调用 `C:\msys64\ucrt64\bin\iverilog.exe -g2001 -Wall -s tb_cop_task_ctrl`
编译仓库该 TB 与 `src/coprocessor/*.v`，输出到已忽略的 `sim/build/deepseek-independent-review/`；
编译退出 `-1073741819`，约 8.929 秒，vvp 和 config_regs 没有执行。
停止追加复跑；原作者的 PASS 与本轮工具启动失败严格区分，不能将后者解释为 RTL FAIL。
