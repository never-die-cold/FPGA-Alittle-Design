# 检查 V0：取图、ROI 预处理与首次成功检查契约（建议稿）

日期：2026-10-09；审查基线 dev/exe @ 051aefa。
状态：设计建议，尚未完成实现/实机验收；不自动替换既有核、视频与 MOCK 协议契约。
“检查 V0/V1”是应用版本，与 RISC-V 核 v0/v1 分开命名。

## 1. 当前事实与首版取图选择

- 当前自定义 vision.bit：HDMI 彩色显示已上板；PS 经 AXI-Lite 配置，不具备完整图像读取通路。
- create_hdmi_bd.tcl 只将 snapshot_debug 接 ILA；没有视频 VDMA/像素存储读口。
- video_pipeline 默认分析快照 224×224、GRAY8，可经过高斯/Sobel；它不是原图 ROI。
- 10/07 的 1280×720、MJPG/30fps 是 Windows UVC 采集证据，不是 PS 读帧证据。
- 检查 V0 建议加载具备视频 VDMA 的 PYNQ base overlay，PS 用 hdmi_in.readframe()。
- PYNQ 官方默认 24 位 BGR；配置时显式选择 BGR，并检查实际 mode、shape、dtype、stride。
- 来源：Pi Camera Module 3 → Pi HDMI → PYNQ HDMI IN → VDMA → PS DDR。
- 接口目标：原分辨率 1280×720，uint8，HWC=(720,1280,3)，每像素 B/G/R 各一字节。
- HDMI 源目标 720p60；检查按人工触发，不承诺每帧推理；UVC30 与 HDMI60 分开记录。
- base.bit 与当前 vision.bit 是互斥的整片 PL 配置；切换 overlay 后重建驱动、重置服务会话。
- 保留 HDMI OUT 预览；base overlay 的显示延迟另测，不沿用自定义直通的延迟指标。
- PS 保存本轮完整 BGR 帧后释放采集缓冲；定位和所有 ROI 只读该副本，禁止混用后续帧。
- 使用软件 capture_id 明确标记来源；不假称它是当前 RTL 的 cop_frame_id。
- 清晰度待真实零件采图确认：记录最小零件/孔洞像素大小、对焦、运动模糊和曝光。
- 新增取图的同一帧同时用于训练采集与部署；base/custom 两条来源未经比对不得视为像素一致。
- 检查 V1 再在自定义 overlay 接原彩色帧捕获分支；现有低分辨率灰度快照不能替代它。

## 2. 建议采用的统一预处理

预处理标识沿用 scene-gray-border-padding-v1，正式模型必须显式携带此标识。
首版保持 PS 软件预处理，CNN 硬件接收已经处理好的输入，避免同时改变模型与缩放语义。

| 项目 | 规则 |
|---|---|
| 输入 | 同一 capture_id 的 uint8 BGR 原帧；不使用 EXE 截图或加框图 |
| 坐标 | 原图左上为原点，x 向右/y 向下；整数 XYXY 半开区间 |
| 有效框 | 0≤x0<x1≤1280、0≤y0<y1≤720；裁剪 frame[y0:y1,x0:x1] |
| 旧接口适配 | 旧闭区间参考框转换为 [x0,y0,x1+1,y1+1]；当前 MOCK 已统一半开区间，无须再加1 |
| 协议 | 新 LIVE 报文显式声明 bbox_format；当前 MOCK 与 EXE 按已合并协议采用半开区间 |
| 灰度 | cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)；输出 uint8 |
| 额外处理 | 首版不做 Gaussian、Sobel、直方图均衡或自动对比度增强 |
| 裁剪余量 | 首版不额外扩框；越界/触边候选转复检，不用截断后的残件放行 |
| 缩放目标 | 长边为42，保持宽高比；输出再居中填充为64×64 |
| 新尺寸 | w=x1-x0，h=y1-y0，s=min(42/w,42/h)；nw=max(1,round(w*s))，nh同理 |
| 插值 | cv2.resize(gray,(nw,nh),interpolation=cv2.INTER_AREA)；小 ROI 同样沿用此规则 |
| 尺寸取整 | Python round：正好半整数时取最近偶数；不改成向下取整或四舍五入 |
| 填充值 | 缩放后首/末行、首/末列拼接（角点重复），int(np.median(...))，向零截断 |
| 居中 | left=(64-nw)//2，top=(64-nh)//2；多出的一像素在右侧/下侧 |
| 像素张量 | uint8[64,64]，逐行排列；软件 float32[1,64,64]=pixels/255，无 mean/std |
| 模型批次 | NCHW=[N,1,64,64]；类别顺序 bolt/nut/washer |
| INT8 衔接 | 归一化后的量化由模型 scale/zero_point 决定，不能直接把 uint8 reinterpret 为 int8 |

