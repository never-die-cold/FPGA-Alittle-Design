# 2026-10-06 协作记录：Pi 相机服务化

> 标签：#vision #工具链；平台：Codex；相关 commit：未提交。
## 1. 任务与初始提示词
用户目标：CM3 经 Pi HDMI 和采集卡到电脑。后确认「正常，按方案继续」。
## 2. 方案
第 1 步普通账号 systemd 手动预览；第 2 步理解确认后 enable、重启实测。
## 3. 已知失败与纠错
普通账号初无 video；添加后旧会话仍报权限拒绝，重新登录后组生效。
720p60 曾出现花屏，后用户确认正常；根因尚未证明。
## 4. 当前验证
已知路径 /usr/bin/rpicam-hello；video 组生效；默认 multi-user，display-manager inactive。
Windows 无可用 WSL，systemd 语法验证和运行证据须由 Pi 回传；未预写 PASS。
## 5. 第 1 步讲解与理解门槛
User=edgesight 和 video 组让普通账号访问相机/显示；ExecStart 复用已验证参数。
Type=exec 确认程序执行，仍需画面验证。异常退出 5 秒重试且不限频，日志进 journal。
stop 发 SIGINT 正常释放资源；WantedBy 仅为 enable 提供目标，本步不 enable。
题 1：服务已占用相机时，再手动运行 rpicam-hello，会有什么问题？
题 2：复制服务文件并执行 start 后，为什么还不能称为开机自动启动已经验证？
用户答案与判定：待回答；第 2 步尚未执行，不得提交。

## 第 1 步实机初始反馈
原始输出：data/logs/2026-10-06-pi-boot/service-first-start.txt。
verify_exit=0；首次 start 后 active/running，但采样仅启动后 33ms。
请求持续状态、初始化日志和电脑画面确认，不把初始 active 写成相机稳态 PASS。
Loaded=disabled，开机尚未启用；本轮不进入第 2 步，理解答案仍待回传。

后续状态核对见 service-manual-check.txt：User=edgesight，active/running，NRestarts=0。
日志已注册 IMX708 并创建 DRM 预览，配置 1280×720 YUV420。
画面确认、理解答案仍待回传；开机启用未执行，未提交。

## 第 1 步理解答案与判定（完整记录）

用户原文：

> 1.正常 2.手动命令启动失败。3.服务“正在运行”和“开机自启”是两回事：
>
> - **正在运行** = 进程现在活着（`Active: active (running)`）
> - **开机自启** = 下次开机是否自动拉起（`Loaded` 行里的 `enabled`/`disabled`）
>
> 你看到 `disabled`，说明**开机自启是关闭的**。当前能运行，可能只是手动 `start` 过，或启动后一直没停。
>
> 所以不能算“开机自启已验证”，因为：
>
> 1. 服务是 `disabled`，重启后**不会**自动启动；
> 2. 真正验证要走完：`enable` → `reboot` → 重启后不手动干预，服务自动 `active (running)`。

判定：两题通过（2/2），画面确认正常。第一题补充原因：已有服务占用相机，
第二个进程通常无法取得相机资源；服务运行时避免并发启动手动预览。
第二题在当前服务方案下判断正确；验收必须观察新 boot 且不手动启动。
第 1 步已完成，开始第 2 步 enable/重启验证；尚未回传结果，未提交。

## 第 2 步后台复验
service-after-reboot.txt 已取得 enabled、active/running、User=edgesight、NRestarts=0。
新 boot 在约 12 秒完成 CM3/DRM 预览配置；HDMI 标准 720p60 和 YU12 平面已确认。
后台检查通过；此次回传未明确确认重启后电脑画面，不预写全链通过。
等待画面确认，未提交；PYNQ 相机路径尚未验收。

## 第 2 步收口与经验沉淀
用户对「本次重启后未手动启动，画面是否自动恢复正常」回复原文「自动回复了」。
据此确认本次重启自动预览通过；与 enabled、active/running、720p60 原始证据对应。
直连目标和两步服务化已完成，未提交；长时间/冷上电/PYNQ 验收未完成。
经验：旧 SSH 进程不会自动取得新附加组；KMS 实际输出必须查询实际 CRTC，
不能用 EDID 支持模式列表或旧 firmware 配置推断；active 必须配合初始化日志及画面，
开机验收需新 boot 且不手动 start。重启输出中的 Pi 时钟未校准，原始日期保留。
