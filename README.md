# Alpha Auto Research

[中文版 (Chinese Version)](README.ZH.md)

> 2025-2026, "AI doing research autonomously" went from an academic dream to engineering reality. [AI Scientist](https://sakana.ai/ai-scientist/) was published in [Nature](https://www.nature.com/articles/s41586-026-10265-5), [AI-Researcher](https://github.com/HKUDS/AI-Researcher) earned NeurIPS 2025 Spotlight, and [OpenAI declared fully-automated research its North Star](https://www.technologyreview.com/2026/03/20/1134438/openai-is-throwing-everything-into-building-a-fully-automated-researcher/). But most of these systems focus on **writing papers**. We focus on **running experiments**.

Alpha Auto Research is an automated RL research system built on a **Leader-Worker architecture**. A **leader agent** reads a natural-language research topic, designs multi-stage experiment plans, generates structured experiment blueprints, dispatches them to GPU clusters, monitors progress, collects results, and writes analysis reports — while **worker agents** execute individual training runs on distributed compute backends. Submit a research topic before bed, wake up to a finished report.

The system is **fully open-source**, powered by [OpenCode](https://github.com/anthropics/opencode) AI agents and [AgentJet](https://github.com/modelscope/AgentJet) (an open-source RL training framework by ModelScope). As the [oh-my-opencode](https://github.com/nicepkg/oh-my-opencode) author put it: *"Claude Code's a nice prison, but it's still a prison."* — we need full control over conversation history, breakpoint recovery, and agent behavior, which only open-source tooling can provide. It supports Alibaba Cloud PAI DLC (灵骏) and SSH-based clusters as compute backends. **No expensive frontier models required** — the entire system runs on affordable LLM APIs like [MiniMax M2.7](https://www.minimax.io/) or GLM coding plans. Got unused coding plan quota sitting idle overnight? Let Auto Research squeeze every last drop of value out of it.

## Key Features

- **Long-horizon experiment loops**: Single RL training runs can take hours or days. The system autonomously handles the full cycle — hypothesize, design, dispatch, wait, analyze, iterate — all unattended
- **Maximize cluster utilization**: Multi-GPU parallel dispatch across SSH servers or Alibaba Cloud PAI DLC (灵骏). Squeeze every GPU-hour out of your cluster instead of running experiments one by one
- **Fully open-source, no vendor lock-in**: Built on [OpenCode](https://github.com/anthropics/opencode) — full control over conversation history, breakpoint recovery, and agent behavior. No dependence on closed-source tools that break when you need deep customization
- **Cheap enough to run freely**: Powered by affordable LLM APIs (MiniMax M2.7, GLM coding plans, or any OpenAI-compatible model). When API cost is effectively zero, "should I run one more experiment?" is never a question
- **Fully autonomous or human-in-the-loop — your choice**: The Blueprint mechanism lets the leader agent draft structured experiment plans while you review, tweak parameters, or take over any sub-task at any stage. Every step is transparent — no wasted compute from days of training in the wrong direction. Or just let it run end-to-end with `--no-human-in-the-loop`
- **Leader-Worker architecture**: Leader designs experiments and analyzes results; Workers execute training on GPU clusters
- **Blueprint-based coordination**: Structured markdown "contracts" between Leader and Worker ensure reproducibility
- **Robust unattended operation**: Auto-recovery from API timeouts, GPU contention, network issues, and agent crashes — runs for days without manual restarts

## Real-World Results: 6 Research Topics Completed Autonomously

The system has been validated on **6 independent research topics**, all completed autonomously by AI agents — from topic submission to final report, with zero human intervention. Here are the highlights:

| # | Research Topic | Key Finding | Model | Duration |
|---|---|---|---|---|
| 1 | AppWorld `max_steps` hyperparameter search | `max_steps=15` is optimal: same accuracy as 25, but **40% faster** (efficiency 1.87x) | Qwen2.5-14B | ~8h overnight |
| 2 | LoRA Rank & Alpha for math reasoning | `rank=32, alpha=64` is the sweet spot: rank 8→32 gives +15.1%, but 32→128 only +1.3% (diminishing returns) | Qwen2.5-7B | ~6h |
| 3 | Qwen3 multi-scale comparison (GSM8K) | **14B beats 32B** (94.67% vs 92.87%) — bigger is not always better; 8B shows the highest learning efficiency (+34.93%) | Qwen3-8B/14B/32B | ~12h |
| 4 | Countdown math reasoning | 8B achieves a **3x performance leap** (26.78% → 83.64%), nearly closing the gap with 14B | Qwen3-8B/14B/32B | ~12h |
| 5 | Learn2Ask medical dialogue | 14B wins again (82.14%); agent auto-diagnosed an API key failure and generated a detailed error report | Qwen3-8B/14B | ~8h |
| 6 | Training anomaly detection mechanisms | Studied `compute_madness_checklist`, `agent_madness_termination`, and `agent_madness_reward` effects on training stability | Qwen2.5-7B | ~3h |

**What the AI research agent did well:**
- Designed efficient experiment plans (e.g., testing 3 strategic values instead of brute-force grid search)
- Pre-planned decision trees before running experiments ("if result is A, do X; if B, do Y")
- Knew when to stop — didn't waste compute on unnecessary follow-up stages when evidence was already sufficient
- Honestly reported limitations (incomplete training, lack of statistical significance, etc.)

> For a detailed walkthrough with figures and analysis, see the full blog post: [`subject_ajet_appworld_step_study/auto_research_blog.md`](subject_ajet_appworld_step_study/auto_research_blog.md)

## Quick Start

### 1. Install

```bash
pip install -e .
```

### 2. Configure

```bash
cp research_config.example.jsonc research_config.jsonc
# Edit research_config.jsonc with your credentials and backend settings
```

### 3. Clone training codebase

```bash
git clone https://github.com/modelscope/AgentJet.git codebase/agentjet
```

### 4. Run

```bash
# Plan a new research topic (using SSH backend)
alpha-new-plan --runner=ssh --topic="research_topic/my_topic.md"

# Review the plan, then begin experiments
alpha-resume --runner=ssh \
    --topic="research_topic/my_topic.md" \
    -r "permission granted, begin research"
```

## CLI Reference

After `pip install -e .`, the following commands are available:

### Convenience Commands

| Command | Description |
|---|---|
| `alpha-new-plan` | Plan a research topic from scratch |
| `alpha-resume-plan` | Resume and refine an existing plan |
| `alpha-resume` | Start or resume experiment execution |
| `alpha-auto` | Fully autonomous research, no human review |

All accept `--topic=<path>` and `--runner=<ssh|pai>` (defaults to ssh). The `-r <text>` flag is available on all except `alpha-auto`.

### Core Commands

| Command | Description |
|---|---|
| `alpha-rl-research leader [OPTIONS]` | Full leader role with all flags |
| `alpha-rl-research worker [OPTIONS]` | Worker role (runs on compute nodes) |
| `alpha-run-blueprint --blueprint=<path>` | Launch a single experiment blueprint |
| `alpha-scan-jobs` | List running and recent jobs |
| `alpha-stop-jobs --stop-job-id=<id>` | Stop a running job (`--delete` to remove) |

### Leader Options

```
--topic PATH               Research topic file or inline text
--blueprint PATH           Path to a research skill .md file
--resume                   Resume the latest session
-r, --resume-instruction   Instruction for the resumed session
--only-run-planning        Generate plan only, don't execute experiments
--no-human-in-the-loop     Fully autonomous role, no human review steps
                           (leader only; conflicts with --only-run-planning,
                           --resume, and -r)
```

## Architecture

### Leader Agent (the "brain")

The Leader Agent receives a natural-language research topic and autonomously:

1. **Parses the topic** — identifies variables to compare and controls to hold fixed
2. **Designs multi-stage experiments** — coarse-to-fine progressive search with pre-planned decision branches ("if result is A, do X; if B, do Y")
3. **Generates experiment blueprints** — structured markdown documents containing everything a Worker needs
4. **Dispatches to GPU clusters** — runs multiple experiments in parallel via PAI DLC or SSH
5. **Monitors progress** — polls experiment status at regular intervals
6. **Analyzes results** — reads metrics, generates comparison charts, writes conclusions
7. **Iterates or terminates** — follows the decision tree to decide if another round is needed or the evidence is sufficient

### Worker Agent (the "hands")

Each Worker Agent runs on an independent GPU node:

- Sets up the environment per the blueprint
- Launches training and monitors with adaptive polling intervals
- Auto-recovers from GPU contention, process crashes, and resource conflicts
- Reports results (success or failure) so the Leader never waits indefinitely

### Blueprint: the contract between Leader and Worker

Blueprints are structured markdown files with **7 standard sections** that serve as the communication protocol:

| Section | Purpose |
|---|---|
| `[exp_purpose]` | Hypothesis being tested, and how this experiment differs from others |
| `[exp_codebase_dir]` | Absolute path to experiment code |
| `[exp_venv_exe]` | Path to Python executable / virtual environment |
| `[exp_yaml_path]` | Path to training config YAML |
| `[exp_launch_command]` | Command to start training |
| `[exp_result_dir]` | Output directory for results |
| `[exp_max_time]` | Maximum allowed runtime |

An optional **notes section** can include environment setup steps, config references, and **pre-experiment hypotheses** — so the analysis can judge whether results matched expectations rather than rationalizing after the fact.

### Workflow

```
 Research Topic (.md)
        |
        v
  +-- LEADER AGENT --+
  |  1. Read topic    |
  |  2. Design plan   |  <--- User reviews & confirms (optional)
  |  3. Generate      |
  |     blueprints    |
  +--------+----------+
           |
     dispatch via runner
     (PAI DLC or SSH)
           |
    +------+------+
    |      |      |
    v      v      v
 WORKER  WORKER  WORKER    Each worker:
  exp_1   exp_2   exp_3    - Sets up environment
    |      |      |        - Runs training
    v      v      v        - Monitors & fixes errors
 results results results   - Writes experiment_log.md
    |      |      |
    +------+------+
           |
           v
  +-- LEADER AGENT --+
  |  Review results   |
  |  Update progress  |  ---> Iterate or finalize
  |  Generate report  |
  +-------------------+
```

### Robustness: run for days without human intervention

- **Auto-resume on crash**: A guardian loop wraps each agent. When an agent is interrupted (API timeout, network issue, context overflow), it automatically resumes from the breakpoint with full conversation history
- **Tolerates LLM service outages**: If the LLM API is rate-limited or temporarily unavailable, the system waits patiently and resumes seamlessly once service recovers — even after hours of downtime
- **Self-healing Workers**: GPU contention? Reallocate. Training process died? Restart. Zombie processes? Clean up automatically
- **Permission-aware**: Detects permission denials and suggests alternative approaches; supports "full trust" mode for fully unattended operation

## Runner Backends

The `--runner` CLI argument selects the compute backend (`ssh` or `pai`). Both backends expose the same interface to the Leader Agent — submit blueprint, wait for results, collect data — so **switching backends requires changing only one flag**, with zero impact on the research workflow.

> **Tip**: Debug and iterate on a local SSH server first, then switch to `--runner=pai` to scale the same research topic to cloud GPUs seamlessly.

### SSH (`--runner ssh`)

Launches workers on SSH-accessible machines via tmux sessions. Ideal for teams with their own GPU servers — zero additional cost. Configure hosts in the `ssh` section:

```jsonc
"ssh": {
    "hosts": [
        { "host": "192.168.1.10", "port": 22, "user": "root" }
    ]
}
```

Supports localhost with automatic SSH key setup.

### Alibaba Cloud PAI DLC (`--runner pai`)

Launches workers as Alibaba Cloud PAI DLC (灵骏) jobs by cloning a template job. Ideal for elastic scaling — run 6+ experiments in parallel without worrying about local hardware limits. Configure credentials and job defaults in the `alibaba_cloud` and `pai_job_template` sections.

## Configuration

See [`research_config.example.jsonc`](research_config.example.jsonc) for all options. Key sections:

| Section | Purpose |
|---|---|
| `runner` | Backend selection: `"pai"` or `"ssh"` |
| `paths` | Home directory and project root |
| `alibaba_cloud` | PAI DLC credentials and region |
| `api_keys` | API keys for training services |
| `pai_job_template` | Job cloning template and defaults |
| `remote_monitor` | Optional kite-client remote monitoring |
| `ssh` | SSH host list for the SSH runner |

## Project Structure

```
alpha_auto_research/
  config.py                  Config loader (research_config.jsonc)
  opencode_runner.py         Leader/worker agent orchestrator
  cli.py                     Convenience CLI entry points
  blueprint_runner/
    base.py                  Abstract ExperimentSubagent interface
    pai_runner.py            Alibaba PAI DLC backend
    ssh_runner.py            SSH/tmux backend
    blueprint_runner.py      Single blueprint executor
    scan_jobs.py             Job listing
    stop_jobs.py             Job management
  pai/
    client.py                PAI DLC API client
  utils/
    pty.py                   Pseudo-terminal runner
    smart_daemon.py          Detached process management
  skills/
    leader_experiment/SKILL.md       Leader agent instructions
    worker_experiment/SKILL.md       Worker agent instructions
```

## Usage Examples

### Basic: plan, review, execute

```bash
# Step 1: Generate a research plan (Leader reads the topic, designs experiments)
alpha-new-plan \
    --runner=ssh \
    --topic="research_topic/example_01_content_madness_detect.md"

# Step 2: Review the generated plan, then confirm execution
alpha-resume \
    --runner=ssh \
    --topic="research_topic/example_01_content_madness_detect.md" \
    -r "permission granted, begin research"
```

### Iterative planning: refine before executing

```bash
# Generate initial plan
alpha-new-plan \
    --runner=ssh \
    --topic="research_topic/example_02_kl_abl.md"

# Refine the plan with specific instructions
alpha-resume-plan \
    --runner=ssh \
    --topic="research_topic/example_02_kl_abl.md" \
    -r "max_env_worker: 64 -> 128, max_num_seqs->1024, revise your plan accordingly"

# Confirm execution
alpha-resume \
    --runner=ssh \
    --topic="research_topic/example_02_kl_abl.md" \
    -r "permission granted, begin research"
```

### Cloud execution with PAI DLC

```bash
alpha-new-plan \
    --runner=pai \
    --topic="research_topic/example_03_appworld.md"

alpha-resume-plan \
    --runner=pai \
    --topic="research_topic/example_03_appworld.md" \
    -r "polish your plan"

alpha-resume \
    --runner=pai \
    --topic="research_topic/example_03_appworld.md" \
    -r "permission granted, begin research"
```

### Resume and finalize reports

```bash
# Resume a broken experiment with corrective instructions
alpha-new-plan \
    --runner=ssh \
    --topic="research_topic/example_02_kl_abl.md" \
    -r "Look at what you have done! Yaml is all wrong, refer to agentjet/ajet/default_config/ajet_default.yaml"

# Tell the leader to write the final report after experiments finish
alpha-resume \
    --runner=pai \
    --topic="research_topic/example_03_appworld.md" \
    -r "the experiment is finished, write report"

# Customize report style
alpha-resume-plan \
    --runner=pai \
    --topic="research_topic/example_03_appworld.md" \
    -r "use seaborn! show as many details as possible, write report in markdown format with figures included."
```

### Fully autonomous (no human review)

```bash
alpha-auto \
    --runner=ssh \
    --topic="research_topic/my_topic.md"
```

### Job management

```bash
# List all running and recent jobs
alpha-scan-jobs --runner=ssh

# Stop a specific job
alpha-stop-jobs --runner=ssh --stop-job-id=<job_id>

# Stop and delete a job
alpha-stop-jobs --runner=ssh --stop-job-id=<job_id> --delete
```

## Writing a Research Topic

A research topic is a markdown file describing what you want to investigate. Example:

```markdown
## Research Task

Investigate the effect of `max_steps` on the balance between training effectiveness and speed.
Use `Qwen2.5-14B-Instruct`, 8 GPUs per experiment, max 24 hours per experiment.

## Capacity

Max parallel experiment blueprints: 3
```

Key elements to include:
- **Research question**: What variable(s) to investigate and what tradeoffs to explore
- **Model and resources**: Which model to use, GPU count per experiment
- **Constraints**: Max parallel experiments, time limits per experiment
- **Codebase and config references**: Point to relevant code paths and YAML configs

See `research_topic/` for complete examples.

## Tech Stack

| Component | Role |
|---|---|
| [OpenCode](https://github.com/anthropics/opencode) | Open-source AI agent runtime — reads files, executes commands, manages processes. Supports conversation persistence and resume-from-breakpoint |
| [AgentJet](https://github.com/modelscope/AgentJet) | Open-source RL training framework (Apache 2.0) by ModelScope. Multi-GPU distributed training, LoRA, diverse tasks (math, AppWorld, medical dialogue, etc.) |
| LLM API (affordable) | Powers the agents' reasoning. Uses exclusively low-cost models (e.g., MiniMax M2.7) via OpenAI-compatible APIs — no expensive frontier models needed |
