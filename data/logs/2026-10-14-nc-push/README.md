# NC离板交付提交与推送

2026-10-14，用户要求上传当前产出，随后等待上板开工。提交范围为本会话docs、llm_log、data日志/指纹/原样源码快照，无生产代码/RTL新增或修改。
理解门槛按skill/understand-gate/SKILL.md文档/data记录豁免执行；NC的Q1/Q3/Q5确认已保存，Q5仍等待JL在[#75](https://github.com/never-die-cold/FPGA-Alittle-Design/issues/75)对齐与修复验收。
构建产物sim/build继续忽略；78MB便携ZIP拟上传GitHub草稿发布nc-offboard-20261014，附件SHA与已验收candidate-package.json相同，不作为正式硬件发布。
初始HEAD为5654eb5；fetch后HEAD与origin/dev/model为0/0，无远端独有提交。前置状态/引用、Git索引原样指纹和diff检查在本目录记录。
本次测试证据沿用本会话C04/N03/Windows打包的真实PASS与退出码，不将上传或文档归档当实机通过。
首轮索引检查88份非Markdown记录及三个runner SHA/长度通过；diff检查把原始CRLF的CR识别为尾随空白（exit2），staged-diff-check.txt原样保留。局部原始记录属性补充cr-at-eol后复查，保持原字节并继续检查真实尾随空白。
后续实际提交/远端/草稿附件结果由publication.json、push输出和远端检查记录，不提前宣称成功。
实际交付提交eeff74f302367f5063dd1d790222f84eeffc1884已push到origin/dev/model，push-delivery.txt/exit=0；远端引用独立核对同SHA。
[草稿候选附件](https://github.com/never-die-cold/FPGA-Alittle-Design/releases/tag/untagged-2811b27604fdc693611f)上传成功，publication.json记录draft=true、asset uploaded、78,183,698 bytes；服务端sha256:aed1205e470c0cac2b819d758bbb05b2131a0858d439ef53165ab812ab7f0393与本机候选一致。
草稿未发布正式版本；本目录上传结果与远端元数据在随后记录提交中一并push。等待上板期间不自动访问硬件，也未替JL确认Q5。
返板入口：[N03执行单](../../../docs/n03-custom-return-runbook-2026-10-14.md)；先核对boot/PL/哈希与原vision基线，再进行候选单帧实验。完整N02/N03、正式模型/CNN集成/核工业固件/真实LIVE仍待完成。
