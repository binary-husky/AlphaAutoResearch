# rl_auto_research

Automated RL research system with a leader-worker architecture, powered by [OpenCode](https://github.com/anthropics/opencode) AI agents.

A **leader agent** designs research plans, dispatches experiments, reviews results, and iterates — while **worker agents** execute individual training runs on distributed compute backends. The system supports Alibaba Cloud PAI DLC and SSH-based clusters.

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
# Plan a new research topic
alpha-rl-new-planning --research-topic="research_topic/my_topic.md"

# Review the plan, then begin experiments
alpha-rl-begin-experiments \
    --research-topic="research_topic/my_topic.md" \
    --resume-instruction="permission granted, begin research"
```

## CLI Reference

After `pip install -e .`, the following commands are available:

### Convenience Commands

| Command | Description |
|---|---|
| `alpha-rl-new-planning` | Plan a research topic from scratch |
| `alpha-rl-resume-planning` | Resume and refine an existing plan |
| `alpha-rl-begin-experiments` | Start executing experiments after planning |
| `alpha-rl-resume-experiment` | Resume interrupted experiment execution |
| `alpha-rl-new-research-no-human` | Fully autonomous research, no human review |

All accept `--research-topic=<path>`. The `--resume-instruction=<text>` flag is available on all except `alpha-rl-new-research-no-human`.

### Core Commands

| Command | Description |
|---|---|
| `alpha-rl-research leader [OPTIONS]` | Full leader mode with all flags |
| `alpha-rl-research worker [OPTIONS]` | Worker mode (runs on compute nodes) |
| `alpha-run-blueprint --blueprint=<path>` | Launch a single experiment blueprint |
| `alpha-scan-jobs` | List running and recent jobs |
| `alpha-stop-jobs --stop-job-id=<id>` | Stop a running job (`--delete` to remove) |

### Leader Options

```
--research-topic PATH      Research topic file or inline text
--blueprint PATH           Path to a research skill .md file
--resume                   Resume the latest session
--resume-instruction TEXT  Instruction for the resumed session
--only-run-planning        Generate plan only, don't execute experiments
--skip-permissions         Use permissive agent config (allow all tools)
--no-human-in-the-loop     Fully autonomous mode, no human review steps
                           (leader only; conflicts with --only-run-planning,
                           --resume, and --resume-instruction)
```

## Workflow

```
 Research Topic (.md)
        |
        v
  +-- LEADER AGENT --+
  |  1. Read topic    |
  |  2. Design plan   |  <--- User reviews & confirms
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

## Runner Backends

The `runner` field in `research_config.jsonc` selects the compute backend:

### SSH (`"runner": "ssh"`)

Launches workers on SSH-accessible machines via tmux sessions. Configure hosts in the `ssh` section:

```jsonc
"ssh": {
    "hosts": [
        { "host": "192.168.1.10", "port": 22, "user": "root" }
    ]
}
```

Supports localhost with automatic SSH key setup.

### PAI DLC (`"runner": "pai"`)

Launches workers as Alibaba Cloud PAI DLC jobs by cloning a template job. Configure credentials and job defaults in the `alibaba_cloud` and `pai_job_template` sections.

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

## Experiment Blueprints

Blueprints are markdown files with 7 required sections that define an experiment:

| Section | Description |
|---|---|
| `[exp_purpose]` | Hypothesis or objective being tested |
| `[exp_codebase_dir]` | Absolute path to experiment code |
| `[exp_venv_exe]` | Path to Python executable |
| `[exp_yaml_path]` | Path to training config YAML |
| `[exp_launch_command]` | Command to start training |
| `[exp_result_dir]` | Output directory for results |
| `[exp_max_time]` | Maximum allowed runtime |

The leader agent generates these from the research plan; worker agents execute them.

## Project Structure

```
rl_auto_research/
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
  leader_experiment.md       Leader agent instructions
  worker_experiment.md       Worker agent instructions
```

## Example: Full Research Cycle

```bash
# 1. Write a research topic
cat > research_topic/kl_ablation.md << 'EOF'
Investigate the effect of KL divergence coefficient on GRPO training stability.
Compare kl_coef values of 0.01, 0.05, and 0.1 across two model sizes.
EOF

# 2. Generate a research plan
alpha-rl-new-planning --research-topic="research_topic/kl_ablation.md"

# 3. Refine the plan if needed
alpha-rl-resume-planning \
    --research-topic="research_topic/kl_ablation.md" \
    --resume-instruction="study kl_type first, ahead of kl coef, try again"

# 4. Execute experiments
alpha-rl-begin-experiments \
    --research-topic="research_topic/kl_ablation.md" \
    --resume-instruction="permission granted, begin research"

# 5. Monitor jobs
alpha-scan-jobs

# 6. Stop a job if needed
alpha-stop-jobs --stop-job-id=<job_id>
```
