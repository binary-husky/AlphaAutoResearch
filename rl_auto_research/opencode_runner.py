"""
Unified OpenCode agent runner — supports both leader and worker modes.

Leader mode:  Orchestrates research via a blueprint, manages a running_flag file.
Worker mode:  Runs inside a PAI DLC node, checks tmux session liveness.

Usage:
    python -m rl_auto_research.opencode_runner leader \
        --attach=http://localhost:4096 \
        --blueprint=/path/to/blueprint.md \
        --additional-prompt="..."

    python -m rl_auto_research.opencode_runner worker \
        <opencode args...>
"""

import argparse
import json
import os
import subprocess
import sys
import time


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _get_latest_opencode_session_id() -> str | None:
    result = subprocess.run(
        ["opencode", "session", "list", "--format=json"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None
    sessions = json.loads(result.stdout)
    if not sessions:
        return None
    latest = max(sessions, key=lambda s: s["updated"])
    return latest["id"]


def run_opencode(args: list[str], *, continue_mode=False, session_id=None,
                 need_permission_error_fix=False) -> tuple[int, bool]:
    cmd = ["opencode"] + args

    if continue_mode:
        cmd = cmd[:-1]  # drop the original prompt
        msg = "continue your job"
        if need_permission_error_fix:
            msg += ", permission error detected, please try some workaround, e.g. tmux command."
        cmd += ["-c", session_id, msg]

    print("[controller message]: executing", " ".join(cmd))
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    terminated_due_to_permission = False
    for stream in (process.stdout, process.stderr):
        if stream:
            for line in stream:
                print(line, end="")
                if "The user rejected permission to use this specific tool call" in line:
                    print("[controller message]: Tool call was rejected by permission settings.")
                    terminated_due_to_permission = True

    process.wait()
    print(f"[controller message]: Return code: {process.returncode}, permission_error={terminated_due_to_permission}")
    return process.returncode, terminated_due_to_permission


def _is_opencode_web_running() -> bool:
    result = subprocess.run(["pgrep", "-f", "opencode web"], capture_output=True, text=True)
    return result.returncode == 0


def _ensure_opencode_web():
    if not _is_opencode_web_running():
        print("[controller message]: Starting opencode web...")
        subprocess.Popen(["opencode", "web"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)


# ---------------------------------------------------------------------------
# Leader mode
# ---------------------------------------------------------------------------

def _should_continue(terminated_due_to_permission: bool, running_flag: str) -> bool:
    if terminated_due_to_permission:
        print("[controller message]: Session terminated due to permission. Will attempt to continue.")
        return True
    if os.path.exists(running_flag):
        return True
    else:
        return False


def run(research_topic: str = "", blueprint:str="", mod: str = ""):

    if mod == "leader":
        leader_skill_path = "skills/leader_experiment.md"
        leader_skill_path = os.path.abspath(leader_skill_path)
        assert os.path.exists(leader_skill_path), f"skill not found: {leader_skill_path}"
        running_flag = leader_skill_path + ".running_flag"

        with open(running_flag, "w+") as f:
            f.write("Running")

        prompt = (
            "You are the main research agent, the research lead, responsible for designing, evaluating, and dispatching research plans.\n"
            f"Experiment skill: {leader_skill_path}\n"
            f"After all experiments are complete and the final report is written, please delete {running_flag}\n"
            f"{research_topic}\n"
        )

    elif mod == "worker":
        worker_skill_path = "skills/worker_experiment.md"
        worker_skill_path = os.path.abspath(worker_skill_path)
        assert os.path.exists(worker_skill_path), f"skill not found: {worker_skill_path}"
        running_flag = worker_skill_path + ".running_flag"

        with open(running_flag, "w+") as f:
            f.write("Running")

        prompt = (
            f"Your task is to follow the instructions in {worker_skill_path} and complete the experiment described in blueprint {blueprint}.\n"
            f"After the experiment is finally complete, please delete {running_flag}.\n"
            f"Try everything you can to make the experiment running until reaching the time limit or completing the goal written in the blueprint.\n"
        )

    _ensure_opencode_web()
    run_args = ["run", f"--attach=http://localhost:4096", prompt]

    print("[controller message]: run opencode 1st ...")
    returncode, terminated_due_to_permission = run_opencode(run_args)

    # begin opencode agent
    while _should_continue(terminated_due_to_permission, running_flag):
        print("[controller message]: Continuing session ...")
        session_id = _get_latest_opencode_session_id()
        if session_id:
            returncode, terminated_due_to_permission = run_opencode(
                run_args, continue_mode=True, session_id=session_id,
                need_permission_error_fix=terminated_due_to_permission,
            )

    if mod == "worker":
        still_training = "/still_training"
        if os.path.exists(still_training):
            os.remove(still_training)

    print("[controller message]: finished.")
    return returncode



# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(prog="opencode_runner")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # Leader
    lp = subparsers.add_parser("leader")
    lp.add_argument("--research-topic", default="", help="Extra instruction")

    # Worker
    wp = subparsers.add_parser("worker")
    wp.add_argument("--blueprint", default="", help="Path to research skill .md")
    args = parser.parse_args()

    rc = run(args.research_topic, args.blueprint, args.mode)
    sys.exit(rc)


if __name__ == "__main__":
    main()
