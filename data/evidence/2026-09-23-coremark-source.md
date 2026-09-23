# CoreMark 官方源码入库证据

> 用途：`docs/coremark_tb_contract.md` §4.1 要求——记录官方源码来源、固定 commit 与逐文件 SHA-256
> 采集：2026-09-23（基准线 `dev/bench`）

## 来源

| 项 | 值 |
|:---|:---|
| 仓库 | https://github.com/eembc/coremark |
| 分支 | `main`（浅克隆 `--depth 1`） |
| **commit** | `1f483d5b8316753a742cbf5590caf5bd0a4e4777` |
| commit 日期 | 2025-05-01 |
| 入库目录 | `src/riscv_fw/coremark/vendor/`（原样，禁止改动） |
| 获取命令 | `git clone --depth 1 https://github.com/eembc/coremark.git` |

## 逐文件 SHA-256（入库副本与上游逐文件比对，全部 MATCH）

| 文件 | 字节（LF） | SHA-256（LF，= 上游 git blob） |
|:---|---:|:---|
| `coremark.h` | 4760 | `42642B9A06C7ED2B3BD9EDA971B7C3868C4F5D27BF7EF6C4BBA11291A0C2598A` |
| `core_list_join.c` | 18225 | `CA00E4E010ECE47D7F040CB92AA50A95345A00D3171B59D088F6B243BE06CE7B` |
| `core_main.c` | 15788 | `17884C93C5B94378EB0FF02B4DF3725756CF2ADDB9B8CBCAA6200A4649FF5CA7` |
| `core_matrix.c` | 9598 | `ECDFF717B5A5C4907D221A606760E25499899CBF617582C05D40DB71C91351E4` |
| `core_state.c` | 9707 | `F4B84BB0A3452C45A4DAA664AB502BFDCCBD31CB57D93E9AC490C60937717A4E` |
| `core_util.c` | 6004 | `A3FBFCB9BB943B638624B8ECE01C5836DD56A96D7BCDE2697B248D077447327F` |
| `LICENSE.md` | 18582 | `9577B9C846F61FD69A0D8AC965998C6450C7D8969F71F0BB4A931B91AEBAD28A` |
| `README.md` | 19687 | `5581FB67DC1609CBD1865F150DBCB1050D96C602987792456850EB96EB0DD08C` |
| `coremark.md5` | 283 | `DAD92861212F8F012E75974E23EA97F7A275A375E0D3BC1D3B216423BA6B6306` |

## 规则

- 算法文件（`core_list_join.c` / `core_matrix.c` / `core_state.c` / `core_util.c` / `coremark.h`）**永不改动**（官方成绩规则）
- `core_main.c` 仅允许加"结果导出钩子"；实现方式为派生副本（父目录），diff 留证（见 `docs/coremark_tb_contract.md` §4.1）
- 许可：Apache-2.0（`LICENSE.md` 随入库）

## 复核记录（2026-09-23 入库时）

- vendor 文件统一 LF（= 上游 git blob 字节，入库后不被换行规范化改变）
- 逐文件 SHA-256 与上游 `git cat-file blob HEAD:<file>` 的 SHA-256 比对：9/9 MATCH（含 UTF-8 样例 `LICENSE.md`）
- ⚠️ 首批记录曾为 CRLF 工作副本哈希，2026-09-23 规范化后已作废并替换为上表 LF 值
- 复核人：基准线会话（OpenCode）；验证线独立复核待契约 §5.2 golden 流程时一并执行
