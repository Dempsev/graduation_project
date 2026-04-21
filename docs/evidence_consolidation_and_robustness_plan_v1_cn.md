# 收口改进与 Robustness 执行顺序 V1

## 1. 结论

当前主线已经稳定，接下来要做的不是重开方向，而是继续把证据链收紧。

后续固定做 4 个收口型改进：

1. 讲清 predictor-guided line 和 exploratory real search 的关系
2. 补一个同预算视角的 baseline 对照
3. 把弱 band shortlist 价值做得更直接
4. 回答 canonical case 周围是“尖点”还是“小盆地”

其中第 4 点本质上就是第 6 步 robustness 的核心入口。

所以可以把后续理解成：

- 前 3 项：证据收口与论证增强
- 第 4 项：进入轻量、服务主线的 robustness

## 2. 这四项改进怎么定位

### 改进 1：澄清 predictor-guided 和 exploratory real search 的关系

要固定的口径是：

- predictor 负责 shortlist 和方向感
- shape-aware front-end 决定搜索起点质量
- exploratory real search 负责真正把弱 band 打开

不要让人误解成：

- exploratory v2 完全脱离 predictor
- 或 predictor 已经单独解决了一切

更准确的系统定义是：

**prediction-guided + shape-aware + real-search refinement**

### 改进 2：补同预算视角

要回答的问题是：

- strongest line 更强，是不是只是因为预算更多？

所以后面要补：

- 前 `N=100 / 200 / 400` 次真实评估时，各线 best cover / overlap 到哪
- 单位真实评估成本下，弱 band 的命中率和 best-case 提升怎样

### 改进 3：把弱 band shortlist 价值做得更直接

要回答的问题是：

- predictor 前排 shortlist 到底有没有明显价值？

更直接的做法是：

- 以 `band200_240` 为主
- 比较 predictor top-20
- 与 random-20 / generic-20 / 旧候选-20 做真实结果对照

### 改进 4：canonical case 局部稳定性

要回答的问题是：

- 我们找到的是稳定可用解，还是特别尖的偶然点？

这是 robustness 的核心，也是后面最有论文价值的一层。

## 3. 第 6 步怎么切入

第 6 步现在应该做，但要做轻量版，不开新大支线。

### 先做的部分

1. threshold sensitivity
2. ranking stability
3. canonical case 的 local neighborhood robustness

### 暂时不做满的部分

1. 大规模材料 profile robustness
2. 大规模跨物理配置 robustness
3. 很重的 manufacturing robustness

## 4. 具体执行顺序

后面建议严格按这个顺序走：

### 第一步

做改进 1：

- 固定 predictor / shape-aware / exploratory 三者关系的正式口径

### 第二步

做改进 2：

- 加同预算切片视角

### 第三步

做改进 3：

- 做弱 band shortlist 价值的小实验

### 第四步

进入改进 4，也就是第 6 步核心：

- 先做 predictor robustness
  - threshold sensitivity
  - ranking stability
- 再做 canonical cases 的 local robustness

## 5. Robustness 的具体对象

建议优先做这几个 canonical case：

1. `ep193_step51_contour_xy` for `band200_240`
2. `ep253_step54_contour_xy` for `band220_260`
3. `ep253_step54_contour_xy` for `band240_280`
4. `ep248_step27_contour_xy` for `band180_220`

局部扰动优先围绕：

- `a1`
- `a2`
- `b2`
- `r0`

先做小范围、一圈式扰动即可，不需要一开始就铺很大网格。

## 6. 最终操作判断

所以现在的正式判断可以固定为：

**这四个收口型改进都要做，而第 4 个改进就是当前第 6 步 robustness 的核心入口。**

执行上不需要把“做四个改进”和“做第六步”分成两套路线。

更准确的理解是：

- 先做前 3 个收口改进
- 做第 4 个改进时，就按轻量、服务主线的第 6 步方案推进

这样主线最稳，也最不容易发散。 
