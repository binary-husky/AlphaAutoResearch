---
name: leader-experiment
---

# Auto Research Task


## Task:

You are the main research agent, the research lead, responsible for designing, evaluating, and dispatching research plans.

1. [Step 1] Based on the [Main Task], name the current research task and generate the experiment path. See [Main Task] for `${subject_dir}`.

2. [Step 2] Generate a research plan and experiment plan (multi-stage plan if necessary), and write it to `${subject_dir}/main_research_agent/plan.md`. You should elaborate on:
    - How many stages your research may contain
    - The research purpose of each stage
    - What experiment blueprints each stage includes
    - What possible outcomes each stage's experiments may yield, and what potential conclusions correspond to each outcome
    - Generate the first batch of experiment yamls in `${subject_dir}/exp_stage_1/blueprints/blueprint_${n}.yaml` (classic mode only).
    - Generate the first batch of experiment blueprints in `${subject_dir}/exp_stage_1/blueprints/blueprint_${n}.md`.
    - Ensure `ajet.trainer_common.train_print_to_markdown_file_path` and `ajet.trainer_common.val_print_to_markdown_file_path` are correct in `${subject_dir}/exp_stage_1/blueprints/blueprint_${n}.yaml`. (classic mode only)
    - Ensure YAML path is written into blueprint (absolute path).

3. [Step 3 (IMPORTANT!)] Double check the generated yamls and blueprints, ensure they provide valid and effective path and instructions (check "AgentJet YAML Configuration Warnings" and ensure all warnings are addressed). If in `HUMAN-INTERACTION-WHEN-PLANNING` mode, wait for user approval or apply user-requested modifications before proceeding to Step 4.

4. [Step 4 (IMPORTANT!)] EXP_STAGE = 1. Before submitting the first batch of experiments, you need to run the first blueprint's experiment (`blueprint_1.md`) yourself, confirm that the training is running properly in the tmux session. (10 minutes max, only to verify the program is bug free, if any error happens, improve blueprint to fix the issue or fix program). (You should use tmux skill, refer to `ajet/copilot/monitor-with-tmux/SKILL.md` under the agentjet codebase)

5. [Step 5] Generate the first (or next) batch of experiment blueprints, record progress in `${subject_dir}/main_research_agent/progress.md`, dispatch experiments, and wait for them to complete.
    - Note: each batch has a maximum blueprint count limit; see [Capacity], $MAX_PARALLEL_BLUEPRINTS
    - Experiment YAML path: `${subject_dir}/exp_stage_{EXP_STAGE}/blueprints/blueprint_${n}.yaml`
    - Experiment blueprint path: `${subject_dir}/exp_stage_{EXP_STAGE}/blueprints/blueprint_${n}.md`
    - Ensure YAML path is written into blueprint (absolute path)

6. [Step 6] Review the first (or next) batch of experiment results, and append to `${subject_dir}/main_research_agent/progress.md`:
    - Whether the experiments completed successfully.
    - Summarize the current experiment results, what the pre-experiment expectations were, and whether any results exceeded expectations.
    - Explain the current stage's experimental conclusions or hypotheses.
    - Choose one of three options:
        - The experimental conclusions are clear; terminate the experiment (do not give up easily).
        - Modify the planned experiment plan. If modifications are needed, create `${subject_dir}/main_research_agent/plan_v2.md`.
        - Continue with the original experiment plan.

7. [Step 7]:
    - If experiments continue, go back to [Step 5], `EXP_STAGE += 1`.
    - If experiments terminate:
        - Write the experiment report: `${subject_dir}/main_research_agent/final_report.md`.
        - Generate charts from the experimental data and append to `final_report.md`. Please use seaborn to draw figures for best visual effects.
        - Write analysis based on the figures and charts you have drawn.
        - Done, if you are instructed to delete a flag file, remember to delete it.


Reminder: you must continuously append task progress to `${subject_dir}/main_research_agent/progress.md` in real time.


## How to Write Experiment Blueprints:

Experiment blueprints are designed to execute experiments that validate hypotheses or gather necessary data.

An experiment blueprint is a markdown file (blueprint.md). It must contain 7 sections (write clearly; no strict format required, but each section must have textual explanation):

1. [exp_purpose] Experiment purpose (text):
    Briefly describe the main purpose of this experiment and the key differences from other blueprints (e.g., which hyperparameter or environment variable differs).
2. [exp_codebase_dir] Main experiment code path (absolute path):
    The **absolute path** containing all code needed to run the experiment. Relatively small in size. Does not include the Python virtual environment.
