# 最终实板启动与网页工单接入

- 日期：2026-11-03（Asia/Shanghai）。
- 源码基线：dev/submission-slim @ 62324fe；本次新增诊断入口和运行证据。
- 授权：用户已接板，继续既有实板调试/修复/视频演示工作；沿用快速模式及本轮理解门槛豁免。
- 只读入口：`python sim/scripts/final_board_probe.py --output sim/build/onboard-final/initial.json`；PC设备用`sim/scripts/list_dshow_video.ps1`枚举。
- 初始结果：SSH已通过现有known_hosts校验，主机名pynq；8765端口拒绝连接；PC以太网192.168.50.1/24、1Gbps，USB Video和COM12存在。
- 产物：`initial.json`、`boot-journal.log`、`start-service.log`、`status-before-order.json`、`no-order-guard.json`、`uvc-initial/`、`deployed-sources.json`及软件回归日志；文件哈希见`artifacts.sha256`。
- 当前边界：已恢复真实视频/共存服务，尚未完成用户新工单下的真实检查、连续稳定性或识别精度验收。不修改队友最终材料，不混用10/30会话结果。

## 用户纠正与实际改动

用户明确：“我的检查工单是在前端输入进去的，不是我预先定好的工单，所以不要沿用了好不好”。据此停止沿用历史3/3/3等数量，不把目测实物数量当工单；补齐网页数量输入与板端确认，产品服务默认`order=None`且检查阻断，不再静默预设2/4/4。显式CLI --order仅保留工具兼容，本次启动未传。

网页输入三类数量、合计1–10，点击应用后通过`POST /v1/config`提交；服务轮次锁内校验→视频ACK→引擎/驱动/服务同步更新，下一轮驱动仍等待核侧CFG_APPLIED。编辑即暂停自动检查并撤旧结果；未确认、非法输入或不匹配ACK不得启用检查。协议补充见`docs/contracts/vision-sync-protocol-decisions.md`。

## 实际板端与PC状态

- boot_id：`89d82a5c-64cd-48d7-b8cf-51be273ccf62`。板端时钟为2026-09-23，记录日期按主机2026-11-03/Asia-Shanghai；没有修改系统时钟。
- 初始视频启动服务成功，但8765无监听。USB Video枚举索引1，24帧1280×720 BGR均成功，PNG字节与解码像素一致，已视觉检查为真实零件画面；并非CNN检查结果，不推断正式标签/数量或推理帧率。
- 独立新版应用：`/home/xilinx/cop-app-final-20261103-62324fe`；运行目录：`/home/xilinx/cop-live-final-20261103-r1`。保留所有旧应用/运行目录，不修改系统自启动。
- 部署：`python data/logs/2026-11-03-onboard-final/deploy-app.py`，上传后SFTP逐字节SHA核对38个源码/启动文件；此入口拒绝既有app/stage目录，复跑须换目录。
- 启动：`python sim/scripts/board_ssh.py --command 'bash /home/xilinx/cop-app-final-20261103-62324fe/start-service.sh' --log sim/build/onboard-final/start-service.log`。脚本检查当前boot、空闲端口、产品锁、冻结包bit/HWH哈希后重载共存包，不含--order。启动期间短暂连接拒绝为服务未就绪，随后启动命令退出0。
- 使用冻结r6包`/home/xilinx/cop-pkg-r6-multitarget-20261028-r1`，bit SHA256 `a929904866213f4133a6c12ee1a3dada0538ea99da6db89ab6f3fb6316807ce9`、HWH `f01b96a3f9435b369595ef7bcdaaa32980213130df6b4e9a0f0ff622cd8c3527`均核对通过；未重综合RTL。
- 新会话`6750ba53-4229-46ab-a777-3e8153e11ac9`，LIVE/C01/COP_HW/prototype=false，硬件健康true，config_id=1，work_order=null。未提交工单的POST /v1/check实际返回400，没有新检查结果。
- PC网页入口`python src/web_client/serve.py --endpoint http://192.168.50.99:8765`，仅监听`http://127.0.0.1:8000`。实际HTTP交付含工单输入区，转发新服务状态成功；用户浏览器操作尚待确认，未冒充完整UI实测。

## 离板回归与下一步

`bash sim/scripts/run_offboard.sh software`整条退出0，`software-regression.log`含`PASS: offboard software`，网页合计21项通过，新增`test_work_order_live.py`验证无预设/非法输入/配置失败不生效/新工单贯穿PS和模拟固件判定。最后增加的自动开关门禁由`web-final.log`复验。`git diff --check`及索引/卫生复核结果见会话。

用户在网页填写并应用工单后，先手动检查一次。随后运行`python sim/scripts/final_live_rounds.py --output sim/build/onboard-final/rounds-user-order --rounds 12`，此入口只读取用户已应用的工单，不代填预设；逐轮保存HTTP、耗时和报文，配置/会话变化或首次失败即停，保留故障现场。连续TASK_ERROR/DMA故障、纸边误框和分类误差仍待本次真实检查，不记为已修复。
