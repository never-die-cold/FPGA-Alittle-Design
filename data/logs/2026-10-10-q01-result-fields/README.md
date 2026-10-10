# Q01 结果字段白名单复验

基线：dev/exe @ aa23206，当前未提交的修复仅涉及Python接口校验与协议测试。

复现入口（仓库根目录）：

```bash
python sim/vision/test_vision_protocol.py
bash sim/scripts/run_vision_python.sh
```

- before.log / before.exit.txt：新负例对旧代码，退出1，AssertionError: invalid packet fields accepted。
- after-sandbox.log / after-sandbox.exit.txt：字段用例PASS，本地HTTP访问被沙箱WinError 10013阻止，退出1；不是完整通过。
- after.log / after.exit.txt：授权环境协议测试完整PASS，退出0。
- 八组回归原始日志与 all.exit.txt：统一入口退出0；rounds超时/重握手WARN为故障恢复用例输出。
- Q01原始通过输出：PASS: Q01 result fields: 3 valid / 12 invalid packets。

Windows使用MSYS2 Bash，启动时PATH加入/usr/bin，调用现有仓库脚本；不依赖工作区外临时测试。
未涉及RTL、综合或上板；LIVE服务、共用ROI预处理、正式分类和工业闭环仍未实现。