- 当前行为依据：sim/vision/train_scene_classifier.py 的 preprocess(...,64,mode='border')。
- 建议后续抽取到 src/pynq_host/roi_preprocess.py，训练/评估/PS 共用；该新模块尚未实现。
- data/golden/vision/localize/reference.py 的拉伸64×64+定点双线性继续作为旧基线，不能替代本契约。
- OpenCV 灰度与 RTL (77R+150G+29B)>>8 不保证逐像素一致；INTER_AREA 也不等于现有 RTL scaler。
- 训练和板端记录 OpenCV/NumPy 版本；以真实 ROI 的 uint8 张量逐字节对拍作为兼容判据。
- golden 至少覆盖彩色通道、长条、奇偶尺寸、小图放大、单像素、边界框及非法/空框。
- 原图+bbox+预处理版本+uint8输出+SHA256 随用例归档；整数像素对拍须零差异。
- 如未来将灰度/缩放搬入 PL，另建预处理版本并重新评估/训练模型，不默换本版本规则。

## 3. 检查 V0 的成功定义

- 范围：静止工件、受控背景/照明、三类已知件、自由分散不遮挡、最多10件、人工触发。
- 工单允许三类非负整数，首版总需求1–10件；不开放零需求工单。
- 首个示例工单：bolt=2、nut=2、washer=2；每个目标须由真实定位产生，禁止固定框或人工指定框。
- 每轮锁定 session_id、request_id、work_order_revision、capture_id、model/preprocess/config版本。
- 请求后取得本轮新完整帧；记录采集获得时刻、计算耗时和接收时刻，不把计算完成时间当采集时间。
- PS 完成定位、统一裁剪、小CNN软件推理、数量核对；界面展示检查快照、框、类别和工单差额。
- 首次成功 = 框/类别逐件与人工真值一致、数量与工单一致、真实结果到达EXE、唯一批次记录落盘。
- 本轮原帧、全部ROI、预测、预期/实际数量、判定、耗时、版本及哈希须可追溯并能文件回放。
- PYNQ 现有证据为 armv7l/Python3.10；OpenCV与CNN部署运行时尚待核实，.pt不等于板端可执行模型。
- 检查 V0 暂由 PS 执行工单规则作软件基线；检查 V1 按主计划迁入 RISC-V，做同输入对照。

| 情况 | 规定结果 |
|---|---|
| 图像有效、无疑似异常、全部类别/数量匹配 | CHECK_PASS |
| 图像有效且分析完成，缺件/多余件/错料 | CHECK_FAIL，携带分类别差额 |
| 有效空图、当前非零需求工单 | CHECK_FAIL；无图像与空图必须区分 |
| 低分、触边、超10件、无法确认支持条件 | RECHECK；置信度阈值由开发集冻结，未知件可靠拒识尚未实现 |
| 无新帧、未连接、模型错误、任务超时 | ERROR/NO_VIDEO；不生成通过记录 |
| 旧会话/旧工单/旧配置结果或断联 | 撤销当前通过显示，保留历史记录并等待重检 |
| 同一 request_id 重试/重复保存 | 返回同一检查结果，批次最多一条 |

- 首轮冒烟：正常/缺件/多余/错料/空图/触边各3个独立真实摆放，共18例，人工真值提前固定。
- 另测断联/过期、请求重试、服务重启；不允许错误放行或重复批次；这不是工业可靠性统计验收。
- 单次正确闭环称“首次成功”；以上用例有仓库内回放/实机入口与原始证据后才称“V0收口”。
- V1增加：自定义彩色取图通路、INT8协处理器与RISC-V调度/判定；冻结同输入做软件/硬件对照。

## 4. 当前未实现与参考

- 未实现/未验：PS实帧采集验证、共用预处理模块、正式部署模型/运行时、LIVE协议、批次幂等与V0整机验收。
- 未实现：自定义overlay彩色帧读口、CNN协处理器、PS↔RISC-V应用接口与V1闭环。
- 依据：create_hdmi_bd.tcl、vision_axi.v、video_pipeline.v、训练preprocess、旧ROI参考及主计划。
- 官方取图/默认BGR依据：[PYNQ Video](https://pynq.readthedocs.io/en/latest/pynq_libraries/video.html)。
