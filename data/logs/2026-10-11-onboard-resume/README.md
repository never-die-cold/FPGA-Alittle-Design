# N03 缓冲区生命周期原始记录（恢复）

- 原记录日期：2026-10-11；恢复日期：2026-11-03（Asia/Shanghai）。
- 来源：提交 `6bcd997`，blob `818d4e1025ab31331df3664a3dd424e687639158`；按原字节恢复，没有重造夹具。
- SHA256：`d68cbb8b81a788d448f133cd40107dc84a51b016f55a791296b20573119fcb9d`。
- 复现：`python sim/vision/test_n03_buffer_lifecycle.py`。
- 产物：`n03-buffer-free-lifecycle.txt`；供仓库测试回放记录中的 freebuffer 方法。
- 结果与边界：恢复后离板测试结果见 `../2026-11-03-offboard-fixes/`；不替代新实板测试，不证明历史 native crash 的完整根因。
