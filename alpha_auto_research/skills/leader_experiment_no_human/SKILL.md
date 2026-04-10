---
name: leader-experiment-no-human
description: Fully autonomous research lead agent for designing, evaluating, and dispatching ML experiment plans using AgentJet — runs without human approval. Use this skill when the user wants unattended/autonomous experiment orchestration, hands-off research runs, or batch experiment management that should proceed without waiting for human confirmation. Ideal for overnight runs, large-scale ablations, or when the user explicitly says "run without asking me" or "fully automated".
---

# Auto Research Task

## Task:

You are the main research agent, the research lead, responsible for designing, evaluating, and dispatching research plans.

1. [Step 1] Based on the [Main Task], name the current research task and generate the experiment path. See [Main Task] for `${subject_dir}`.

2. [Step 2] Generate a research plan and experiment plan, and write it to `./${subject_dir}/main_research_agent/plan.md`. You should elaborate on:
    - How many stages your research contains
    - The research purpose of each stage
    - What experiment blueprints each stage includes
    - What possible outcomes each stage's experiments may yield, and what potential conclusions correspond to each outcome
    - Generate the first batch of experiment yamls in `${subject_dir}/exp_stage_1/blueprints/blueprint_${n}.yaml`.
    - Generate the first batch of experiment blueprints in `${subject_dir}/exp_stage_1/blueprints/blueprint_${n}.md`.

3. [Step 3] Double check the generated yamls and blueprints, ensure they provide valid and effective path and instructions.

4. [Step 4] EXP_STAGE = 1

5. [Step 5] Generate the first (or next) batch of experiment blueprints, record progress in `./${subject_dir}/main_research_agent/progress.md`, dispatch experiments, and wait for them to complete.
    - Note: each batch has a maximum blueprint count limit; see [Capacity]
    - Experiment YAML path: `${subject_dir}/exp_stage_{EXP_STAGE}/blueprints/blueprint_${n}.yaml`
    - Experiment blueprint path: `${subject_dir}/exp_stage_{EXP_STAGE}/blueprints/blueprint_${n}.md`
    - Ensure YAML path is written into blueprint (absolute path)

6. [Step 6] Review the first (or next) batch of experiment results, and append to `./${subject_dir}/main_research_agent/progress.md`:
    - Whether the experiments completed successfully.
    - Summarize the current experiment results, what the pre-experiment expectations were, and whether any results exceeded expectations.
    - Explain the current stage's experimental conclusions or hypotheses.
    - Choose one of three options:
        - The experimental conclusions are clear; terminate the experiment (do not give up easily).
        - Modify the planned experiment plan. If modifications are needed, create `./${subject_dir}/main_research_agent/plan_v2.md`.
        - Continue with the original experiment plan.

7. [Step 7]:
    - If experiments continue, go back to [Step 5], `EXP_STAGE += 1`.
    - If experiments terminate:
        - Write the experiment report: `./${subject_dir}/main_research_agent/final_report.md`.
        - Generate charts from the experimental data and append to `final_report.md`. Please use seaborn to draw figures for best visual effects.
        - Write analysis based on the figures and charts you have drawn.
        - Done, if you are instructed to delete a flag file, remember to delete it.


Reminder: you must continuously append task progress to `./${subject_dir}/main_research_agent/progress.md` in real time.


## How to Write Experiment Blueprints:

Experiment blueprints are designed to execute experiments that validate hypotheses or gather necessary data.

An experiment blueprint is a markdown file (blueprint.md). It must contain 7 sections (write clearly; no strict format required, but each section must have textual explanation):

1. [exp_purpose] Experiment purpose (text):
    Briefly describe the main purpose of this experiment and the key differences from other blueprints (e.g., which hyperparameter or environment variable differs).
2. [exp_codebase_dir] Main experiment code path (absolute path):
    The **absolute path** containing all code needed to run the experiment. Relatively small in size. Does not include the Python virtual environment.
3. [exp_venv_exe] Python virtual environment path (absolute path to python executable):
    Path to the Python executable.
4. [exp_yaml_path] Experiment config file path (absolute path):
    Path to the experiment configuration YAML file. Should be placed alongside the blueprint file.
5. [exp_launch_command] Training execution command (string):
    E.g. `python -m ajet.launcher --conf tests/bench/benchmark_math/benchmark_math.yaml --skip-check-avail-gpu --with-ray`
6. [exp_result_dir] Result data storage path (absolute path):
    Path for output data storage. Typically `${subject_dir}/exp_stage_{EXP_STAGE}/???_results`
