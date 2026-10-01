# 模块二跨分支离板复验（2026-10-01）

- dev/verify：8408ecc73aa8234445eb807325212e2cdd4aee17。
- dev/vision：d5ccd7ea9378387759ebda4913fb09faf047a2f2。
- 已执行 git fetch origin；其余远端 main/dev/rtl/dev/bench 与 dev/verify 同点。
- Icarus Verilog：13.0 stable；本次未复跑 Vivado/XSim。

## 可复现入口与原始结果

在对应 commit 的仓库根运行：

```bash
export PATH=/ucrt64/bin:/usr/bin:$PATH
bash sim/scripts/run_vision_iverilog.sh all
```

Windows 调用使用 C:/msys64/usr/bin/bash.exe -c，保留仓库根为当前目录。
验证仅使用对应工作树已有的 sim/vision tb、sim/scripts 入口和 data/golden 数据。
仿真生成物均在对应仓库 sim/build；原始输出统一归档到本目录。

| 版本 | 原始日志 | 结果 |
|:---|:---|:---|
| dev/verify 8408ecc | vision-baseline.log | 10 个 tb PASS，进程退出 0 |
| dev/vision d5ccd7e | vision-branch-baseline.log | 13 个 tb PASS（含 A5 共 14 行 PASS），进程退出 0 |

最新分支额外原始结果：

```text
PASS: cop_buf 3 frames ping-pong, 96 px replay = golden, ready-gate + concurrent write verified
PASS: vision_top v0.3 6 frames dual-path, display 768 px + cop 512 px, 0 errors (frame-latch verified)
PASS: A5 latency gray=1 gauss=25 gauss+sobel=49 cycles (1-row window lag model match), scaler throughput-based
```

日志含 rgb2gray 输入标记悬空及 scaler 数组组合敏感性警告；PASS 不等于零警告。
首次调用因 PATH 缺 dirname 未启动仿真；第二次 login shell 改变 cwd 亦未启动。
改用非 login 的 bash -c 并显式 PATH 后成功，上述失败不算 RTL FAIL。
其他工作树源码复验前后 git status --short 无输出。
当前仅新增复验日志/文档；git diff --check 无输出、退出 0。

## 结论边界

现有用例通过，不等于缓冲拥塞、真正异步配置、彩色显示或 HDMI 实机通过。
dev/vision 归档顶层 WNS=+2.934 ns 为 Synthesized OOC 报告，不是 post-route。
后续步骤与未实现项见 docs/vision-offboard-next.md；代码变更待步骤清单确认。
