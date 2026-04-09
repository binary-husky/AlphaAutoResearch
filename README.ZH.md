# Alpha Auto Research

[English Version](README.md)

> 让 AI Agent 自主完成完整的研究闭环：**提出假设 -> 设计实验 -> 调度训练 -> 分析结果 -> 撰写报告**。睡前提交研究课题，醒来查看报告。

Alpha Auto Research 是一套基于 **Leader-Worker 架构**的全自动强化学习科研系统。**Leader Agent** 读取自然语言描述的研究课题，设计多阶段实验方案，生成结构化实验蓝图（Blueprint），将其调度到 GPU 集群执行，监控进度，收集结果并撰写分析报告——而 **Worker Agent** 在分布式计算后端上执行各个训练任务。

系统基于 [OpenCode](https://github.com/anthropics/opencode) AI Agent 框架和 [AgentJet](https://github.com/modelscope/AgentJet)（ModelScope 开源的强化学习训练框架）构建，支持阿里云 PAI DLC 和 SSH 集群两种计算后端。**无需昂贵的顶级大模型**——整个系统仅使用 [MiniMax M2.7](https://www.minimax.io/) 等廉价模型驱动（Plus 极速版仅需 ~98 元/月，~100 TPS 推理速度，仅为 Claude 5x 价格的 1/7——不是广告哈，M2.7 确实很不错）。白天 vibe coding，晚上自动科研，两不误。

## 核心特性

- **端到端自主研究**：从课题到结论，全程零人工干预
- **Leader-Worker 架构**：Leader 负责设计实验和分析结果；Worker 在 GPU 集群上执行训练
- **蓝图协议**：Leader 和 Worker 之间通过结构化 Markdown "合约"通信，确保实验可复现
- **多后端支持**：阿里云 PAI DLC 或 SSH 集群，通过 `--runner` 参数一键切换
- **鲁棒的无人值守运行**：自动从 API 超时、GPU 争抢、网络波动和 Agent 崩溃中恢复——可连续运行数天无需手动重启
- **低成本**：仅使用廉价的大模型 API（如 MiniMax M2.7，Plus 极速版 ~98 元/月）——无需昂贵的顶级模型
- **人机协同或全自动**：可在执行前审查和修改方案，也可让系统全程自主运行

## 实战成果：6 个研究课题全自动完成

系统已在 **6 个独立研究课题**上验证，全部由 AI Agent 自主完成——从提交课题到输出最终报告，全程零人工干预。以下是核心发现：

| # | 研究课题 | 核心发现 | 模型 | 耗时 |
|---|---|---|---|---|
| 1 | AppWorld `max_steps` 超参搜索 | `max_steps=15` 为最优：与 25 效果持平，但**快 40%**（效率 1.87 倍） | Qwen2.5-14B | ~8h（一夜） |
| 2 | LoRA Rank 与 Alpha 对数学推理的影响 | `rank=32, alpha=64` 是最优性价比：rank 8→32 提升 +15.1%，但 32→128 仅 +1.3%（收益递减） | Qwen2.5-7B | ~6h |
| 3 | Qwen3 多模型规模对比（GSM8K） | **14B 打败了 32B**（94.67% vs 92.87%）——更大不等于更好；8B 的学习效率最高（+34.93%） | Qwen3-8B/14B/32B | ~12h |
| 4 | Countdown 数学推理 | 8B 实现 **3 倍性能飞跃**（26.78% → 83.64%），几乎追平 14B | Qwen3-8B/14B/32B | ~12h |
| 5 | Learn2Ask 医疗对话 | 14B 再次胜出（82.14%）；Agent 自动诊断出 API 密钥失效并生成详细故障报告 | Qwen3-8B/14B | ~8h |
| 6 | 训练异常检测机制研究 | 研究了 `compute_madness_checklist`、`agent_madness_termination`、`agent_madness_reward` 对训练稳定性的影响 | Qwen2.5-7B | ~3h |

**AI 研究 Agent 做对了什么：**
- 设计了高效的实验方案（如选取 3 个策略性数值而非暴力网格搜索）
- 实验开始前就预先规划好决策树（"如果结果是 A 就做 X，如果是 B 就做 Y"）
- 知道何时停下——当证据已经充分时，不浪费算力做多余的后续阶段
- 诚实地报告了局限性（训练未完成、缺乏统计显著性验证等）

> 完整的实验过程、图表和分析详见博客全文：[`subject_ajet_appworld_step_study/auto_research_blog.md`](subject_ajet_appworld_step_study/auto_research_blog.md)

## 快速开始

### 1. 安装

```bash
pip install -e .
```

### 2. 配置

```bash
cp research_config.example.jsonc research_config.jsonc
# 编辑 research_config.jsonc，填写你的凭据和后端设置
```

### 3. 克隆训练代码库

```bash
git clone https://github.com/modelscope/AgentJet.git codebase/agentjet
```

### 4. 运行

```bash
# 规划一个新的研究课题（使用 SSH 后端）
alpha-rl-new-planning --runner=ssh --research-topic="research_topic/my_topic.md"

# 审查方案后，确认开始实验
alpha-rl-begin-experiments --runner=ssh \
    --research-topic="research_topic/my_topic.md" \
    --resume-instruction="permission granted, begin research"
```

## CLI 命令参考

执行 `pip install -e .` 后，以下命令可用：

### 便捷命令

| 命令 | 说明 |
|---|---|
| `alpha-rl-new-planning` | 从零开始规划研究课题 |
| `alpha-rl-resume-planning` | 恢复并修改已有方案 |
| `alpha-rl-begin-experiments` | 规划完成后开始执行实验 |
| `alpha-rl-resume-experiment` | 恢复中断的实验执行 |
| `alpha-rl-new-research-no-human` | 全自动研究，无需人工审查 |

所有命令均接受 `--research-topic=<路径>` 和 `--runner=<ssh|pai>`（必填）。除 `alpha-rl-new-research-no-human` 外，均支持 `--resume-instruction=<文本>` 参数。

### 核心命令

| 命令 | 说明 |
|---|---|
| `alpha-rl-research leader [选项]` | 完整的 Leader 角色，支持全部参数 |
| `alpha-rl-research worker [选项]` | Worker 角色（运行在计算节点上） |
| `alpha-run-blueprint --blueprint=<路径>` | 执行单个实验蓝图 |
| `alpha-scan-jobs` | 列出正在运行和最近的任务 |
| `alpha-stop-jobs --stop-job-id=<id>` | 停止运行中的任务（`--delete` 可同时删除） |

### Leader 参数

```
--research-topic PATH      研究课题文件路径或内联文本
--blueprint PATH           研究技能 .md 文件路径
--resume                   恢复最近的会话
--resume-instruction TEXT   恢复会话时的指令
--only-run-planning        仅生成方案，不执行实验
--skip-permissions         使用宽松的 Agent 配置（允许所有工具）
--no-human-in-the-loop     全自动模式，无人工审查步骤
                           （仅限 leader；与 --only-run-planning、
                           --resume 和 --resume-instruction 冲突）
```

## 系统架构

### Leader Agent（研究的"大脑"）

Leader Agent 接收自然语言描述的研究课题，自主完成以下工作：

1. **解析课题** — 识别需要比较的变量和需要控制的因素
2. **设计多阶段实验** — 粗筛到细筛的渐进式搜索策略，预先规划决策分支（"如果结果是 A 就做 X；如果是 B 就做 Y"）
3. **生成实验蓝图** — 包含 Worker 所需全部信息的结构化 Markdown 文档
4. **调度到 GPU 集群** — 通过 PAI DLC 或 SSH 并行运行多个实验
5. **轮询监控** — 定期检查实验状态
6. **分析结果** — 读取指标数据，生成对比图表，撰写结论
7. **迭代或终止** — 依据决策树判断是否需要新一轮实验，还是已有足够证据得出结论

### Worker Agent（实验的"双手"）

每个 Worker Agent 运行在独立的 GPU 节点上：

- 按照蓝图配置环境
- 启动训练并以自适应间隔监控进度
- 自动从 GPU 争抢、进程崩溃和资源冲突中恢复
- 汇报结果（无论成功或失败），确保 Leader 不会无限等待

### 蓝图（Blueprint）：Leader 和 Worker 之间的"合约"

蓝图是包含 **7 个标准章节**的结构化 Markdown 文件，作为 Leader 和 Worker 之间的通信协议：

| 章节 | 用途 |
|---|---|
| `[exp_purpose]` | 待验证的假设，以及本实验与其他实验的区别 |
| `[exp_codebase_dir]` | 实验代码的绝对路径 |
| `[exp_venv_exe]` | Python 可执行文件 / 虚拟环境路径 |
| `[exp_yaml_path]` | 训练配置 YAML 文件路径 |
| `[exp_launch_command]` | 启动训练的命令 |
| `[exp_result_dir]` | 结果输出目录 |
| `[exp_max_time]` | 最大允许运行时间 |

可选的**附加说明**区域可包含环境准备步骤、配置参考，以及**实验前的预期假设**——使后续分析能判断结果是否符合预期，而非事后强行解释。

### 工作流程

```
 研究课题 (.md)
        |
        v
  +-- LEADER AGENT --+
  |  1. 读取课题     |
  |  2. 设计方案     |  <--- 用户审查确认（可选）
  |  3. 生成蓝图     |
  +--------+----------+
           |
     通过 runner 调度
     (PAI DLC 或 SSH)
           |
    +------+------+
    |      |      |
    v      v      v
 WORKER  WORKER  WORKER    每个 Worker：
  实验1   实验2   实验3    - 配置环境
    |      |      |        - 运行训练
    v      v      v        - 监控并修复错误
  结果    结果    结果      - 记录 experiment_log.md
    |      |      |
    +------+------+
           |
           v
  +-- LEADER AGENT --+
  |  审查结果         |
  |  更新进度         |  ---> 迭代或输出最终报告
  |  生成报告         |
  +-------------------+
```

### 鲁棒性：连续运行数天无需人工干预

- **崩溃自动恢复**：每个 Agent 外层有一个守护循环。当 Agent 因任何原因中断（API 超时、网络波动、上下文溢出）时，自动从断点恢复，保留完整对话历史
- **容忍大模型服务中断**：如果 LLM API 被限流或暂时不可用，系统会耐心等待，服务恢复后无缝继续工作——即使中断数小时也不受影响
- **Worker 自愈**：GPU 争抢？重新分配。训练进程挂了？重启。僵尸进程？自动清理
- **权限感知**：检测到权限拒绝时自动建议替代方案；支持"全权委托"模式用于完全无人值守运行

## 计算后端

`--runner` 参数选择计算后端（`ssh` 或 `pai`）。两种后端对 Leader Agent 暴露完全相同的接口——提交蓝图、等待结果、收集数据——因此**切换后端只需改一个参数**，对整个研究流程零影响。

> **提示**：可以先在本地 SSH 服务器上调试跑通，再把同一个研究课题切换到 `--runner=pai` 无缝扩展到云端大规模运行。

### SSH（`--runner ssh`）

通过 tmux 会话在 SSH 可访问的机器上启动 Worker。适合有自有 GPU 服务器的团队，零额外成本。在 `ssh` 配置节中设置主机列表：

```jsonc
"ssh": {
    "hosts": [
        { "host": "192.168.1.10", "port": 22, "user": "root" }
    ]
}
```

支持 localhost，可自动配置 SSH 免密登录。

### 阿里云灵骏 PAI DLC（`--runner pai`）

通过克隆模板任务，将 Worker 作为阿里云 PAI DLC（灵骏）任务启动。适合需要弹性扩缩容的场景——同时跑 6 组以上实验也不必担心本地机器不够用。在 `alibaba_cloud` 和 `pai_job_template` 配置节中设置凭据和任务默认参数。

## 配置

所有配置项详见 [`research_config.example.jsonc`](research_config.example.jsonc)。关键配置节：

| 配置节 | 用途 |
|---|---|
| `runner` | 后端选择：`"pai"` 或 `"ssh"` |
| `paths` | 主目录和项目根路径 |
| `alibaba_cloud` | PAI DLC 凭据和区域 |
| `api_keys` | 训练服务所需的 API 密钥 |
| `pai_job_template` | 任务克隆模板和默认参数 |
| `remote_monitor` | 可选的 kite-client 远程监控 |
| `ssh` | SSH 后端的主机列表 |

## 项目结构

```
alpha_auto_research/
  config.py                  配置加载器（research_config.jsonc）
  opencode_runner.py         Leader/Worker Agent 编排器
  cli.py                     便捷 CLI 入口
  blueprint_runner/
    base.py                  ExperimentSubagent 抽象接口
    pai_runner.py            阿里云 PAI DLC 后端
    ssh_runner.py            SSH/tmux 后端
    blueprint_runner.py      单蓝图执行器
    scan_jobs.py             任务列表
    stop_jobs.py             任务管理
  pai/
    client.py                PAI DLC API 客户端
  utils/
    pty.py                   伪终端运行器
    smart_daemon.py          后台进程管理
  skills/
    leader_experiment.md       Leader Agent 指令
    leader_experiment.no_human.md  全自动 Leader（无人工审查）
    worker_experiment.md       Worker Agent 指令
```

## 使用示例

### 基本流程：规划、审查、执行

```bash
# 第一步：生成研究方案（Leader 读取课题，设计实验）
alpha-rl-new-planning \
    --runner=ssh \
    --research-topic="research_topic/example_01_content_madness_detect.md"

# 第二步：审查方案后，确认开始执行
alpha-rl-begin-experiments \
    --runner=ssh \
    --research-topic="research_topic/example_01_content_madness_detect.md" \
    --resume-instruction="permission granted, begin research"
```

### 迭代规划：执行前反复打磨方案

```bash
# 生成初始方案
alpha-rl-new-planning \
    --runner=ssh \
    --research-topic="research_topic/example_02_kl_abl.md"

# 用具体指令修改方案
alpha-rl-resume-planning \
    --runner=ssh \
    --research-topic="research_topic/example_02_kl_abl.md" \
    --resume-instruction="max_env_worker: 64 -> 128, max_num_seqs->1024, revise your plan accordingly"

# 确认执行
alpha-rl-begin-experiments \
    --runner=ssh \
    --research-topic="research_topic/example_02_kl_abl.md" \
    --resume-instruction="permission granted, begin research"
```

### 使用阿里云 PAI DLC 执行

```bash
alpha-rl-new-planning \
    --runner=pai \
    --research-topic="research_topic/example_03_appworld.md"

alpha-rl-resume-planning \
    --runner=pai \
    --research-topic="research_topic/example_03_appworld.md" \
    --resume-instruction="polish your plan"

alpha-rl-begin-experiments \
    --runner=pai \
    --research-topic="research_topic/example_03_appworld.md" \
    --resume-instruction="permission granted, begin research"
```

### 断点恢复与报告生成

```bash
# 以纠正性指令恢复中断的实验
alpha-rl-new-planning \
    --runner=ssh \
    --research-topic="research_topic/example_02_kl_abl.md" \
    --resume-instruction="Look at what you have done! Yaml is all wrong, refer to agentjet/ajet/default_config/ajet_default.yaml"

# 实验完成后，告诉 Leader 撰写最终报告
alpha-rl-resume-experiment \
    --runner=pai \
    --research-topic="research_topic/example_03_appworld.md" \
    --resume-instruction="the experiment is finished, write report"

# 自定义报告风格
alpha-rl-resume-planning \
    --runner=pai \
    --research-topic="research_topic/example_03_appworld.md" \
    --resume-instruction="use seaborn! show as many details as possible, write report in markdown format with figures included."
```

### 全自动模式（无人工审查）

```bash
alpha-rl-new-research-no-human \
    --runner=ssh \
    --research-topic="research_topic/my_topic.md"
```

### 任务管理

```bash
# 列出所有运行中和最近的任务
alpha-scan-jobs --runner=ssh

# 停止指定任务
alpha-stop-jobs --runner=ssh --stop-job-id=<job_id>

# 停止并删除任务
alpha-stop-jobs --runner=ssh --stop-job-id=<job_id> --delete
```

## 编写研究课题

研究课题就是一个 Markdown 文件，用自然语言描述你想研究的问题。示例：

```markdown
## 主任务描述

你的任务是研究使用多大的 `max_steps` 能达到效果和训练速度的平衡。
使用 `Qwen2.5-14B-Instruct`，每个实验 8 GPU，单实验最长 24 小时。

## 容量

最大并行实验蓝图是: 3
```

关键要素：
- **研究问题**：要研究什么变量，探索什么权衡
- **模型和资源**：使用哪个模型，每个实验多少 GPU
- **约束条件**：最大并行实验数，单实验时间限制
- **代码库和配置引用**：指向相关代码路径和 YAML 配置文件

更多示例请查看 `research_topic/` 目录。

## 技术栈

| 组件 | 角色 |
|---|---|
| [OpenCode](https://github.com/anthropics/opencode) | 开源 AI Agent 运行时——读写文件、执行命令、管理进程。支持对话持久化和断点恢复 |
| [AgentJet](https://github.com/modelscope/AgentJet) | ModelScope 开源的 RL 训练框架（Apache 2.0）。支持多 GPU 分布式训练、LoRA、多种任务（数学推理、AppWorld、医疗对话等） |
| 大模型 API（廉价） | 驱动 Agent 的推理能力。仅使用低成本模型（如 MiniMax M2.7），通过 OpenAI 兼容 API 接入——无需昂贵的顶级模型 |