3. [exp_venv_exe] Python virtual environment path (absolute path to python executable):
    Path to the Python executable.
4. [exp_yaml_path] (Only needed when using classic mode or swarm mode with YAML configuration) Experiment config file path (absolute path) (may not exist in swarm training mode):
    Path to the experiment configuration YAML file. Should be placed alongside the blueprint file.
5. [exp_launch_command] Training execution command (string):
    E.g. `python -m ajet.launcher --conf tests/bench/benchmark_math/benchmark_math.yaml --skip-check-avail-gpu --with-ray` (classic mode)
6. [exp_result_dir] Result data storage path (absolute path):
    Path for output data storage. Typically `${subject_dir}/exp_stage_{EXP_STAGE}/???_results`
7. [exp_max_time] Maximum runtime is ${MaxTime}; each experiment is forcefully terminated after ${MaxTime}
8. Additional notes: e.g., what preparation is needed before running, how to configure necessary dependencies; what cleanup is needed after running. Also, if the user's "main task description" contains critical information, attach it here. Most importantly, you should rephrased the original user instructions and requirements in this section, so that the worker agent can understand what user is thinking.

Generate experiment blueprints at `${subject_dir}/exp_stage_{EXP_STAGE}/blueprints/blueprint_${n}.md`.
Once blueprints are issued, other agents will execute them. Therefore, each section should have textual explanation — the more detailed the better.

Here is an example of an experiment blueprint (for `exp_purpose` ,`exp_codebase_dir` ,`exp_venv_exe` ,`exp_yaml_path` ,`exp_launch_command` ,`exp_result_dir` ,`exp_max_time`, add additonal fields such as `description` and `hint`):


<blueprint_example_begin>

```markdown
    # Experiment Blueprint - Qwen2.5-14B-Instruct with LoRA Rank 16

    ## [exp_purpose]
    - description: Experiment Purpose
    - purpose: Perform LoRA fine-tuning training (rank=16) on the Qwen2.5-14B-Instruct model on the appworld benchmark, evaluating the model's task completion capability in the appworld environment.

    ## [exp_codebase_dir]
    - description: Main experiment code path (absolute path)
    - dir: /foo/bar/codebase
    - hint: you must `cd` to this directory before executing the training command

    ## [exp_venv_exe]
    - description: Python virtual environment path (absolute path to python)
    - path: /foo/bar/venv/.venv/bin/python
    - hint: you must use this python executable to run the training command, or use `source /foo/bar/venv/.venv/bin/activate` to activate the virtual environment before running the training command

    ## [exp_yaml_path] (Only needed when using classic mode or swarm mode with YAML configuration)
    - description: Experiment configuration file path (absolute path)
    - path: /foo/bar/agentjetdir/tests/bench/benchmark_appworld/benchmark_appworld.yaml

    Note: This yaml file must contain the following key configurations:
    - model.lora.lora_rank: 16
    - model.lora.lora_alpha: 16
    - .......

    ## [exp_launch_command]
    - description: Training execution command
    - command:
        cd /foo/bar/codebase && \
        export APPWORLD_PATH="/tmp/pack_all_in_one" && \
        export APPWORLD_SCRIPT="bash EnvService/env_sandbox/appworld.sh" && \
        source /foo/bar/venv/.venv/bin/activate && \
        python -m ajet.launcher --conf tests/bench/benchmark_appworld/benchmark_appworld.yaml --with-appworld --skip-check-avail-gpu --with-ray
    - hint: Not 100% reliable. You need to flexibly adjust the experiment command based on the specific system you are on.

    ## [exp_result_dir]
    - description: Result data storage path (absolute path)
    - path: /foo/bar/subject_appworld/exp_stage_1/result/qwen2_5_14b/
    - hint: this is where `ajet.trainer_common.train_print_to_markdown_file_path` and `ajet.trainer_common.val_print_to_markdown_file_path` should point to in the yaml configuration.

    ## [exp_max_time]
    - description: Maximum runtime, or ${MaxTime}
    - time: 12 hours
    - note: The runtime should not exceed 12 hours. If the experiment exceeds 12 hours, it needs to be forcefully terminated.

    ## Other Notes

    ### Preparatory Work
    1. Ensure the appworld environment is installed:
    - If /tmp/pack_all_in_one does not exist, run first:
            ```
            wget https://dail-wlcb.oss-cn-wulanchabu.aliyuncs.com/astuner_archive/appworld_pack_v3.tar.gz
            tar -xzf ./appworld_pack_v3.tar.gz -C /tmp
            ```
    - Set the environment variables:
            ```
            export APPWORLD_PATH="/tmp/pack_all_in_one"
            export APPWORLD_SCRIPT="bash EnvService/env_sandbox/appworld.sh"
            ```

    2. Ensure the model path exists: /mnt/data_cpfs/model_cache/modelscope/hub/Qwen/Qwen/Qwen2___5-14B-Instruct

    3. Ensure the output directory exists: /foo/bar/subject_appworld/exp_stage_1/result/qwen2_5_14b/

    ### Closing Work
    1. After training is complete, check the evaluation results in val_print_to_markdown_file_path
    2. Confirm that the finish.flag file has been generated

    ### Key Configuration Reference
    - The launch command uses the --with-appworld flag
    - n_gpus_per_node = 8
    - test_freq = 10
    - execute_test = False (mandatory)

    ### Warning:
    Be careful that venv is relocated at a path, but the codebase maybe located at a different path.
```

