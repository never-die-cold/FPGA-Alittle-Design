# 采集规程与模板同步证据

2026-10-12，dev/model@3e2e1c9，续接用户的 continue。仅文档和示例模板数据同步；未改 RTL/生产 Python/寄存器或协议字段，未操作硬件、提交或推送。
变更：规程与交接包按现有审计器统一小写 session / 大写 light，引用 C02 已冻结的64×64及当前分工，区分 base/custom 和工具/人工覆盖能力；CSV示例补齐washer-a。返场/离板准备同步移除已解决的旧提示。

## 检查与复现

CSV由bundled Node v24.19.0的Artifact Tool导入/修改/检查/渲染，再由单元格值导出UTF-8/LF；只改A2(session_id)、J2(specimens)，其余值及15列表头一致。
template-before.csv保存原样输入；inspect-before/after.txt与三组before/after.png保存修改前后视图，已人工查看，无裁切。
prepare-template.mjs为此记录的生成入口。复跑时复制该文件到新的data/logs子目录（不要覆盖本证据），创建该目录的node_modules联接到bundled依赖，按技能运行edit/csv操作标记后执行`node <新目录>/prepare-template.mjs --write`。
template-before/after.txt及对应.exit.txt=0。任务内依赖联接已移除；依赖安装目录未改动。

现有仓库测试入口：

```powershell
python sim/vision/test_dataset_manifest.py
git diff --check
git diff --cached --check
```

实际Python为C:/Users/ASUS/AppData/Local/Programs/Python/Python312/python.exe（与上步回归相同）；dataset-manifest.txt / exit=0，行/半开框/空帧/非法字段及PNG格式/身份/重叠/数量限制检查通过。
bundled Python缺少cv2的初次输出以*.bundled-python-unavailable保留；换既有本机环境后通过，未安装依赖。

template-validator.txt / exit=0：实际CSV通过既有validate_row的session/light/specimen元数据检查；构造的1×1坐标仅供字段校验，不是GT或相机数据。
元数据校验复现命令（仅模板字段；不会生成或认证真实图像/GT）：

```powershell
python -c '
import csv,sys
sys.path.insert(0,"src/pynq_host")
from dataset_manifest import validate_row
r=next(csv.DictReader(open("docs/fastener-collection-log-template.csv",encoding="utf-8")))
b=dict(frame_id="frame_00001",session=r["session_id"],split=r["split"],light=r["light"],bg=r["bg"],spacing="1D",obj_id="1",x0="0",y0="0",x1="1",y1="1",notes="TEMPLATE_METADATA_ONLY")
assert {s.split("-")[0] for s in r["specimens"].split(",")}==set(r["classes"].split(";"))
for s in r["specimens"].split(","): validate_row(dict(b,**{"class":s.split("-")[0],"specimen_id":s}))
print("PASS: template metadata compatible with existing validator")
'
```
checks.txt记录本轮Markdown链接/空白、CSV保留项及源文件哈希；diff/staged-diff-check.txt和.exit.txt记录Git检查。

## 保持待办

机位/mm每像素/曝光/间距等仍待N04实测，CSV示例中的60cm和12帧不是实测结果；采集覆盖、标签/GT、朝向、相似帧仍需人工或后续实现。
未实现/未验收：custom DDR保护、正式数据/INT8整网、CNN RTL、核工业固件、真实硬件LIVE、完整N02–N05与C04/工业验收。
W01整体不因文档/模板修正自动冻结；上一轮原始审查及全量结果保持原样。
