"""Explain retained artifacts using names, formats and adjacent evidence context."""
import json
import re
import struct
from pathlib import PurePosixPath

from scan import ROOT, clean_title

TYPES = {
    ".rpt": "Vivado报告", ".log": "原始运行日志", ".output": "工具原始标准输出",
    ".txt": "文本记录", ".sha256": "SHA256校验摘要", ".dis": "固件反汇编",
    ".hex": "十六进制数据", ".pgm": "灰度像素图", ".png": "无损图像",
    ".npy": "NumPy张量", ".pt": "PyTorch模型权重", ".yml": "结构化模型/配置",
    ".hwh": "硬件描述", ".xsa": "硬件导出包", ".bit": "FPGA配置位流",
    ".dcp": "Vivado设计检查点", ".xml": "IP接口/元数据", ".xci": "Vivado IP配置",
    ".pdf": "PDF资料", ".docx": "Word资料", ".ttf": "字体资产",
    ".patch": "源码补丁", ".csv": "表格数据", ".jsonl": "逐行JSON记录",
    ".json": "结构化结果/元数据", ".dat": "二进制或表格数据", ".data": "数据表",
    ".md5": "MD5校验摘要", ".jou": "Vivado命令日志", ".coe": "存储器初始化数据",
}


def artifact(path, text, context):
    pp = PurePosixPath(path)
    name, ext = pp.name.lower(), pp.suffix.lower()
    kind = TYPES.get(ext, "项目辅助文件")
    if name.endswith(".tar.gz"):
        return "压缩交接包", f"把{pp.name[:-7]}相关源码/数据/结果集合打成gzip tar包；与{context}的移交/哈希记录配套，不需当作单个源文件编辑。"
    if ext == ".bin":
        role = "原始输入文件字节副本" if name == "source.bin" else "原始清单/文件字节" if "manifest" in name else "二进制内容"
        return "原始字节副本", f"保存{pp.stem}的{role}；扩展名不说明像素或固件格式，需由{context}中的格式/哈希加载规则解释。"
    if ext in {".trace", ".pid", ".tsv", ".diff", ".gtcl"} or name == "weights_hex" or "bundled-python-unavailable" in name:
        roles = {".trace": "指令退休/执行轨迹，用于比较周期与提交行为", ".pid": "当时启动进程的编号，不能据此判断当前同号进程身份",
                 ".tsv": "制表符分隔的文件/读取快照清单", ".diff": "该轮源码差异补丁", ".gtcl": "第三方IP的GUI Tcl配置"}
        role = "解释器不可用时的原始失败/退出记录" if "bundled-python-unavailable" in name else "训练演练导出的权重十六进制字节" if name == "weights_hex" else roles[ext]
        return "归档轨迹/配置/数据", f"保存{pp.stem}的{role}；与{context}配套，历史失败、演练权重与正式验收分开引用。"
    if name == ".gitkeep":
        return "目录占位", "让Git保留尚无正式内容的目录；它不包含设计、数据或验收结果。"
    if name == "requirements.txt":
        packages = [s.split("==")[0].strip() for s in text.splitlines() if s.strip() and not s.startswith("#")]
        return "Python依赖清单", "列出该模块所需的Python包：" + "、".join(packages[:8]) + "；安装/打包入口据此准备环境，版本约束以原文件为准。"
    if "license" in name or name.startswith("ofl"):
        return "许可证", "记录这份第三方代码/字体/资料的使用许可与署名要求；需与同目录资产一起保留。"
    if name == ".gitattributes":
        return "Git配置", "对本目录证据的行尾/二进制和差异检查作局部约定；用于保留归档字节，与根Git属性叠加。"
    if name == ".gitignore":
        return "Git配置", "规定本目录生成物的忽略范围；它与根.gitignore共同决定哪些文件进入项目版本库。"
    if ext == ".rpt":
        role = "时序路径和slack" if any(k in name for k in ("timing", "path", "skew", "hold", "setup")) else "资源占用" if "util" in name else "设计规则检查" if "drc" in name else "时钟/跨域结构" if any(k in name for k in ("clock", "cdc")) else "该轮设计分析"
        desc = f"保存{role}报告，供{context}复查；它是工具输出，不是待编辑的RTL。"
    elif ext in {".log", ".output"} or any(k in name for k in ("console", "stdout", "stderr")):
        desc = f"保存{pp.stem}这次运行的原始输出，用于追查编译、仿真或现场操作过程；具体通过/失败与版本应结合{context}。"
    elif "exit" in name and ext == ".txt":
        code = text.strip()
        value = f"（记录值{code}）" if re.fullmatch(r"-?\d+", code) else ""
        desc = f"记录{pp.stem}关联命令的退出码{value}；需与同名日志的判据共同判断，退出0不能代替实机验收。"
    elif ext == ".sha256" or "hash" in name or "fingerprint" in name:
        desc = f"记录{pp.stem}相关输入/产物的指纹或校验数据；用于与同轮文件比较字节身份，不能单独证明构建来源。"
    elif ext == ".dis":
        desc = f"展示{pp.stem}固件编译后的地址、机器码和汇编指令；与同名hex/源程序配套，用于核测试定位。"
    elif ext in {".pgm", ".png", ".jpg", ".jpeg"}:
        role = "目标ROI裁剪" if re.match(r"target_\d+", name) or "roi" in name else "期望/对比画面" if any(k in name for k in ("expected", "compare", "annotated", "overlay")) else "采样/测试图像"
        shape = ""
        if ext == ".png":
            with (ROOT / path).open("rb") as handle:
                header = handle.read(24)
            if header[:8] == b"\x89PNG\r\n\x1a\n":
                w, h = struct.unpack(">II", header[16:24])
                shape = f"，尺寸{w}×{h}"
        desc = f"保存{pp.stem}的{role}{shape}；其合成/文件/实机来源及框/标签含义以{context}为准。"
    elif ext in {".hex", ".coe", ".npy"}:
        role = "目标ROI像素" if name.startswith("target_") else "逐层权重/偏置" if any(k in name for k in ("weight", "bias", "param")) else "期望输出" if any(k in name for k in ("expected", "golden", "output", "logits")) else "输入像素/张量" if "input" in name or "pixel" in name else "固件或数值测试向量"
        desc = f"以{kind}形式保存{pp.stem}的{role}；由对应加载器/testbench读取，位宽、排布和端序按{context}核对。"
    elif ext == ".json":
        try:
            value = json.loads(text)
            keys = "、".join(list(value)[:7]) if isinstance(value, dict) else "列表元素"
        except (ValueError, TypeError):
            keys = "具体字段"
        role = "文件清单及完整性信息" if "manifest" in name else "输入/设备/运行元数据" if any(k in name for k in ("metadata", "input", "config", "session")) else "实验结果或检查产物"
        desc = f"保存{pp.stem}的{role}，字段包括{keys}；与{context}中的生成/校验流程一起使用。"
    elif ext == ".jsonl":
        desc = f"逐行追加{pp.stem}记录，便于独立读取检查/异常事件；对应schema和来源标识由{context}解释。"
    elif ext in {".xml", ".xci", ".vhd", ".dat", ".data", ".pdf", ".docx"} and "hdmi-library" in path:
        desc = f"锁定Digilent视频IP库中的{kind}，属于HDMI接收/发送或接口配套资料；作为该轮构建输入保存，不是项目原创业务实现。"
    elif ext == ".txt":
        desc = f"保存{pp.stem}的文本记录或工具读回；用于{context}中对应步骤的对照，不从文件名推断PASS。"
    elif ext == ".ttf":
        desc = "供前端HUD绘制文字的字体文件；与字符清单、子集生成脚本及OFL许可证一起打包。"
    else:
        desc = f"保存{pp.stem}相关的{kind}；使用方式和来源应与{context}及同目录文件对照。"
    return kind, desc
