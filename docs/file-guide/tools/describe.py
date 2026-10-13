"""Combine manually checked project roles with content/format-based descriptions."""
import re
from pathlib import PurePosixPath

from artifacts import artifact
from scan import clean_title, logical

CODE = {".py", ".v", ".vhd", ".c", ".h", ".s", ".sh", ".ps1", ".bat", ".tcl", ".xdc", ".ld", ".service", ".include"}
TESTS = {
    "axi_lock_reset": "断源时AXI域不被像素失锁复位拖死",
    "axi_split": "AXI写地址/写数据独立握手与响应反压",
    "cop_buf_stress": "快照争用、覆盖、排空和银行所有权",
    "video_real": "720p几何、彩色显示/快照像素及帧/配置号",
    "core_coremark": "CoreMark固定负载结果、CRC、周期与退休数",
    "core_fwd": "转发相关指令的结果与执行行为",
    "core_bht_flow": "分支预测集成与正确冲刷",
    "core_v1_hazard": "三级核数据相关的停顿/转发边界",
    "pynq_z2_clock_config": "板级时钟参数与目标核频率",
    "n03_buffer_lifecycle": "记录的PYNQ缓冲释放行为，使用替身避免真实munmap",
    "c01_artifacts": "产物复位配置错误及bit/HWH/XSA完整性拒绝",
    "c01_build_inputs": "构建输入CRLF精确恢复、严格哈希/字节数与篡改拒绝",
    "vision_records": "有效轮记录、同进程键去重、来源前缀与schema v2",
    "vision_rounds": "触发节流、超龄/断联撤框和服务新会话恢复",
    "vision_live_service": "FILE/LIVE轮次、产物落盘与软件配置号",
    "vision_live_standin": "合成LIVE替身的PASS/FAIL/RECHECK与PROTOTYPE",
    "class_aware_metrics": "类别/IoU匹配与共享预处理",
    "roi_preprocess": "共享ROI与原交付训练函数的逐像素一致性",
    "numpy_reference": "独立FP32卷积/网络阶段与PyTorch对拍",
    "int8_conv": "INT8卷积累加、步长/padding与INT32溢出拒绝",
    "int8_primitives": "INT8量化、舍入、scale编码与requant边界",
    "int8_tensors": "张量/逐通道权重与bias量化",
}
VERBS = {"train": "训练", "evaluate": "评估", "generate": "生成测试数据", "export": "导出",
         "check": "校验", "compare": "对比", "calibrate": "校准", "audit": "审计", "probe": "探测",
         "synth": "综合", "build": "构建", "run": "运行入口", "verify": "验证"}
GUIDE = {"scan.py": "盘点Git文件、读取文本前缀并识别目录/快照路径",
         "relations.py": "提取Python导入、RTL例化、测试入口和文档链接",
         "describe.py": "组合人工角色、测试目标和格式说明，标明归档副本",
         "artifacts.py": "说明日志、退出码、报告、张量和图像等证据格式",
         "render.py": "输出Markdown/CSV/JSON/HTML并校验覆盖与关联目标",
         "generate.py": "统一执行盘点、说明、关系提取和输出",
         "verify.py": "独立核对CSV/JSON/HTML/Markdown覆盖集合、说明和差异检查",
         "roles.json": "保存人工核对的核心项目文件说明",
         "roles-extra.json": "补充新增CNN/DDR文件及训练/基准工具说明",
         "script-roles.json": "保存核心构建、仿真和上板脚本的用途说明",
         "page.html": "提供可搜索、分页和查看双向关系的离线页面模板",
         "README-template.md": "提供阅读路线、目录地图和索引边界说明模板"}


def describe(path, text, relations, exact, names):
    pp, lp = PurePosixPath(path), logical(path)
    label, basis = "项目文件", "目录/格式与邻接文件"
    parent = next((r["path"] for r in relations if r["type"] == "所在目录说明"), "根README.md")
    context = parent
    if path.startswith("docs/file-guide/"):
        if "/tools/" in path:
            return "索引生成工具", GUIDE.get(pp.name, "索引辅助组件") + "；属于文档生成流程，不参与FPGA运行。", "工具源码/数据"
        return "生成的文件索引", f"本次逐文件说明的{pp.name}输出；与索引主页、完整CSV/JSON和校验清单配套，不参与产品运行。", "生成器输出"
    candidates = [value for key, value in exact.items() if PurePosixPath(key).name == pp.name]
    role = exact.get(lp) or names.get(pp.name) or (candidates[0] if len(candidates) == 1 and pp.suffix.lower() in CODE else None)
    if pp.suffix.lower() == ".md" and not role:
        title = clean_title(text) or pp.stem
        label = "协作历史记录" if path.startswith("report/llm_log/") else "历史/外包文档" if "/outsource/" in path or "/done/" in path else "说明/计划/契约"
        role = f"说明《{title}》的规则、过程或结果；其引用文件见关联栏，日期/候选/冻结边界按正文保留。"
        basis = "读取Markdown标题与链接"
    elif pp.name.startswith(("tb_", "test_")) and pp.suffix.lower() in {".v", ".py"}:
        subject = pp.stem.removeprefix("tb_").removeprefix("test_")
        purpose = TESTS.get(subject, subject + "对应模块/流程的正常与边界行为")
        label = "RTL测试台" if pp.suffix == ".v" else "Python测试"
        role = f"检查{purpose}；与关联栏的被测源码/回归入口配套，测试文件存在不等于这次运行已通过。"
        basis = "测试源码/被测模块与入口"
    elif role:
        label, basis = "RTL实现" if pp.suffix == ".v" else "接口契约" if pp.name.startswith("design_") else "软件/脚本/项目入口", "人工核对角色说明"
    elif pp.suffix.lower() in CODE or pp.name.startswith("Makefile"):
        label = "约束" if pp.suffix == ".xdc" else "RTL/IP源码" if pp.suffix.lower() in {".v", ".vhd"} else "源码/配置脚本"
        if pp.suffix == ".xdc":
            role = f"给{pp.stem}设置管脚、时钟或跨域时序约束；构建Tcl加载它，约束对象须与实际RTL/BD相符。"
        else:
            action = VERBS.get(pp.stem.split("_")[0], "实现/配置")
            syms = re.findall(r"(?:def|class|module|entity|proc)\s+(\w+)", text)[:4]
            detail = "，定义" + "、".join(syms) if syms else ""
            role = f"{action}{pp.stem}相关流程{detail}；实际导入、例化和文本引用见关联栏，与{context}配套阅读。"
        basis = "源码声明与局部引用"
    else:
        label, role = artifact(path, text, context)
    archived = path.startswith(("data/logs/", "data/evidence/")) and pp.suffix.lower() in CODE
    if archived:
        label, basis = "归档源码/输入副本", "快照路径＋对应源码角色"
        role = "这是该轮保存的源码/配置副本：" + role.rstrip("。") + "；所属实验与当前入口以关联栏区分。"
    if "hdmi-library" in path and pp.suffix.lower() in CODE:
        role = "锁定Digilent HDMI库的第三方源码/配置：" + role
    return label, role, basis
