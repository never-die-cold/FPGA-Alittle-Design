# 上板位流字节对应（2026-10-10）

归档的 `vision-2026-10-03-after-fix.xsa` 复制自同仓库另一工作树
`E:/Projects/FPGA-Alittle-Design-vision/sim/build/hdmi-project/vision.xsa`，
原文件和归档副本 SHA256 均为
`69ac73e04d39df52e5230345bd5e4ffca183c1dc12f8581a5b6c65f27783dead`。
复制后仅对归档副本做以下校验，避免另一工作树被清理后失去复现入口：

```powershell
python -c 'import hashlib,zipfile; p="data/evidence/2026-10-10-onboard-bit-provenance/vision-2026-10-03-after-fix.xsa"; z=zipfile.ZipFile(p); print("xsa_sha256",hashlib.sha256(open(p,"rb").read()).hexdigest()); [(print(n,hashlib.sha256(z.read(n)).hexdigest())) for n in ("vision.bit","vision.hwh")]'
```

原始结果：

```text
xsa_sha256 69ac73e04d39df52e5230345bd5e4ffca183c1dc12f8581a5b6c65f27783dead
vision.bit 4f0c491a6383d8a11f87cd2de260027f519dbd466942d0b1b6e36198e39d5be5
vision.hwh c0adfd3656c2fdb0468de356dc8232857580286d48977c41d6ee61edc3b7b5a5
```

两项内容哈希分别与板端
`data/logs/2026-10-10-onboard-n01/baseline/artifacts.txt` 完全相等。
`data/logs/2026-10-03-vision-onboard/hdmi-rebuild-after-fix.log` 记录了该次
Vivado bitgen 于 10 月 3 日 12:19:59 完成、XSA 于 12:20:06 导出且 PASS；
位流文件时间为 12:19:49。同日记录将此轮标为 AXI 复位修复后重建。
因此板端部署文件可以对应到该轮归档 XSA，不能再称为“修复前旧位流”。

该归档没有构建时完整源码快照或源码树摘要；修复提交 `3c4b852` 的
时间是同日 13:31，晚于 XSA 导出，不能仅凭提交时间断定构建采用了
该提交的干净工作树。字节对应也不证明本次 HDMI 热插拔一定稳定。
