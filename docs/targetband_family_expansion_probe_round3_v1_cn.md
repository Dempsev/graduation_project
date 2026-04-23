# Target-Band Family Expansion Probe Round 3 v1

## 1. 目标

这一轮只保留最值得冲的 `3` 个 family-target：

- `band200_240 / ep130`
- `band240_280 / ep195`
- `band240_280 / ep253`

目标非常明确：

1. 看 `ep195` 能不能被真正推过 `0.50`，进入 strong。
2. 看 `ep253` 是不是已经接近平台，还是还能继续上升。
3. 看 `ep130` 的新 strong 状态是不是能稳定再抬一点。

## 2. 方向设置

### `ep130`

围绕第二轮最优点 `r0_plus_tinier_a1_plus_tiny` 继续做 ultra-small 扫描：

- 更小的 `r0+`
- `r0+ + a1+`
- `r0+ + a2+`
- 单独 `a1+ / a2+`

### `ep195`

围绕第二轮最优点 `a1_plus_tiny_a2_minus_tiny` 做更细 `a1+ / a2- / b2+` 扫描：

- `a1+`
- `a2-`
- `a1+ + a2-`
- `b2+`
- `a1+ + b2+`

### `ep253`

围绕第二轮最优点 `a1_plus_tiny_a2_minus_tiny` 做同类小步长验证：

- `a1+`
- `a2-`
- `a1+ + a2-`
- `b2+`
- `a1+ + b2+`

## 3. 已生成文件

- [build_targetband_family_expansion_probe_round3_v1.py](/d:/graduation_project/coad/optimization/seed_ranking/build_targetband_family_expansion_probe_round3_v1.py)
- [build_targetband_family_expansion_probe_round3_v1.py](/d:/graduation_project/coad/optimization/runners/build_targetband_family_expansion_probe_round3_v1.py)
- [get_stage4_validation_config_tbf_probe_round3_v1.m](/d:/graduation_project/coad/stage4_validation/get_stage4_validation_config_tbf_probe_round3_v1.m)
- [run_stage4_validation_tbf_probe_round3_v1.m](/d:/graduation_project/coad/runners/run_stage4_validation_tbf_probe_round3_v1.m)

## 4. 运行顺序

### 4.1 生成 manifest

```powershell
python D:\graduation_project\coad\optimization\runners\build_targetband_family_expansion_probe_round3_v1.py
```

### 4.2 跑 stage4 validation

```matlab
run('d:/graduation_project/coad/runners/run_stage4_validation_tbf_probe_round3_v1.m')
```

## 5. 这一轮怎么看

如果 round 3 之后出现下面任一结果，就可以考虑收口：

1. `ep195` 过 `0.50`
2. `ep253` 提升幅度已经非常小，说明接近平台
3. `ep130` 的最佳点稳定保持在 strong 区，并且再抬幅度有限

也就是说，这一轮本质上是“确认门槛与平台”，不是再大范围探索。
