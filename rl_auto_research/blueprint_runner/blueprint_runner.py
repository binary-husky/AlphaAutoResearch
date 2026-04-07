"""
PAI DLC experiment launcher.

Launches a blueprint as a PAI DLC job by cloning a template,
injecting a worker boot command that starts opencode inside tmux.
"""

import os
from textwrap import dedent

from rl_auto_research.config import config
from rl_auto_research.pai.client import create_job, wait_for_job
from rl_auto_research.experiment_worker.base import ExperimentSubagent


class PaiExperimentSubagent(ExperimentSubagent):

    def _build_user_command(self, blueprint_path: str) -> str:
        uv_cache = config["paths"]["uv_cache"]
        project_root = config["paths"]["project_root"]

        return dedent(f"""
            rm -rf /root/.local/share/uv && ln -s {uv_cache} /root/.local/share/uv
            service ssh start && \\
            wget --header="Cache-Control: no-cache" https://public.agent-matrix.com/publish/bashrc/plus/open/best/bashrc_extend.bash && \\
            bash -i -c "source bashrc_extend.bash && up_rc && rm bashrc_extend.bash" && \\
            echo "set-option -g history-limit 100000" >> ~/.tmux.conf && tmux source-file ~/.tmux.conf && \\
            tmux start-server 2>/dev/null || true && \\
            sed -i '2 a\\  "permission": "allow",' /root/.config/opencode/opencode.json
            tmux has-session -t main 2>/dev/null || tmux new-session -d -s main && tmux new-window -n "TRAIN" && \\
            tmux send-keys -t "TRAIN" "cd {project_root}" Enter
            tmux send-keys -t "TRAIN" "source .venv/bin/activate" Enter
            tmux send-keys -t "TRAIN" "export SETUPTOOLS_USE_DISTUTILS=local" Enter
            tmux send-keys -t "TRAIN" "export OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS=1800000" Enter
            sleep 5;
            tmux send-keys -t "TRAIN" "python -m rl_auto_research.opencode_runner worker run --blueprint={blueprint_path}." Enter
            touch /still_training && while true; do [ -f "/still_training" ] || break; sleep 5; done
        """)

    def launch(self, blueprint_path: str, exp_name: str) -> str:
        user_command = self._build_user_command(blueprint_path)

        job_id = create_job(
            exp_name=exp_name or f"research-{os.path.abspath(blueprint_path)[-50:]}",
            n_nodes=config["pai_job_template"]["default_nodes"],
            priority=config["pai_job_template"]["default_priority"],
            region_id=config["alibaba_cloud"]["region_id"],
            workspace_id=config["alibaba_cloud"]["workspace_id"],
            clone_target=config["pai_job_template"]["clone_target"],
            clone_target_time_range=tuple(config["pai_job_template"]["clone_target_time_range"]),
            user_command=user_command,
        )
        return job_id

    def monitor(self, job_id: str) -> str:
        return wait_for_job(region_id=config["alibaba_cloud"]["region_id"], job_id=job_id)

    def stop(self, job_id: str) -> None:
        raise NotImplementedError("PAI job stop not yet implemented")


def run_blueprint():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--blueprint', type=str, required=True, help='Path to the blueprint to run')
    args = parser.parse_args()

    subagent = PaiExperimentSubagent()
    job_id = subagent.launch(blueprint_path=args.blueprint, exp_name="")
    print(f"Job submitted: {job_id}")


if __name__ == "__main__":
    run_blueprint()
