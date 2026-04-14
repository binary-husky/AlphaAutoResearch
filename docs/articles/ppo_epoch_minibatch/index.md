# Alpha Auto Research 自动化研究实录：PPO Epochs 与 Mini-Batch Num 对 LLM 强化学习训练的影响

![封面：四条 GRPO 训练曲线在全息仪表盘上攀升，minibatch_4 最亮最陡；背景是 GPU 机架与漂浮的策略梯度方程](https://serve.gptacademic.cn/publish/auto/ppoepochminibatch/cover.jpg)

用 LoRA 微调 7B 模型做数学推理时，一个常见的困惑是：`ppo_epochs` 和 `mini_batch_num` 这两个超参数听起来都是"让训练多转几圈"，实际调哪一个更划算？调大了会不会把训练搞崩？

下面是一次跑满 21.7 小时、4 组并行实验的完整回答。


![按步数对齐的训练进度](https://serve.gptacademic.cn/publish/auto/ppoepochminibatch/progress_charts.png)

---

## 1. 为什么由一套 Auto Research 系统来跑这个实验

这篇文章里的四组实验、九张图、甚至文字本身，都是由一套叫 **Alpha Auto Research** 的自动化科研系统跑完并整理出来的。它做的事情并不复杂：接到一个自然语言描述的研究问题，自己拆解出实验计划、写好蓝图（blueprint）、把任务分发到 GPU 集群、在训练跑完之后自动分析日志、画图、写报告。

工作目录长这样：

```
subject_ajet_ppo_epoch_and_num_minibatch_v2/
├── main_research_agent/  (顶层代理：plan / progress / final_report)
├── exp_stage_1/
│   ├── blueprints/       (每个实验对应 md+yaml 蓝图)
│   └── results/          (训练日志 + 自动绘图)
```

把这套流程自动化有几个实际的好处：RL 训练动辄十几二十个小时，人不可能守在屏幕前；所有决策都以文件形式沉淀下来，便于事后回溯；而自然语言入口让研究员可以直接提问题、而不是先花半天写 pipeline。下面的实验就是一个具体的例子——从提出问题到产出这份报告，全程没有人介入调度。

---

## 2. 两个超参数分别卡在 GRPO 循环的哪里

本实验用的算法是 **GRPO**（Group Relative Policy Optimization）——近两年数学推理类任务上最常用的 RL 变体。它不训练独立的 critic，而是对同一 prompt 采样一组（group）回答，用组内相对优势代替价值函数。虽然名字里没有 "PPO"，但它继承了 PPO 的内循环结构——也就正好保留了本文关心的两个超参数：`ppo_epochs` 和 `mini_batch_num`。

### 2.1 一次 GRPO 迭代长什么样

下图把一次完整迭代拆成了四步，其中我们关心的两个超参数用高亮标出：

![GRPO 训练循环示意：Rollout → Group-Relative Advantage → Inner Loop (ppo_epochs) → Mini-Batch Updates (mini_batch_num)](https://serve.gptacademic.cn/publish/auto/ppoepochminibatch/grpo_loop.jpg)

流程并不复杂：

1. **Rollout**：用当前策略 πθ 对每个 prompt 采样一组 G 个候选回答。
2. **Group-Relative Advantage**：给这组回答打分，用"减去组内均值"得到每个回答的优势 A_i——这是 GRPO 相对于 PPO 最显著的简化。
3. **Inner Loop（`ppo_epochs`）**：把这批 rollout 反复用 K 次，即同一批数据做 K 轮完整的梯度更新。
4. **Mini-Batch Updates（`mini_batch_num`）**：每一轮内部，把大 batch 切成 M 份子批，累加梯度后再更新策略。

两个超参数的语义可以总结为：

| 超参数 | 在循环里的位置 | 直观含义 | 默认 |
|---|---|---|---:|
| `ppo_epochs` | 内循环次数 K | 同一批 rollout 被复用几遍 | 1 |
| `mini_batch_num` | 子批数量 M | 每遍内部走几次优化器步 | 1 |

它们乘起来就决定了 **"一批 rollout 能换来多少次参数更新"**——这正是 GRPO 样本效率的总阀门。

### 2.2 已有的调参经验

社区在 PPO 时代对这两个参数已经有不少共识，大部分也直接适用于 GRPO：

- 提 `ppo_epochs` 能摊薄昂贵的 rollout 成本，但 epoch 太多、新策略偏离 rollout 策略过远，重要性采样就不再成立，训练容易不稳——所以 LLM 场景的主流建议是从 1 起步，按需升到 3–5。
- OpenAI 在 *Batch size-invariance for policy optimization* (Hilton, 2021) 里系统研究过有效批量的影响，结论是只要学习率等超参同步调整，PPO 在不同批量下都能保持性能——意味着 `mini_batch_num` 的选择有不小的可调空间。
- 2025 年的 LLM-RL 工作（clip-higher、token-level PG loss、overlong reward shaping 等）几乎都隐式地依赖 epoch/batch 的配置，反向佐证这两个参数是现代 LLM-RL 的基石。

但这些经验几乎都来自经典 RL 或全参 RLHF 的设定。到了 **7B 模型 + LoRA + 数学推理** 这种具体场景下，它们谁先撞墙、能撞多远，就是下面要用四组实验亲自验证的事。

---

## 3. 四组实验，六张诊断图

### 3.1 实验配置

4 组实验并行跑在 8 张 GPU 上（每组 2 卡），总时长 ≈21.7 小时。

| # | 配置名 | `ppo_epochs` | `mini_batch_num` | GPUs |
|---|---|---:|---:|:-:|
| 1 | baseline | 1 | 1 | 0,1 |
| 2 | minibatch_2 | 1 | 2 | 2,3 |
| 3 | minibatch_4 | 1 | 4 | 4,5 |
| 4 | ppoepochs_2 | 2 | 1 | 6,7 |

其他公共设置：Qwen2.5-7B-Instruct + LoRA rank=16；Countdown 基准；验证集 1024 题 × 4 采样。

### 3.2 一级结果：训练曲线

把 21.7 小时的日志直接铺开，肉眼就能看出四条曲线的走势差异。

按训练时间对齐的曲线：

![按时间对齐的训练进度](https://serve.gptacademic.cn/publish/auto/ppoepochminibatch/progress_charts_by_time.png)

按训练步对齐的曲线：

![按步数对齐的训练进度](https://serve.gptacademic.cn/publish/auto/ppoepochminibatch/progress_charts.png)

最基础的观察：所有实验都经过 "缓慢热启动 → 快速上升 → 平台" 的三阶段，但 **热启动时长相差悬殊**——baseline 到 8 h 才开始起飞，而 minibatch_4 在 3–4 h 就已经爬到一半。v1 注意到了这个现象却没解释。这一现象从哪里来？是 mb_4 的每一步更快，还是每一步"走得更远"？下面六张图顺着这条线索一张一张往下追。

---

### 3.3 是每步更快吗？

第一个最容易冒出来的猜测是："mb_4 大概是每步跑得快一点。"先把它证伪。

![Fig.1 per-step cost & cumulative time](https://serve.gptacademic.cn/publish/auto/ppoepochminibatch/deep_1_stepcost.png)

**观察**：四组实验的 `timing_s/step` 分布几乎重合（中位数 ~180 s/step，都有少量 1000s+ 长尾），累计耗时曲线在 step 轴上也几乎平行。

**结论**：性能加速 **不** 来自更快的每步计算——mb=4 / ppo=2 既没把每步变慢，也没变快。那加速从哪来？答案是 **每个 rollout 所能撬动的策略更新量**。

mb=4 意味着在同一批 rollout 上走 4 次 optimizer step（梯度累积粒度更细），ppo=2 意味着在同一批上走 2 轮完整 epoch。两者都使 "每个 rollout → 策略位移" 的杠杆变大，而 baseline 的这个杠杆是 1。

### 3.4 换算成"达到同一性能要多久"

既然不是每步更快，那把"每步一样慢"换算成"到达同一性能要等多久"，差距到底被放大了几倍？

![Fig.2 time-to-threshold](https://serve.gptacademic.cn/publish/auto/ppoepochminibatch/deep_2_time_to_threshold.png)

**观察（核心结果）**：达到各级 pass@4 阈值所需的训练小时：

| 阈值 | baseline | mb_2 | **mb_4** | ppo_2 |
|---|---:|---:|---:|---:|
| ≥0.10 | 7.9 h | 5.2 h | **3.8 h** | 4.7 h |
| ≥0.20 | 8.5 h | 5.2 h | **3.8 h** | 4.7 h |
| ≥0.30 | 10.5 h | 5.9 h | **4.5 h** | 5.4 h |
| ≥0.35 | 11.8 h | 7.3 h | **5.2 h** | 6.8 h |

- mb_4 相对 baseline 在 pass@4≥0.20 这一关键门槛上 **加速 2.2×**，在 ≥0.35 上加速 **2.3×**。
- ppo_2 紧随其后，加速 1.7–1.8×。
- mb_2 居中。

### 3.5 这个加速集中在训练的哪一段

整段训练上都加速了 2×，还是集中在某一段？这个问题对工程实践很关键——如果你只能跑半程，baseline 亏在哪？

![Fig.3 learning-speed heatmap](https://serve.gptacademic.cn/publish/auto/ppoepochminibatch/deep_3_speed_heatmap.png)

**观察**：在 4 小时这个快照点，

- baseline：0.017（几乎没学到东西）
- mb_4：0.211（**12× 于 baseline**）
- mb_2：0.035
- ppo_2：0.043

这说明 **热启动阶段差异最大**，等所有实验进入平台（≥10h）后差距收敛到 <0.02。也就是说：**"机会成本"集中在前 6 小时**。

### 3.6 打开黑盒：baseline 为什么动不起来

到这里我们知道了"baseline 前几小时几乎没动"，但只看验证曲线说不清为什么没动。把训练时的几个内部指标叠在一起看，机理立刻就清楚了。

![Fig.4 stability: grad_norm / entropy / ppo_kl / clipfrac](https://serve.gptacademic.cn/publish/auto/ppoepochminibatch/deep_4_stability.png)

这张图揭示了最关键的 **机理**：

- **Gradient norm**：baseline 的 grad_norm 长期停在 ~0.1，而 mb_4 / ppo_2 逐步上升至 0.3–0.4。也就是说 baseline 的每个优化器步所见到的有效梯度信号都很小。
- **Policy entropy**：baseline 的熵始终维持在 ~0.45（策略几乎没有偏好化），mb_4 稳定地从 0.45 下降到 ~0.27（策略逐渐变得确定性、"学出了偏好"）。这是 baseline 学得慢的直接证据：它还没有完成"策略塑形"。
- **PPO KL**：四组都非常接近 0（< 3e-4），说明没有任何一组越过 clip 边界导致不稳定 —— **把 `ppo_epochs` 提到 2 并没有引入 PPO 社区担忧的"跨度过大"风险**。
- **Clip fraction**：mb_2 / mb_4 的 clip 比例随训练缓慢上升到 ~0.2%–0.25%，仍然极低。

**机理总结**：`mb_num` / `ppo_epochs` 的作用不是"让梯度更大"，而是 **让同一批 rollout 被"摊开"到更多个优化器步** —— 每步的梯度仍然规范，但累计起来的策略位移显著增大。baseline 每 rollout 只能走一次小步，因此前期学习缓慢。

### 3.7 动起来之后，策略被塑造成什么样

内部指标解释了"为什么 baseline 动不起来"，但"动起来的那几组"最终把模型训练成了什么样？对 Countdown 这种数学推理任务，最直接的外显指标是回答长度——模型愿不愿意"多想几步"。

![Fig.5 response length & training reward](https://serve.gptacademic.cn/publish/auto/ppoepochminibatch/deep_5_behavior.png)

**观察**：

- **回答长度**：mb_4 的平均回答长度从 ~430 tokens 一路拉长到 **~550 tokens**，其它三组都停留在 ~430–470。回答变长说明模型学会了"多想几步再给答案"，这是 Countdown 任务上 CoT 能力被强化的外显特征。
- **训练时奖励**：mb_4 / ppo_2 最早在 step ~70 进入高奖励区，baseline 要等到 step ~140。

这张图把 "更多更新次数 → 更强的 CoT 倾向 → 更高 pass@4" 这一因果链补上了：**策略有机会走得更远 → 学到更长、更完整的推理链条 → 任务成功率提升**。

### 3.8 跑满 21.7 小时，最终峰值谁赢

中间某个时间点上看起来领先的未必就是最终冠军——RL 曲线还在波动，得等平台期稳下来再盖棺定论。跑到 21.7 h 的最终数据如下。

![Fig.6 efficiency frontier](https://serve.gptacademic.cn/publish/auto/ppoepochminibatch/deep_6_efficiency.png)

| 实验 | best pass@4 | 达峰时长 |
|---|---:|---:|
| **minibatch_4** | **0.383** | 21.7 h |
| ppoepochs_2 | 0.382 | 19.2 h |
| minibatch_2 | 0.377 | 15.3 h |
| baseline | 0.376 | 18.3 h |

**解读**：
- **最终峰值**：mb_4 ≈ ppo_2 > mb_2 > baseline；mb_4 与 ppo_2 只差 0.001，在训练噪声范围内，可以视为并列第一。
- **时间-性能 Pareto 最优**：minibatch_2——只用 15.3 h 就拿到 0.377，再往后几乎不再涨。如果预算有限、宁肯牺牲 1 个百分点换 30% 的时间，这是最划算的一档。

---

## 4. 把故事拼起来：结论与配置建议

把六张图串起来看，故事其实很干净：加速既不来自更快的每步，也不来自更大的梯度，而是同一批 rollout 被允许多走几步；这几步撬开了 baseline 卡住的热启动，策略才有机会真正塑形，也才能学会更长的推理链条。

下面把这条线索拆成可以直接带走的几条结论：

1. **"更多 rollout 内更新"是加速的根因**。无论通过 `mini_batch_num↑` 还是 `ppo_epochs↑`，本质都是把同一批 rollout 的梯度杠杆放大，**而不是把单步计算加速**（图 1）。
2. **mini_batch_num=4 是最佳综合配置**：最终峰值 pass@4 最高（0.383），达到 pass@4≥0.35 仅需 5.2 h（图 2、图 6）。
3. **ppo_epochs=2 与 mb_4 几乎同等有效**（0.382 vs 0.383），且没有观察到 PPO 社区担忧的 KL 爆炸 / 熵崩溃（图 4）。这对后续研究很重要：在 LoRA + 小 clip 配置下，ppo_epochs=2 是安全的。
4. **baseline 最严重的问题是"热启动失灵"**：前 4 h 几乎无学习信号（pass@4=0.017），而 mb_4 已经 0.211。**计算资源的"机会成本"集中在前 6 小时**（图 3）。
5. **策略行为层面**：mb_4 同时带来 **更长回答（~550 tokens）** 和 **更低熵（~0.27）**，说明策略走得更远、学到了更具体的解题偏好（图 4、图 5）。

**推荐配置**：

| 目标 | 推荐 |
|---|---|
| 最高最终峰值 | `mb_num=4, ppo_epochs=1` 或 `ppo_epochs=2, mb_num=1` |
| 最快达到可用性能 | `mb_num=4, ppo_epochs=1` |
| 显存紧张 | `mb_num=1~2, ppo_epochs=2` |
| 时间-性能 Pareto | `mb_num=2` |

## 欢迎关注 Alpha Auto Research 和 AgentJet 项目

Alpha Auto Research: https://github.com/binary-husky/Alpha-RL-Research.git

AgentJet: https://github.com/modelscope/AgentJet.git

![rednote](https://serve.gptacademic.cn/publish/auto/ppoepochminibatch/rednote.png)