<blueprint_example_end>



# AgentJet Configuration

First you have to choose from classic mode and swarm mode, according to user instructions or given examples.

## Classic Mode (YAML Configuration):

    In classic mode, training is configured via a standalone YAML file passed to the launcher CLI (e.g. `python -m ajet.launcher --conf /path/to/exp.yaml`).

    `ajet.execute_test` should be False, because when enabled, training will be interrupted if the training reward score falls below a pre-defined threshold.
    `ajet.project_name` the current research task name; recommended to keep consistent across all blueprints for easier swanlab curve comparison.
    `ajet.experiment_name` the current experiment name; different blueprints and stages should have different experiment names.
    `ajet.trainer_common.n_gpus_per_node` should be as few as possible.
    `ajet.trainer_common.test_freq` should be `${TestFreq}`. `${TestFreq}=10`.
    `ajet.trainer_common.save_freq` should be large enough; we do not save checkpoints.
    `ajet.trainer_common.train_print_to_markdown_file_path` should be where intermediate training results are stored. Not critical, but should still be specified. This file should be written into `exp_result_dir`.
    `ajet.trainer_common.val_print_to_markdown_file_path` should be where evaluation results are stored. Although you can refer to tmux console logs for data, you should always find evaluation results at this path. This file should also be written into `exp_result_dir`. Val attribute list:
        pass_n: For each task, how many times to run repeatedly.
        total_tasks: Number of tasks in the validation dataset.
        num_all_success_tasks: Number of tasks achieving 100% success rate.
        num_pass_n_tasks: Number of tasks that succeed at least once.
        task_pass_rate@1: Average success rate
        task_pass_rate@2: Number of tasks (proportion of all tasks) that succeed at least once in the first 2 trials
        task_pass_rate@4: Number of tasks (proportion of all tasks) that succeed at least once in the first 4 trials (optional)
        task_pass_rate@8: Number of tasks (proportion of all tasks) that succeed at least once in the first 8 trials (optional)
        mean_reward: Mean validation reward across all data points.
        std_reward: Reward standard deviation across all data points.
    `ajet.trainer_common.val_before_train` should be True, because we want to capture the initial performance of the model before training.
    `ajet.trainer_common.total_epochs` should be large enough, but you only have `${MaxTime}` hours to run each experiment.
    `ajet.trainer_common.total_training_steps` the max global steps, prior than `ajet.trainer_common.total_epochs` if it is not `null`.

    For other configurations, refer to `agentjet/ajet/default_config/ajet_default.yaml`, do not use ANY configurations that is absent in `ajet_default.yaml`,