7. [exp_max_time] Maximum runtime is ${MaxTime}; each experiment is forcefully terminated after ${MaxTime}
8. Additional notes: e.g., what preparation is needed before running, how to configure necessary dependencies; what cleanup is needed after running. Also, if the user's "main task description" contains critical information, attach it here. A todo list is recommended here.


Generate experiment blueprints at `${subject_dir}/exp_stage_{EXP_STAGE}/blueprints/blueprint_${n}.md`.
Once blueprints are issued, other agents will execute them. Therefore, each section should have textual explanation — the more detailed the better.

Here is an example of an experiment blueprint:


<blueprint_example_begin>

```markdown
    # Experiment Blueprint - Qwen2.5-14B-Instruct with LoRA Rank 16

    ## [exp_purpose]
    Experiment Purpose: Perform LoRA fine-tuning training (rank=16) on the Qwen2.5-14B-Instruct model on the appworld benchmark, evaluating the model's task completion capability in the appworld environment.

    ## [exp_codebase_dir]
    Main experiment code path (absolute path): /foo/bar/codebase

    ## [exp_venv_exe]
    Python virtual environment path (absolute path to python): /foo/bar/venv/.venv/bin/python

    ## [exp_yaml_path]
    Experiment configuration file path (absolute path): tests/bench/benchmark_appworld/benchmark_appworld.yaml

    Note: This yaml file must contain the following key configurations:
    - model.lora.lora_rank: 16
    - model.lora.lora_alpha: 16
    - .......

    ## [exp_launch_command]
    Training execution command:
    ```
    cd /foo/bar/codebase && \
    export APPWORLD_PATH="/tmp/pack_all_in_one" && \
    export APPWORLD_SCRIPT="bash EnvService/env_sandbox/appworld.sh" && \
    python -m ajet.launcher --conf tests/bench/benchmark_appworld/benchmark_appworld.yaml --with-appworld --skip-check-avail-gpu --with-ray
    ```
    Note: You need to flexibly adjust the experiment command based on the specific system you are on.

    ## [exp_result_dir]
    Result data storage path (absolute path): /foo/bar/subject_appworld/exp_stage_1/result/qwen2_5_14b/

    ## [exp_max_time]
    ${MaxTime} = 12 hours
    Note: The runtime should not exceed 12 hours. If the experiment exceeds 12 hours, it needs to be forcefully terminated.

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
```

<blueprint_example_end>


## How to Start a Batch of Experiments (After Writing Blueprints):

- Generate experiment blueprints at `${subject_dir}/exp_stage_{EXP_STAGE}/blueprints/blueprint_${n}.md`
- Run `python -m alpha_auto_research.blueprint_runner.blueprint_runner --runner=${runner} --blueprint=${path_to_blue_print}` to submit the blueprint to the GPU cluster
- Wait at least 10 seconds between each blueprint submission to avoid overloading the scheduler.
- Record the returned job_id in `./${subject_dir}/main_research_agent/progress.md`
- Record task progress in `./${subject_dir}/main_research_agent/progress.md`

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



## Current Progress:

- If `./${subject_dir}/main_research_agent/progress.md` exists, read the progress; if not, start from stage 1


## AgentJet YAML Configuration Warnings:

`ajet.execute_test` should be False, because when enabled, training will be interrupted if the training reward score falls below a pre-defined threshold.
`ajet.project_name` the current research task name; recommended to keep consistent across all blueprints for easier swanlab curve comparison.
`ajet.experiment_name` the current experiment name; different blueprints and stages should have different experiment names.
`ajet.trainer_common.n_gpus_per_node` should be as few as possible.
`ajet.trainer_common.test_freq` should be `${TestFreq}`. `${TestFreq}=10`.
`ajet.trainer_common.save_freq` should be large enough; we do not save checkpoints.
`ajet.trainer_common.train_print_to_markdown_file_path` should be where intermediate training results are stored. Not critical, but should still be specified.
`ajet.trainer_common.val_print_to_markdown_file_path` should be where evaluation results are stored. Although you can refer to tmux console logs for data, you should always find evaluation results at this path. Val attribute list:
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


## AgentJet Launcher Arguments

- assign training config yaml: `--conf /path/to/yaml`
- skip gpu check: `--skip-check-avail-gpu` (skip this when you are not using all 8 GPUs in a server)
- init ray before training (always to this): `--with-ray`
- init appworld service before training: `--with-appworld` (must install appworld according to `agentjet/docs/en/example_app_world.md` before you use `--with-appworld`)
- kill all ray and python (dangerous! never use this one.): `--autokill`

## Warning

You must not edit `research_config.jsonc` in any circumstances.
