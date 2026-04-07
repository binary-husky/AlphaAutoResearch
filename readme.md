# rl_auto_research_v2

Automated RL research system with a leader-worker architecture.

## Setup

1. Copy config template and fill in your credentials:
   ```bash
   cp research_config.example.jsonc research_config.jsonc
   # Edit research_config.jsonc with your actual keys
   ```

2. Install dependencies:
   ```bash
   pip install alibabacloud-pai-dlc20201203 alibabacloud-aiworkspace20210204 alibabacloud-credentials loguru
   ```

## Usage

### Run as leader (orchestrate research)
```bash
bash begin_research.bash \
    --blueprint=./topics/topic_07_math/ajet_auto_research_multi_experiment.md \
    --additional-prompt="your instructions here"
```

### Run as worker (on PAI DLC node)
```bash
python -m rl_auto_research.opencode_runner worker run --attach=http://localhost:4096 "your prompt"
```

### Launch a single experiment on PAI
```bash
python -m rl_auto_research.experiment_worker.blueprint_runner --blueprint=path/to/blueprint.md
```

### Scan running PAI jobs
```bash
python -m rl_auto_research.blueprint_runner.scan_jobs
```

## Project Structure

```
rl_auto_research/          # Core library
  config.py                # Loads research_config.jsonc
  opencode_runner.py       # Unified leader/worker agent
  pai/                     # Alibaba PAI DLC client & job scanner
  experiment_worker/     # Abstract launcher + PAI backend
blueprints/                # Research blueprint templates
topics/                    # Research topic data (gitignored)
subjects/                  # Experiment subject data (gitignored)
```