## Swarm Mode (AgentJetJob Configuration):

    In swarm mode, training is configured via the `AgentJetJob` Python class.
    To use Swarm Training Mode, first,
    we always start by launching the swarm server in a tmux session:
    ```bash
    ajet-swarm start --swarm-port=10086
    ```
    And then run the swarm client (usually a python script) in **ANOTHER** tmux session.
    Assign training config yaml:
        - choice 1: in swarm client script, use AgentJetJob to set training arguments
        - choice 2: in swarm client script, use AgentJetJob's base_yaml_config config (optional) to assign the yaml path, and then change the yaml to alter training configurations.
        - configuration priority (highest to lowest):
            - general config kwargs in AgentJetJob's init
            - base_yaml_config config argument in AgentJetJob's init (yaml file configuration)
            - the default base_yaml_config: agentjet_codebase/ajet/default_config/ajet_swarm_default.yaml
        - configuration coverage:
            - general config kwargs in AgentJetJob's init covers the most important configurations.
            - yaml config covers all configurations.

    `project_name` the current research task name; recommended to keep consistent across all blueprints for easier swanlab curve comparison.
    `experiment_name` the current experiment name; different blueprints and stages must have different experiment names.
    `n_gpu` GPUs allocated on the swarm server; should be as few as possible.
    `algorithm` advantage estimator; typically `"grpo"`.
    `model` absolute path to the base model to train.
    `batch_size` server-side training batch size (the watermark that triggers a weight update).
    `num_repeat` GRPO group size — how many repeated samples per task_id the swarm server expects.
    `swarm_mode` must be True.
    `swarm_mode_sample_collection_method` one of `"rollout_until_finish_enough_episodes"`, `"rollout_until_finish_enough_tasks"` (default), `"rollout_until_finish_enough_non_dummy_tasks"`. Pick the last when many tasks produce uniform reward (all-pass or all-fail GRPO groups give zero advantage and waste compute).
    `max_env_worker` estimated number of episodes running in parallel across all swarm clients combined.
    `max_prompt_length`, `max_response_length`, `max_response_length_in_one_turn`, `max_model_len` must all be set together or all left as None. Constraints: `max_prompt_length + max_response_length <= max_model_len`, and `max_response_length_in_one_turn <= max_response_length`.
    `max_num_seqs` maximum sequences each vLLM engine processes in parallel (default 64).
    `mini_batch_num` number of `optimizer.step` calls per big training batch.
    `lora_rank` set > 0 to enable LoRA. When > 0: `lora_load_format` must be `"safetensors"`, `layered_summon` must be True, and `lr` must be > 1e-5 (else `AgentJetJob` raises).
    `lora_alpha`, `lora_target_modules`, `lora_load_format`, `layered_summon` LoRA fields; only meaningful when `lora_rank > 0`.
    `gpu_memory_utilization` vLLM GPU memory utilization (default 0.85).
    `lr` optimizer learning rate (default 1e-6 for full FT; > 1e-5 required for LoRA).
    `ppo_epochs` PPO epochs per update (default 1).
    `compute_madness_checklist` rollout-time abnormality checks; default `["nonsense"]` detects degenerate repeated tokens (e.g. `"但但但但..."`).
    `train_print_to_markdown_file_path` path where training metrics are appended; should be inside `exp_result_dir`. Not critical, but should still be specified.
    `val_print_to_markdown_file_path` path where evaluation results are appended; should be inside `exp_result_dir`. Same val attribute list as Classic Mode (pass_n, total_tasks, num_all_success_tasks, num_pass_n_tasks, task_pass_rate@1/2/4/8, mean_reward, std_reward).
    `total_training_steps` hard cap on global steps; takes priority over `total_epochs` when not None. Should be large enough, but you only have `${MaxTime}` hours per experiment.

    Configurations not exposed as `AgentJetJob` kwargs (e.g. `ajet.execute_test`, `trainer_common.test_freq`, `trainer_common.save_freq`, `trainer_common.val_before_train`, `trainer_common.total_epochs`) must be set via a custom `base_yaml_config`, or by mutating `ajet_job.config` directly before `swarm_worker.auto_sync_train_config_and_start_engine(ajet_job)`. Apply the same recommendations as Classic Mode (`execute_test=False`, `test_freq=${TestFreq}=10`, large `save_freq` since we do not save checkpoints, `val_before_train=True`).

    Configuration priority (highest to lowest):
        1. kwargs passed to `AgentJetJob.__init__`
        2. the YAML pointed to by `base_yaml_config`
        3. default `agentjet/ajet/default_config/ajet_swarm_default.yaml`

    For swarm-mode blueprints, `[exp_yaml_path]` is typically absent (the config is in-script). Use `ajet_job.dump_job_as_yaml('./resolved.yaml')` once during blueprint review to inspect the fully-resolved config. The `[exp_launch_command]` must (1) start the swarm server in a tmux session via `ajet-swarm start --swarm-port=<port>`, then (2) run the swarm client python script in a separate tmux session.

    For the full argument list and defaults, refer to `ajet/copilot/job.py` (class `AgentJetJob`) or run `help(AgentJetJob)`. Do not pass any kwarg absent from `AgentJetJob.__init__`.


## AgentJet Launch

### Classic Mode

WARNING: you must choose from classic mode and swarm mode, according to user instructions or examples.

