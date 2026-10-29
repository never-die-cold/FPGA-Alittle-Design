# 2026-10-03-arm-localize-baseline（最小留存）

> 状态：2026-10-29 提交瘦身连根删除 R1 基线包（45 MiB，唯一引用为自家 bench 注释，owner 确认）；
> 但 `sim/vision/test_arm_localize.py` 回归组仍引用其测试 fixture，故保留**最小子集**：仅本文件与 `two_targets.json`（439 B）。
> 大包（pc/board 三方跑分原始 JSON、PGM 像素与 manifest）完整存在于两处：git 历史 commit 88ac1c4；
> 本地 `others/submission-slim-backup-20261029.tar.gz`（data/evidence/ 全目录字节级包）。

## 用途

- `two_targets.json`：两目标合成图 fixture，驱动 `sim/vision/test_arm_localize.py`（箱/序/幂等/复用断言）与
  `test_arm_localize_package.py`（便携包自检 + 篡改负例）；
- 组包入口 `sim/scripts/make_arm_localize_pkg.py` 已按保留口径恢复（见 git 历史 88ac1c4 前 pi-dev-roles §3）。

## 变更记录

| 日期 | 变更 |
|:---|:---|
| 2026-10-29 | 瘦身后按回归依赖恢复最小子集；其余见上方备份与 git 历史 |
