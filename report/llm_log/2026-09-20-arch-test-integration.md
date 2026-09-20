# [2026-09-20] 协作记录：riscv-arch-test 接入——目标移植 + 双预载签名比对（3 测试全 PASS）

> 标签：#riscv #验证 #工具链
> 平台：OpenCode ｜ 模型：opencode-go/deepseek-v4.1-flash
> 相关 commit：`643f258`（接入代码，由组长提交入库）；本条记录与理解门槛为**事后补记**（时间线如实记录，见第 5 节）
> 用途：Part C 验证闭环先行的第三方判据接入；RV32I 子集回归入口

## 1. 任务与初始提示词

验证线 Step 3：riscv-arch-test 接入，"编译/比对 signature 机制跑通，至少 1 组 RV32I 子集纳入回归"。

> "Step3 先不降级，先运行再说，今晚最后我来一起把三个人的工作合并"

## 2. 模型第一版方案

- 选 `old-framework-2.x`（套件自带 `references/*.reference_output` 参考签名，无需本机 ISS）
- 自建 target：`sim/arch_test/target/pynq_z2_v0/`（`model_test.h` + `env/link.ld` + 框架 Makefile 配置）
- `tb_arch_test.v`：统一镜像**同时预载 imem/dmem**，跑固定周期后逐字比对签名区
- `run_arch_test.sh`：make 编译 → nm 取签名符号 → bin2hex → 仿真比对；`fetch_arch_test.sh` 下载套件（不入库）

## 3. 失败现象（真实偏差）

1. **MSYS2 缺 make**：套件编译流程依赖 make，本机只有 makepkg → `pacman -S make` 安装
2. **Windows 无符号链接**：套件里 `device/rv32i_m/I/Makefile.include` 是符号链接（指向 `../Makefile.include`），Windows 检出为纯文本路径 → `*** 缺失分隔符`；本仓库 target 改为 `include $(TARGETDIR)/$(RISCV_TARGET)/device/rv32i_m/Makefile.include`
3. **MSYS2 PATH 无 git**：脚本里 `git rev-parse` 报"未找到命令" → 改为 `command -v git` 判断后回退
4. **架构冲突（设计层）**：本核是哈佛式（imem/dmem 两个独立模型），而 arch-test ELF 是统一地址空间 → 只预载 imem 会导致读初始数据的测试（如 `lw-align-01`）大面积 FAIL；解法：**同一镜像同时预载 imem 与 dmem**
5. **deprecated 宏告警刷屏**：定义了旧名 `RVTEST_IO_*` 触发套件迁移别名 → 只保留 `RVMODEL_*` 新名

## 4. 纠错轨迹

| 轮次 | 喂回的信息 | 模型诊断 | 修改内容 | 验证结果 |
|:---|:---|:---|:---|:---|
| 1 | make 缺失 | 环境依赖不全 | pacman 安装 make | ✅ 编译进入 |
| 2 | `缺失分隔符` | 套件符号链接在 Windows 失效 | 目标配置显式 include | ✅ 编译通过 |
| 3 | git 未找到 | MSYS2 PATH 无 Windows git | 脚本加存在性判断 | ✅ |
| 4 | （设计评审）哈佛 vs 统一镜像 | 数据区初值需在 dmem 可见 | tb 双预载同一镜像 | ✅ `lw` 类测试可扩展 |
| 5 | 告警刷屏 | 旧宏名触发弃用别名 | model_test.h 清理 | ✅ 日志仅剩已知无害告警 |
| 6 | 全流程复跑 | — | add-01/addi-01/and-01 | ✅ 3/3 PASS |

## 5. 最终结论

- **3 个 RV32I 子集测试全 PASS**（逐字签名比对）：`add-01` 588 字、`addi-01` 564 字、`and-01` 584 字
- 套件锚定 `6f7f47b`（old-framework-2.x，浅克隆，不入库）；证据与边界：`data/logs/2026-09-20-arch-test/`
- 跑法：`bash sim/scripts/fetch_arch_test.sh` → `bash sim/scripts/run_arch_test.sh add-01`
- **时间线说明**：接入代码由组长先提交为 `643f258` 并合并；理解门槛问答在提交后补做（记录如下）——与 `skill/understand-gate` 的"commit 前过门槛"要求存在流程偏差，如实记录，作为后续 AI 代码入库的注意项
- 后续：load/store、跳转等子集按需纳入；非对齐/特权/非 I 扩展不覆盖（套件有官方免责声明）

## 理解门槛（事后补记：逐段讲解 + 测试题 + 用户答案 + 判定）

### 逐段讲解稿（要点）

1. **与 self-check tb 的区别**：arch-test 由第三方出题，把指令结果按序写入"签名区"，与套件自带参考签名逐字比对——判据不来自我们自己，是"优化不改语义"的独立证据
2. **四个组成**：`model_test.h`（环境宏：HALT=自旋、签名区 begin/end 符号、无 IO）；`env/link.ld`（统一镜像 16KB@0x8000_0000）；target Makefile 配置（框架编译入口）；`run_arch_test.sh`（编译→取符号→转 hex→仿真比对）
3. **为什么双预载**：哈佛核取指看 imem、访存看 dmem；ELF 镜像统一编址，数据段初值只存在于镜像里——只灌 imem 会导致读初值的测试失败
4. **为什么固定周期**：核无停机信号，HALT 是死循环；跑够周期后签名区已稳定；周期不足会表现为签名不匹配（响亮的失败）
5. **符号提取**：签名区地址/长度随 link 变化，`nm` 从 ELF 取 `begin_signature/end_signature` 传给 tb

### 测试题 + 用户答案 + 判定

| 题 | 用户答案 | 判定 |
|:---|:---|:---|
| Q1 为何同一镜像预载 imem 与 dmem | "核心是哈佛式的，同步取指和异步 load 用两个独立存储器" | 🟡 讲了结构、未讲"数据初值可见"的必要性 → 补课后追加小题通过（见下） |
| Q2 签名不匹配说明什么、比数气泡 tb 强在哪 | "说明流水线改造有问题；强在**与微架构无关**、**覆盖广**" | ✅ |
| Q3 HALT 是死循环，tb 如何处理；100 周期不匹配说明什么 | "死循环后仅取指无签名；100 周期不匹配可能是功能错误，也可能是没跑完、时间不够" | ✅（补充：100 周期大概率是"未跑完"，靠增加周期与失配位置区分） |
| 追加：只预载 imem、dmem 全 0 会怎样 | "大面积 FAIL；add-01 不用 dmem，而 lw-align-01 会读初值" | ✅ 通过 |

**判定：通过**（Q1 经补课 + 追加小题通过；全量落盘）

## 6. 经验沉淀

- 触发条件：把第三方签名式测试套件移植到自研核（尤其哈佛结构/Windows 工具链） #skill候选
- 排查步骤：
  1. 选**自带参考签名**的框架版本（2.x），绕开本机 ISS 依赖；套件版本（commit）必须入档
  2. Windows 检出的符号链接会退化为文本文件——目标配置里显式 include 变量路径
  3. 哈佛核对"统一地址空间镜像"的通用解法：**同一镜像双预载 imem/dmem**
  4. 签名地址/长度从 ELF 符号表提取，不硬编码；固定周期 + 签名失配是"响亮失败"
- 适用范围（换题目/换板卡是否成立）：成立；任何"第三方 golden + 自研 DUT"的签名比对接入均适用
