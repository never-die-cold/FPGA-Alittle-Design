# 2026-10-27 启动竞争与 MMCM 工具修复

> 下文按执行过程保留历史状态；最终事实：v2 第二次正常重启自动成功，见 startup-v2-reboot-final.txt。
> 独立 CNN 四例（zero/pattern/roi_001/frame）均 matches_expected=true，10,000 次寄存器读取无错误，
> 见 cdc-*.json、cdc-zero-01.txt、cdc-remaining-cases.txt。后续共存实测发现多目标槽错位，
> 修复版本未上板，见[新交接](../../../docs/runbooks/pynq-coexist-handoff-2026-10-27.md)。
> 本目录保留关键文本和最后一次重启图像；其余本地中间图像和源码 before 快照不作为发布输入。

- 日期：2026-10-27，电脑 Asia/Shanghai；板端墙钟错误，使用 boot_id 和内核 uptime 对照。
- 源基线：dev/riscv / bc37c08 + 原工作区改动。本轮快速模式经用户明确授权，理解题留到最后；不提交。
- 范围：启动配置、loader/打包/诊断脚本，后续扩展至 AXI-Lite CDC RTL 与约束；均在本轮先说明范围后执行。原有并发改动保留，不提交。
- 原始诊断见 [并发审计](../2026-10-27-concurrent-agent-audit/README.md)。

## 1. 启动顺序

- 新 unit：`sim/scripts/fpga-vision-boot.service`，Requires/After bootpy.service；完成后保持 exited 状态。
- `sim/scripts/install_pynq_vision_boot.sh` 先保存 cron，再移除自动 vision / park 原型两行，保留 192.168.50.99 配置；失败时恢复配置。
- 板上备份：`/home/xilinx/fpga-startup-backups/2026-10-27-startup-clock-repair`，另已下载本目录 startup-backup-*。
- 第一次安装：`STARTUP_INSTALL_PASS` / exit 0；LoadState=loaded / active(exited)，见 install-startup.txt、startup-installed-status.txt。
- 第一次重启：boot_id 262586ac-0a30-4383-87df-f2538721a20a；119.049 秒 base.bin → 143.228 秒 vision.bin；原型服务未自启。
- 无手动重载/改线即抓到 24 帧真实相机图像：uvc-after-reboot/raw.png，标准差 37.669。
- 首版 ExecStartPost 复用 1 秒 smoke，首次锁定时返回 NOVIDEO，service 标 failed；原始失败留在 startup-first-reboot-post-timeout.txt。
- v2 改为 `pynq_vision_boot.py` 同进程加载后只提交一次配置，最多等 30 秒，不重复提交 busy 配置。
- v2 手动重启服务：`VISION_BOOT_PASS applied_config_id=1`、Result=success / active(exited)，见 startup-v2-status.txt；v2 的再次系统重启复验尚待完成。
- 未安装 systemd-analyze，使用实际 systemd LoadState、依赖与执行/重启结果验证，不声称 analyzer PASS。

## 2. 时钟和包

- 本机 PYNQ overlay.py 明确按 HWH 的 clock_dict 写 PS 时钟；ps.py 的 getter 读寄存器计算频率，不能把它笼统称作 Python 缓存回声。源码摘录 pynq-clock-source.txt。
- 原板端 fclk1_boot.py 错用 0x174；实际 PYNQ Zynq 定义 FPGA1_CLK_CTRL=0x180。本轮不运行该旧脚本，也不把 Zynq UltraScale 的 CLKACT 字段套到 Zynq-7000。
- loader 从 HWH 判断直连 / cop_mmcm；MMCM 不先设 40 MHz，不 pulse SLCR reset，下载后核对约 142.857 MHz 输入再访问 cop。
- 测试先复现旧工具失败（loader-before-fix.txt）；修复后保留直连用例，并通过 MMCM / 错误输入在 MMIO 前拦截（loader-after-fix.txt）。
- fast runner 共用 loader 初始化；C helper 默认保存在 package/runtime，避免用 /tmp 作为验证依据。
- 打包器拒绝已有输出目录；包 VERSION 写 clock topology、预期输入/输出和 bit/HWH SHA。
- 独立新包 build/board-package-mmcm-20261027-{diagnostic,trained}，各 12 文件 SHA 匹配；诊断包板上传输逐项校验见 upload-diagnostic.txt。
- 保留全部旧包；重复输出被拒且原 SHA256SUMS 未变化（package-no-overwrite.txt）。

## 3. 入口与当前边界

```powershell
python -X utf8 sim/coprocessor/test_cop_payload_loader.py --generated build/board-package-edge-fix/payload/provisional-model --network build/board-package-edge-fix/golden --output sim/build/payload-loader-clock-repair
```

板端新安装：将上述 service / installer / pynq_vision_boot.py 放在同一持久目录，root 执行 installer 并指定新的 /home/xilinx/fpga-startup-backups/<RUN>；已安装时拒绝覆盖。
回退：disable --now fpga-vision-boot.service；恢复备份 pynq-live 到 /etc/cron.d/pynq-live；移走新增 unit/runner；daemon-reload。回退会恢复旧自启动行为。
板端检查：`cop_slcr_status.py` 只读 PS 寄存器；`cop_runtime_snapshot.py --package <包>` 先核对当前 overlay 和时钟，再读 cop/DMA/GPIO。
DMA 正在单例验证；未将离板测试或视频恢复外推为硬件 CNN 验收。连续作业、正式模型精度、完整相机→CNN→EXE 仍未验收。

## 4. DMA 已推进到结果阶段，发现 CDC 旧读数

- dma-zero-01.txt：新 loader 读取 FCLK1=142.857143，权重/ROI DMA 均完成，logits=[2,-3,4]、margin=2、score=258；class/valid 首次解码错误，因此如实 FAIL。
- zero-01-snapshot.txt：DMASR=0x1002（完成），DMA_BYTES=4096、RESULT_SEQ=1、FW_DECISION=0x10403。首个 8 秒 snapshot 超时是 Python 启动预算不足，45 秒预算下成功。
- result-register-repeat.txt：版本地址第一次读到前一个 IP_ID，RESULT_SEQ 第一次读到前一个 SCORE；随后同址读正确。稳定 RESULT_META=0x03020000，字段本身正确。
- sim/riscv/tb_cop_axi_cdc_skew.v 人为让 payload 比 ACK 晚一拍到达：旧 RTL 必败；修改后 8 地址及反压 PASS；原有 CDC tb 同样 PASS。
- AXI CDC 控制请求/ACK 改为三级，保持 payload 两级，在控制与数据间留一拍稳定窗口；接口地址与字段不变。
- 旧 XDC 使用全异步 clock group，且 Vivado 原日志报 XDC 内 if 不受支持；现改为 opt_design 后 Tcl hook，检查实际 100/40 MHz 并约束 held payload / Gray pointer 延迟。
- 新构建目录 build/run/pynq_cop_cdc_20261027_r1；旧 bit/包未覆盖；新位流尚在构建，板端未验收该 RTL。
- 全回归初次因 Windows 无 make 命令中断（rtl-all.txt）；增加 mingw32-make 后备入口，固件门禁 PASS；全回归重跑见 rtl-all-make-fixed.txt。
