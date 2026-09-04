# sim —— 仿真脚本与结果

各模块 testbench、仿真脚本与波形结果。**所有 RTL 模块必须先过仿真再上板。**

## 规划结构

```
sim/
├── riscv/           # RISC-V 核各级与整核 testbench
├── coprocessor/     # 协处理器 testbench
├── vision/          # 预处理流水线 testbench（含测试图样生成）
├── soc/             # SoC 级联调仿真
└── scripts/         # xsim 批处理脚本（可复跑）
```

## 约定

- 每个 testbench 输出 PASS/FAIL 自检结果，禁止只靠肉眼看波形
- 关键波形截图归档到 `report/`，供设计报告引用
- 黄金参考数据放 `data/`，仿真比对脚本引用相对路径

> 状态：🚧 待开发
