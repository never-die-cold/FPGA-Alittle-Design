# 根目录生成物归位与卫生检查修复

## 日期与版本

- 日期：2026-10-20；执行者：Codex（用户授权修复卫生检查）。
- 基线：`dev/riscv@04024d1`；保留本会话未提交的工单与索引改动，不 commit、不切分支。

## 命令

在仓库根目录执行；迁移前确认无 Vivado/XSim 进程，检查路径边界与重解析点，逐文件记录 SHA256；用 PowerShell `Move-Item -LiteralPath` 将三项生成物归位，迁移后逐文件复算哈希。

```powershell
python sim/scripts/index_runs.py --write
python sim/scripts/index_runs.py --check
python sim/scripts/check_repo_hygiene.py
git diff --check
```

备份完整性可从仓库根目录重新核对：

```powershell
$artifactManifest = Get-Content -Raw data/logs/2026-10-20-repo-hygiene/artifact-manifest.json | ConvertFrom-Json
foreach ($artifact in $artifactManifest.files) {
    $artifactHash = (Get-FileHash -LiteralPath $artifact.archived_path -Algorithm SHA256).Hash
    if ((Get-Item -LiteralPath $artifact.archived_path).Length -ne $artifact.bytes -or $artifactHash -ne $artifact.sha256) { throw ('Mismatch: ' + $artifact.original_path) }
}
Write-Output 'PASS: 7/7 archived files match manifest'
```

## 结果与产物

- 修复前：4 error，12 条历史重复文件告警；原始结果见 `hygiene-before.json`。
- 迁移对象：根目录 `.Xil/`、`clockInfo.txt`、`tight_setup_hold_pins.txt`，共 7 个文件；内容与空目录保留在 `build/run/root-hygiene-2026-10-20/`（已忽略，不入库）。
- 指纹与恢复位置见 `artifact-manifest.json`；`relocation-verification.txt` 记录 7/7 文件大小与 SHA256 一致。
- 验证结果：卫生检查 `errors: 0`、`repo hygiene: PASS`，索引 `run index: OK`，`git diff --check` 无输出，三项退出码均为 0；原始输出见 `validation.txt`。历史 12 条重复文件告警保留。

## 恢复与后续运行

如需恢复原现场，先确认没有 Vivado/XSim 运行、根目录同名目标不存在，再从仓库根目录将备份中的 `.Xil/`、`clockInfo.txt`、`tight_setup_hold_pins.txt` 分别移回根目录，并按 manifest 核对 SHA256；这会重新出现原来的 3 项根目录错误。备份只保存在当前工作区，不宣称能从 Git 重建缓存。

后续 Vivado 从 `build/run/` 下相应构建目录启动，使用脚本绝对路径，避免再次把缓存和诊断文本落到根目录；`.gitignore` 不替代根目录卫生要求。

## 边界 / 未完成

仅修复上述 4 项 error；历史重复证据告警不做删除或去重。未修改 RTL/TB/构建脚本、未生成位流、未执行板端操作；实体存储与首网硬件输出仍未实现。
