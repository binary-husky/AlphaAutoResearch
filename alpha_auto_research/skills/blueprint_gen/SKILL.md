Your task is to generate a experiment blueprint at user's **current working dir**.

- 采用试错循环
  - 编写代码 & yaml配置 -> 运行训练 -> 发现异常 -> 修复异常直到训练成功 -> 编写代码 & yaml配置 -> (循环往复，优化成功率) -> ....

- 每个实验 `8` GPU


Experiment blueprints are designed to execute experiments that validate hypotheses or gather necessary data.

An experiment blueprint is a markdown file (blueprint.md). It must contain 7 sections (write clearly; no strict format required, but each section must have textual explanation):

1. [exp_purpose] Experiment purpose (text):
    Briefly describe the main purpose of this experiment and the key differences from other blueprints (e.g., which hyperparameter or environment variable differs).
2. [exp_codebase_dir] Main experiment code path (absolute path):
    The **absolute path** containing all code needed to run the experiment. Relatively small in size. Does not include the Python virtual environment.
    Default: ./
3. [exp_venv_exe] Python virtual environment path (absolute path to python executable):
    Path to the Python executable.
    Default: ./venv/bin/python
4. [exp_yaml_path] Experiment config file path (absolute path):
    Path to the experiment configuration YAML file. Should be placed alongside the blueprint file.
    Default: NA, the agent must write its own yaml file for the experiment.
5. [exp_launch_command] Training execution command (string):
    Default: the agent must write its own command
6. [exp_result_dir] Result data storage path (absolute path):
    Path for output data storage.
    Default: ./auto_agent/exp_results/
7. [exp_max_time] Maximum runtime is ${MaxTime}; each experiment is forcefully terminated after ${MaxTime}
    Default:
      - MaxTime per run:
        24 hours
      - First step success timeout:
        20 minutes (when you see the first kl loss value printed in tmux window, that means the first step is successful, if you did not see any kl loss value printed in tmux window after 20 minutes, that means the first step is failed, you can check the log file for details)


8. Additional notes: e.g., what preparation is needed before running, how to configure necessary dependencies; what cleanup is needed after running. Also, if the user's "main task description" contains critical information, attach it here. A todo list is recommended here.


Once blueprints are issued, other agents will execute them. Therefore, each section should have textual explanation — the more detailed the better.

Here is an example of an experiment blueprint (for `exp_purpose` ,`exp_codebase_dir` ,`exp_venv_exe` ,`exp_yaml_path` ,`exp_launch_command` ,`exp_result_dir` ,`exp_max_time`, add additonal fields such as `description` and `hint`):




<blueprint_example_begin>

```markdown
    # Experiment Blueprint

    ## [exp_purpose]
    - description:
    - hint:
    - content 1:
    - content 2:
    - content 3:

    ## [exp_codebase_dir]
    - description:
    - hint:
    - content 1:
    - content 2:
    - content 3:
    - warning 1:
    - warning 2:

    ## [exp_venv_exe]
    - description:
    - hint:
    - content 1:
    - content 2:
    - content 3:
    - warning 1:
    - warning 2:

    ## [exp_yaml_path]
    - description:
    - hint:
    - content 1:
    - content 2:
    - content 3:
    - warning 1:
    - warning 2:

    ## [exp_launch_command]
    - description:
    - hint:
    - content 1:
    - content 2:
    - content 3:
    - warning 1:
    - warning 2:

    ## [exp_result_dir]
    - description:
    - hint:
    - content 1:
    - content 2:
    - content 3:
    - warning 1:
    - warning 2:

    ## [exp_max_time]
    - description:
    - hint:
    - content 1:
    - content 2:
    - content 3:
    - warning 1:
    - warning 2:

    ## Other Notes
    - description:
    - note 1:
    - note 2:
    - note 3:
    - note 4:
    - note 5:
    ....

```

<blueprint_example_end>
