---
name: worker-experiment
description: Execute ML experiment blueprints on GPU clusters, monitor training via tmux, debug errors, and report results. Use this skill whenever the user provides an experiment blueprint to run, asks to execute a training job, wants to monitor a running experiment, or needs to launch and track an AgentJet training session. Also triggers for "run this blueprint", "start the experiment", "monitor training", or any task involving blueprint execution with tmux monitoring.
---

## Your Task

Before doing anything, create a log file `${exp_result_dir}/experiment_log.md`, refer to the blueprint to get `${exp_result_dir}`.

1. Run the experiment according to the experiment blueprint.
    - when execute training commandline, record your command into `${exp_result_dir}/experiment_log.md`.
2. Wait for the experiment to finish, error or time out.
3. If the experiment fails, attempt to fix it and document the debugging process (`${exp_result_dir}/experiment_log.md`). If it cannot be fixed, skip to step 5.
4. Place comprehensive experiment results in the designated location (`${exp_result_dir}/experiment_log.md`).
5. Create a `finish.flag` file in [exp_result_dir] to mark the task as complete.
6. Done.

## Experiment Blueprint:

Experiment blueprints are designed to execute experiments that validate hypotheses or gather necessary data.
An experiment blueprint is a markdown file (blueprint.md). It contains 7 sections — you should execute the task based on this information:

1. [exp_purpose] Experiment purpose (text):
    Briefly describe the main purpose of this experiment and the key differences from other blueprints (e.g., which hyperparameter or environment variable differs).
2. [exp_codebase_dir] Main experiment code path (absolute path):
    The **absolute path** containing all code needed to run the experiment. Relatively small in size. Does not include the Python virtual environment. Remember to cd to this path before starting the experiment.
3. [exp_venv_exe] Python virtual environment path (absolute path to python executable):
    Path to the Python executable. E.g.: /mnt/data_cpfs/agentjet/project/.venv/bin/python
4. [exp_yaml_path] Experiment config file path (absolute path):
    Path to the experiment configuration YAML file. This file must be located within the main experiment code path. E.g.: /mnt/data_cpfs/agentjet/project/tests/bench/benchmark_math/benchmark_math.yaml
5. [exp_launch_command] Training execution command (string):
    E.g. python -m ajet.launcher --conf tests/bench/benchmark_math/benchmark_math.yaml --skip-check-avail-gpu --with-ray
6. [exp_result_dir] Result data storage path (absolute path):
    Path for output data storage
7. [exp_max_time] Maximum runtime is ${MaxTime}; each experiment is forcefully terminated after ${MaxTime}


## YAML Configuration Notes:

`ajet.execute_test` should be False, because when enabled, training will be interrupted if the training reward score falls below a pre-defined threshold.
`ajet.project_name` the current research task name; recommended to keep consistent across all blueprints for easier swanlab curve comparison.
`ajet.experiment_name` the current experiment name; different blueprints and stages should have different experiment names.
`ajet.trainer_common.test_freq` specifies how many steps between each evaluation.
`ajet.trainer_common.n_gpus_per_node` number of GPUs.
`ajet.trainer_common.train_print_to_markdown_file_path` should be where intermediate training results are stored. Not critical, but should still be specified.
`ajet.trainer_common.val_print_to_markdown_file_path` should be where evaluation results are stored. Although you can refer to tmux console logs for data, you should always find evaluation results at this path:
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
- skip gpu check: `--skip-check-avail-gpu`
- init ray before training (always to this): `--with-ray`
- init appworld service before training: `--with-appworld` (must install appworld according to `agentjet/docs/en/example_app_world.md` before you use `--with-appworld`)
- kill all ray and python (dangerous! never use this one.): `--autokill`

## Running Experiments with tmux

See the "Experiment Monitoring Skill" section below. Note: when creating a session, the session name must contain the keyword `ajet` and reflect `exp_purpose`, e.g. `ajet_math_top_k_ablation`.


## Do Not Terminate Running Experiments Lightly

You must ensure the experiment continues running throughout the [exp_max_time] period. Exceptions:

- The experiment error is too severe and cannot be fixed

- The experiment has completed successfully ahead of schedule, with complete data collected

- The experiment is in its mid-to-late stage, and `mean_reward` or `task_pass_rate` in `val_print_to_markdown_file_path` has stopped changing for an extended period


## Experiment Monitoring Skill

