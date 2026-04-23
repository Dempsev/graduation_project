# Target-Band Family Expansion Probe Round 2 v1

## 1. 目标

这一轮只围绕第一轮 family probe 中最值得继续的 `5` 个 family-target 做更小步长二次扫描：

- `band200_240 / ep130`
- `band200_240 / ep36`
- `band240_280 / ep183`
- `band240_280 / ep195`
- `band240_280 / ep253`

目标是把“第一轮看起来有效”的方向再确认一轮：

- 哪些 family 真的存在可持续提升的局部邻域
- 哪些 family 只是第一轮偶然抬了一点
- 哪些方向在 family 内是可重复的

## 2. family 分组逻辑

### `r0_family`

适用于：

- `ep130`
- `ep36`
- `ep183`

这些 family 的第一轮 best variant 是 `r0_plus_tiny`，所以 round 2 主要围绕：

- 更小的 `r0+`
- 对称的小 `r0-`
- 少量 `a1+ / a2+`
- 两个 `r0+` 耦合点

### `a1a2_family`

适用于：

- `ep195`
- `ep253`

这些 family 的第一轮 best variant 是 `a1_plus_a2_minus`，所以 round 2 主要围绕：

- 更小的 `a1+`
- 对称的 `a1-`
- 更小的 `a2- / a2+`
- 一个 `b2+`
- 一个 `a1+ + a2-` 的更细耦合点

## 3. 已生成文件

- [build_targetband_family_expansion_probe_round2_v1.py](/d:/graduation_project/coad/optimization/seed_ranking/build_targetband_family_expansion_probe_round2_v1.py)
- [build_targetband_family_expansion_probe_round2_v1.py](/d:/graduation_project/coad/optimization/runners/build_targetband_family_expansion_probe_round2_v1.py)
- [get_stage4_validation_config_tbf_probe_round2_v1.m](/d:/graduation_project/coad/stage4_validation/get_stage4_validation_config_tbf_probe_round2_v1.m)
- [run_stage4_validation_targetband_family_expansion_probe_round2_v1.m](/d:/graduation_project/coad/runners/run_stage4_validation_targetband_family_expansion_probe_round2_v1.m)

## 4. 运行顺序

### 4.1 先生成 manifest

```powershell
python D:\graduation_project\coad\optimization\runners\build_targetband_family_expansion_probe_round2_v1.py
```

### 4.2 再跑 stage4 validation

```matlab
run('d:/graduation_project/coad/runners/run_stage4_validation_targetband_family_expansion_probe_round2_v1.m')
```

## 5. 这一轮的完成标准

满足以下任一项即可视为成功：

1. `ep195` 或 `ep183` 明确再往上走一截
2. `ep130` 的 strong 状态稳定，甚至再提高一点
3. `ep253` 在高 band 邻域里继续被 small-step 推高
4. 明确证明某些 family 第一轮只是一次性抬升，第二轮无继续空间
