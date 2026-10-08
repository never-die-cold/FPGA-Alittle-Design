# 树莓派相机经 PYNQ 的实机检查（2026-10-06）

## 范围与当前状态

- 链路：CM3 → 树莓派 HDMI → PYNQ HDMI IN/OUT → USB 采集卡 → 电脑。
- 用户报告：接入 PYNQ 后电脑黑屏或无信号；PYNQ 未接网线，通过 USB 串口控制。
- 用户确认串口 COM12，并释放 MobaXterm 占用；115200、8N1、无流控。
- 本步不修改 RTL、板端脚本、系统配置；仅操作已有加载/冒烟入口并保存实测输出。
- PYNQ 装载及真实视频输入的帧首确认已通过；电脑采集画面的确认仍待用户反馈。
- 定位、CNN 分类和检查结果闭环未实现。

## 已取得的原始证据

- `serial-connect.txt`：COM12 返回 `xilinx@pynq:~$`，已登录。
- `serial-env.txt`：`hostname` 返回 `pynq`；读取板端文件 SHA256。
- `m2_onboard.py`：`679befc31ee11f0ab5ff4d7bf9d19ed83389750b12febdd3b90fdc27373664cd`。
- `vision_regs.py`：`1b30a62d27c9cedbc0e5cb94321984e343d903b4a84165fe5e0c4e13a7030479`。
- 上述两脚本与当前仓库文件哈希一致。
- 板端 `/home/xilinx/vision_m2/vision.bit`：`4f0c491a6383d8a11f87cd2de260027f519dbd466942d0b1b6e36198e39d5be5`。
- 本地 `sim/build/hdmi-project/vision.bit`：`38f24077254fc73efec275e34face61a061d41f6c2fa205a04a52c8e96e42b17`。
- 两份 bit 不同，不能据此声称板端对应当前本地构建或已确认包含断连修复。
- 首次 `sudo -n ... m2_onboard.py env` 返回 `sudo: a password is required`；当时未执行 env。

## 实测结果

- 用户随后提供凭据授权串口 sudo 验证；输入不写入日志。
- `serial-env-recheck.txt`：Python 3.10.4、PYNQ 3.1、三个文件均 OK、`PASS: env`。
- `serial-load.txt`：第一次加载失败，`No Devices Found`，提示 XRT 环境未初始化。
- `serial-xrt-env.txt`：板上 `/etc/profile.d/xrt_setup.sh` 设置 `XILINX_XRT=/usr`；
  `pynq_venv.sh` 激活 `/usr/local/share/pynq-venv`。用户环境已有 XRT 变量，sudo 子进程需重新初始化。
- `serial-load-xrt.txt`：root 子进程初始化以上环境后，`pipe @ 0x40000000 range 0x10000`，`PASS: load`。
- `serial-smoke.txt`：等待至少 3 秒后执行，`R11 busy=0 R12 applied=0`；
  提交后 `{'busy': False, 'applied_config_id': 1}`，`PASS: smoke`。
- 串口本轮默认字符解码使部分中文成为 `?`，英文判据和寄存器数值完整；保留原输出，不补写中文。
- 未改系统环境脚本、RTL 或板端 Python 文件；只加载板端现有 bit 并执行已有 smoke。

## 后续复现入口

1. 在 PYNQ 串口终端执行下面的 load；sudo 如需密码，由操作人完成验证。
2. 在 root 子进程初始化板端现有环境，而非仅指定 Python 绝对路径：

   `sudo bash -c 'source /etc/profile.d/xrt_setup.sh && source /etc/profile.d/pynq_venv.sh && python3 /home/xilinx/vision_m2/m2_onboard.py load'`

3. 检查 `pipe @ 0x40000000` 及 `PASS: load`。
4. 等待至少 3 秒，将上一命令末尾 `load` 改为 `smoke`，保存 PASS/NOVIDEO/FAIL 原始结果。
5. 用户确认电脑端出现实时相机画面；随后才记录真实源链路通过。

不以服务存活、文件存在或加载成功代替实际画面验证。本步尚未进行断连或冷上电测试。
