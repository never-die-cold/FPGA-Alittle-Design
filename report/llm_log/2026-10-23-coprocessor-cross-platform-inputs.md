# [2026-10-23] 协作记录：门禁输入的跨平台字节/LF 与 Verilog 声明顺序

> 标签：#coprocessor #manifest #跨平台 #可复现 #Verilog
> 平台：Codex（VS Code 扩展）｜ 模型：GPT-5
> 相关 commit：`23e8aef`

## 1. 任务与初始提示词

WC 两条反馈：① 会被 SHA256/CRC 的 manifest 与侧车哈希文本必须跨平台稳定，不能依赖宿主
换行转换；② `cop_axi_lite_cdc.v` 的寄存器声明必须位于首次使用之前，满足 Verilog-2001
解析顺序。要求提交这 3 个文件、跑对应模式与全量回归，本地不 push。

## 2. 模型第一版方案

`generate_payload_manifest.py` 改用 `write_bytes`：manifest JSON 显式 UTF-8、侧车 SHA256
显式 ASCII、全部 LF；`manifest.json.sha256` 对实际字节计算。`test_payload_manifest.py`
改 `read_bytes` 并断言 manifest 不含 `\r\n`。`cop_axi_lite_cdc.v` 仅把
`reg w_ack,r_ack,w_active,r_active;` 移到首次过程块使用之前，不改逻辑。

## 3. 失败现象

1. 文本模式写入在 Windows 可能生成 CRLF，导致同一内容在不同宿主上 SHA256 不同，
   包内 `sha256sum -c` 与下游复算会不一致。
2. 声明位于首次使用之后时，部分 Verilog-2001 解析器/综合器会拒绝或产生不一致结果。
3. 全量回归用本机 riscv64 工具链重生成了已跟踪的 `cop_job.dis`，属于无关工具链漂移。

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | 文本哈希随宿主换行变化 | 未显式控制字节 | `write_bytes` + 显式 UTF-8/ASCII/LF | `manifest_v1` PASS |
| 2 | 缺少回归护栏 | 只修生成器不够 | 测试 `read_bytes` + 断言无 CRLF | 负例可复现 |
| 3 | Verilog 声明后置 | 解析顺序不一致 | 声明前移到首次使用前 | `axi_lite_cdc` PASS |
| 4 | `cop_job.dis` 被测试改写 | 无关生成物 | 恢复到 HEAD，不带入提交 | 工作树干净 |

## 5. 最终结论

```text
PASS: manifest_v1 PROVISIONAL payload bytes=36032
      sha256=14a1993336c67c83c115b7e6a1e67b198b487b99f325569f693ea0e4d67f1393 crc32=0x2f760211
PASS: manifest_v1 20 tensors preserve J02 bytes; SHA256/CRC/padding valid; offset and OOB negatives rejected
PASS: axi_lite_cdc reset plus write/read payload cross intact; no all-ones folding
```

全量 `all` 退出 0，最后一条为 zero 组 73,795 元素逐项 PASS。Windows 整机门禁随后两次独立
复跑均 PASS（WNS +2.498、DSP 136/220、BRAM36 69/140、LATCHES=0、DRC=0）。

## 6. 经验沉淀

- 触发条件：文本产物参与哈希/CRC，或 RTL 在不同解析器/综合器间行为不一致。
- 排查步骤：凡入哈希文本一律 `write_bytes` 并显式编码与 LF；在测试里断言无 CRLF；
  Verilog 声明一律先于使用，不用“能编译”赌解析器宽容度。
- 适用范围：所有跨 Windows/Linux 的交付包与 Verilog-2001 工程。
#skill候选