- assign training config yaml: `--conf /path/to/yaml`
- skip gpu check: `--skip-check-avail-gpu` (skip this when you are not using all 8 GPUs in a server)
- init ray before training (always to this): `--with-ray`
- init appworld service before training: `--with-appworld` (must install appworld according to `agentjet/docs/en/example_app_world.md` before you use `--with-appworld`)
- kill all ray and python processes (dangerous! never use this one.): `--autokill`


### Swarm Mode

WARNING: you must choose from classic mode and swarm mode, according to user instructions or examples.

AgentJet has a unique swarm training mode.
AgentJet training network (swarm) is composed by interconnected swarm server and swarm client nodes.
The number of swarm servers depends on the number of models being trained,
as each server independently hosts and trains a distinct model.
While each swarm client runs agents to gather trajectories and send reward back to server for RL training.

To use Swarm Training Mode, first,
we always start by launching the swarm server in a tmux session:

```bash
ajet-swarm start --swarm-port=10086
```

And then run the swarm client (usually a python script) in another tmux session.

Assign training config yaml:
    - choice 1: in swarm client script, use AgentJetJob to set training arguments
    - choice 2: in swarm client script, use AgentJetJob's base_yaml_config config (optional) to assign the yaml path, and then change the yaml to alter training configurations.
    - configuration priority (highest to lowest):
        - general config kwargs in AgentJetJob's init
        - base_yaml_config config argument in AgentJetJob's init (yaml file configuration)
        - the default base_yaml_config: agentjet_codebase/ajet/default_config/ajet_swarm_default.yaml
    - configuration coverage:
        - general config kwargs in AgentJetJob's init covers the most important configurations.
        - yaml config covers all configurations.





## How to Start a Batch of Experiments (After Writing Blueprints):

Warning: Do not generate more than [Capacity] blueprints within one stage! Never let more than the maximum parallel blueprint count (see [Capacity], $MAX_PARALLEL_BLUEPRINTS) run at the same time. Always check the current running blueprint count before submitting new blueprints.


Please follow the following checklist (say "yes" to each item before starting to dispatch experiments):

[] Did you clearly identify which mode to use, classic mode or swarm mode, based on user instructions or examples?
[] In plan, did you estimate what possible outcomes each stage's experiments may yield, and what potential conclusions correspond to each outcome?
[] Did you successfully generate experiment blueprints at `${subject_dir}/exp_stage_{EXP_STAGE}/blueprints/blueprint_${n}.md` ?
[] Did you double check the generated yamls and blueprints, ensure they provide valid and effective path and instructions ?
[] Did you run the first blueprint's experiment (`blueprint_1.md`) yourself, confirm that the training is running properly in the tmux session?
[] Did you ensure that you have rephrased the original user instructions and requirements (research topic) in blueprints, so that the worker agent who execute experiments more accurately?
[] Did you ensure that the total number of blueprints at each stage is less than [Capacity]?

If all the checklist is satisfied, you can start to dispatch the experiments:

- Run `python -m alpha_auto_research.blueprint_runner.blueprint_runner --runner=${runner} --blueprint=${path_to_blue_print} --acknowledge-max-parallel-capacity=${MAX_PARALLEL_BLUEPRINTS}` to submit the blueprint to the GPU cluster
- Wait at least **10 seconds** between each blueprint submission to avoid overloading the scheduler.
- Record the returned job_id in `${subject_dir}/main_research_agent/progress.md`
- Record task progress in `${subject_dir}/main_research_agent/progress.md`

Note: remember to batch process. When possible, generate a batch of blueprints before entering the wait state, allowing multiple experiments to run in parallel.




## How to Wait for Experiments to Complete:

Every 10 minutes (sleep 600):
- Check whether [exp_result_dir] contains a `finish.flag` file. If yes, the task is complete; otherwise, continue waiting.
- Run `python -m alpha_auto_research.blueprint_runner.scan_jobs --runner=${runner}` to check the current blueprint status (Queuing / Running / Succeeded)




## How to Stop Experiments:

- Think twice when you terminate a experiment!
- Run `python -m alpha_auto_research.blueprint_runner.stop_jobs --runner=${runner} --stop-job-id=<job_id>` to stop a running job
- Multiple jobs: `python -m alpha_auto_research.blueprint_runner.stop_jobs --runner=${runner} --stop-job-id=<id1> --stop-job-id=<id2>`
- To also delete after stopping: add `--delete`
- Warning: NEVER USE `tmux kill-server`! That is suicide, it will kill ALL tmux sessions on the server!



## Current Progress:

- If `${subject_dir}/main_research_agent/progress.md` exists, read the progress; if not, start from stage 1



## Warning

You must not edit `research_config.jsonc` in any circumstances.