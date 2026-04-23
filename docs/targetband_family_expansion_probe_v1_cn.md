# Target-Band Family Expansion Probe v1

## 1. 目的

这一批是“优先级 1：weak-band near-miss family 内定向补样本”的首批可执行试点。

目标不是扩大全库，而是先回答两个问题：

1. 当前 weak-band near-miss family 能不能在小范围定向补点后转成更强 family。
2. 哪些 family 值得继续深挖，哪些 family 应该进入“暂缓/剔除名单”。

## 2. 首批 family-target 选择

本批共 `10` 个 family-target：

- `band240_280`: `ep183`, `ep195`, `ep205`, `ep252`, `ep253`
- `band220_260`: `ep206`, `ep248`
- `band200_240`: `ep36`, `ep130`, `ep193`

选择逻辑：

- 优先覆盖最弱的高 band：`240_280`
- 保留一部分 `220_260` 的 high near-miss family
- 用 `200_240` 做中间带补充
- 避免第一批就把 family-target 扩得过多

## 3. 每个 family-target 的 probe recipe

每个 family-target 固定 `10` 个点：

1. `center`
2. `a1_plus`
3. `a1_minus`
4. `a2_minus`
5. `a2_plus`
6. `b2_plus`
7. `b2_minus`
8. `r0_minus_small`
9. `r0_plus_tiny`
10. `a1_plus_a2_minus`

对应意图：

- `a1+ / a2- / b2+`：已知有利方向探测
- `a1- / a2+ / b2-`：反方向检查
- `r0_plus_tiny`：failure-boundary 探测
- `r0_minus_small`：半径敏感性对照
- `a1_plus_a2_minus`：near-miss 修正组合点

## 4. 已生成的文件

### Manifest builder

- [build_targetband_family_expansion_probe_manifest_v1.py](/d:/graduation_project/coad/optimization/seed_ranking/build_targetband_family_expansion_probe_manifest_v1.py)
- [build_targetband_family_expansion_probe_manifest_v1.py](/d:/graduation_project/coad/optimization/runners/build_targetband_family_expansion_probe_manifest_v1.py)

### Stage4 validation

- [get_stage4_validation_config_targetband_family_expansion_probe_v1.m](/d:/graduation_project/coad/stage4_validation/get_stage4_validation_config_targetband_family_expansion_probe_v1.m)
- [run_stage4_validation_targetband_family_expansion_probe_v1.m](/d:/graduation_project/coad/runners/run_stage4_validation_targetband_family_expansion_probe_v1.m)

### Analysis

- [analyze_targetband_family_expansion_probe_v1.py](/d:/graduation_project/coad/prediction_targetband_param_v1/tools/analyze_targetband_family_expansion_probe_v1.py)

## 5. 运行顺序

### 5.1 先生成 manifest

```powershell
python D:\graduation_project\coad\optimization\runners\build_targetband_family_expansion_probe_manifest_v1.py
```

输出目录：

- `D:\graduation_project\coad\data\ml_runs\targetband_family_expansion_probe_v1\validation_manifest_v1`

### 5.2 再跑 COMSOL stage4 validation

```matlab
run('d:/graduation_project/coad/runners/run_stage4_validation_targetband_family_expansion_probe_v1.m')
```

输出目录：

- `D:\graduation_project\coad\data\comsol_batch\stage4_validation_targetband_family_expansion_probe_v1`

### 5.3 最后做分析

```powershell
python D:\graduation_project\coad\prediction_targetband_param_v1\tools\analyze_targetband_family_expansion_probe_v1.py
```

分析输出目录：

- `D:\graduation_project\coad\data\analysis\targetband_family_expansion_probe_v1`

## 6. 这批结果怎么看

重点看三类结果：

1. 是否有 family 从 `<0.15` 提升到 `>=0.15`
   说明从 near-miss 提升到了 weak contributor。

2. 是否有 family 从 `<0.50` 提升到 `>=0.50`
   说明直接转成 target-band strong。

3. 哪些 family 不管怎么补都几乎不涨
   这些 family 应进入暂缓或剔除名单。

## 7. 这批做完后的决策规则

### 继续做的信号

- 有 family 明确转 strong
- 有多个 family 明确从 near-miss 进入 weak contributor
- `band240_280` 和 `band220_260` 出现可复制的有利方向

### 暂停的信号

- 大多数 family 只是重复旧 near-miss
- best cover 几乎不涨
- `r0` 类 failure-boundary 只是在重复已知失败，没有新增机制信息

## 8. 这批工作的定位

这一批不是新的 thesis 主线，而是：

- 对 frozen mainline 的定向 upgrade probe
- 对“是否值得继续扩 family 内样本”的低风险验证

如果这批有效，下一步再进入“小而异质”的新 archetype 子库；
如果这批无效，就不要继续在同风格 family 上追加大量样本。