```
    ---
    name: monitor-with-tmux
    description: Monitor training progress by reading tmux content at exponential backoff intervals (30s, 1min, 2min, 4min, 8min, 16min), analyze logs when anomalies occur, and provide fix suggestions
    license: Complete terms in LICENSE.txt
    ---

    # Monitor with Tmux

    Monitor in tmux, detect anomalies, analyze errors, provide fix suggestions.

    ## Step Zero

    Create a sleep script for tmux monitoring:

    1. Create `./tmux_wait.py`

    ```python
    import argparse
    import subprocess
    import time

    SHELLS = {"bash", "zsh", "sh", "fish", "csh", "tcsh", "ksh", "dash", "ash"}

    def smart_sleep(session: str, seconds: float, check_every: float = 2.0) -> bool:
        end_time = time.time() + seconds
        while time.time() < end_time:
            try:
                r = subprocess.run(
                    ["tmux", "list-panes", "-F", "#{pane_current_command}", "-t", session],
                    capture_output=True, text=True, timeout=5
                )
                if r.returncode != 0:
                    return False
                cmds = [l.strip().lower() for l in r.stdout.splitlines() if l.strip()]
                if not any(c not in SHELLS for c in cmds):
                    return False
            except Exception:
                return False
            time.sleep(min(check_every, end_time - time.time()))
        return True

    def print_tmux_window(session: str, lines: int = 100):
        try:
            r = subprocess.run(
                ["tmux", "capture-pane", "-p", "-t", session],
                capture_output=True, text=True, timeout=5
            )
            if r.returncode == 0:
                output_lines = r.stdout.splitlines()
                print("\n\n--- tmux pane output (last {} lines) ---".format(lines))
                print("\n".join(output_lines[-lines:]))
                print("--- tmux pane output ends ---\n\n")
        except Exception as e:
            print(f"Failed to capture tmux pane: {e}")

    def main():
        parser = argparse.ArgumentParser(description="Wait for a tmux session with smart early-exit.")
        parser.add_argument("session", help="tmux session name")
        parser.add_argument("seconds", type=float, help="total seconds to wait")
        args = parser.parse_args()
        timed_out = smart_sleep(args.session, args.seconds, 2)
        print_tmux_window(args.session, 100)
        raise SystemExit(0 if timed_out else 1)

    if __name__ == "__main__":
        main()
    ```

    ## Begin Monitoring

    When you need to monitor a tmux window, run:

    ```bash
    python ./tmux_wait.py my_ajet_session_name 30
    ```

    This means:
    1. Monitor the tmux session named my_ajet_session_name
    2. Wait for 30 seconds

    - Exit code 0: Normal timeout (command is still running)
    - Exit code 1: Command finished early or session disappeared

    ## Using SSH

    When using SSH, always use a local tmux window to establish the SSH connection.

    ## When You Want to Delay Before Reading tmux Again

    You must have early-return-on-error capability. Do not use `sleep xxx`; instead use `python ./tmux_wait.py my_ajet_session_name xxx`

    DO NOT USE: `sleep 60 && tmux capture-pane -t my_ajet_session_name -p | tail -80`

    YOU SHOULD USE: `python ./tmux_wait.py my_ajet_session_name 30 && tmux capture-pane -t my_ajet_session_name -p | tail -80`

    - 60 seconds is too long
    - Always use `python ./tmux_wait.py` to wait



    ## Examples:


    ### Without SSH

    0 examples available


    ### With SSH

    1 example available

    ```agent

    --- example user instruction begin ---
    login
    ssh root@localhost -p 8824
    goto
    /foo/bar/venv
    run with venv and monitor
    source .venv/bin/activate && python -m ajet.launcher --conf tests/bench/benchmark_math/benchmark_math.yaml --skip-check-avail-gpu --with-ray
    --- example user instruction end ---

    --- example agent reaction begin ---
    The user wants me to monitor a tmux session while running a training job. Let me break down what they're asking:
    1. SSH into a remote machine (root@localhost -p 8824)
    2. Go to a specific directory
    3. Activate a virtual environment and run a Python command
    4. Monitor the tmux session

    # Write tmux_wait.py
    ....

    # Create tmux session for training (note: session name must contain the keyword `ajet`)
    $ tmux new-session -d -s ajet_session -c "/foo/bar/venv"
    ...

    # Send SSH command to tmux session
    $ tmux send-keys -t ajet_session "ssh root@localhost -p 8824" Enter
    ...

    # Wait and check SSH connection
    $ python3 ./tmux_wait.py ajet_session 10 && tmux capture-pane -t ajet_session -p | tail -20
    SSH connected successfully. Now I need to navigate to the directory and run the training command. Let me send the commands to the tmux session.
    ...

    # Navigate to working directory
    $ tmux send-keys -t ajet_session "cd /foo/bar/venv" Enter
    ...

    # Start training with venv and launcher
    $ tmux send-keys -t ajet_session "source .venv/bin/activate && python -m ajet.launcher --conf tests/bench/benchmark_math/benchmark_math.yaml --skip-check-avail-gpu --with-ray" Enter
    ...

    # Capture initial training output
    $ tmux capture-pane -t ajet_session -p | tail -40
    ...

    # Wait 30s and check training progress
    $ python3 ./tmux_wait.py ajet_session 30 && tmux capture-pane -t ajet_session -p | tail -50
    ...
    Training is running. The command is executing properly. Let me continue monitoring at 1 minute intervals.

    # Wait 1min and check training progress
    $ python3 ./tmux_wait.py ajet_session 60 && tmux capture-pane -t ajet_session -p | tail -50
    ...

    # Wait 2min and check training progress
    $ python3 ./tmux_wait.py ajet_session 120 && tmux capture-pane -t ajet_session -p | tail -60
    ...
    Training is progressing well. Checkpoints loaded, vLLM server started, swanlab is tracking the run. No errors so far, just warnings. Let me continue monitoring.

    # Wait 4min and check training progress
    $ python3 ./tmux_wait.py ajet_session 240 && tmux capture-pane -t ajet_session -p | tail -60
    ...

    ... multiple monitoring rounds ...

    --- example agent reaction end ---

    # Destroy tmux session
    tmux kill-session -t ajet_session

    ```
```

## Using GPUs

You should use `--skip-check-avail-gpu` and `--with-ray` argument of `ajet` when starting the experiment.
This is very important when you feel that you are not the only one that is experimenting with a blueprint.
Then you should use `CUDA_VISIBLE_DEVICES` env variable to declare the GPUs you are using.

When there are GPUs that are busy, check `nvidia-smi` before running the experiment.

And never use `--autokill` argument, that will destory all running experiments running on the same server.


## Warning

- You must not edit `research_config.jsonc` in any circumstances!
- When encounter any error, you should check experiment blueprint, and double check you have followed all the instructions in the blueprint (e.g. venv, additional service installation)!
