"""
Unified Claude Code agent runner — supports both leader and worker modes.

Equivalent of opencode_runner.py but uses the `claude` CLI (Claude Code) instead
of `opencode`.

Leader role:  Orchestrates research via a blueprint, manages a running_flag file.
Worker role:  Runs inside a PAI DLC node, checks tmux session liveness.
"""

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

from beast_logger import print_dict
from alpha_auto_research.utils.install_skills import install_skills
from alpha_auto_research.utils.claudecode_printer import format_stream_json_line


# ---------------------------------------------------------------------------
# Package paths
# ---------------------------------------------------------------------------

_PACKAGE_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Claude Code session helpers
# ---------------------------------------------------------------------------

def _build_env(skip_permissions: bool = False, extra: dict | None = None) -> dict:
    """Build environment dict for Claude Code subprocesses."""
    env = {**os.environ}
    # Remove CLAUDECODE to allow nesting inside a Claude Code session
    env.pop("CLAUDECODE", None)
    # Disable noisy features for programmatic use
    env.setdefault("DISABLE_TELEMETRY", "1")
    env.setdefault("DISABLE_AUTO_UPDATER", "1")
    env.setdefault("IS_SANDBOX", "1")
    if skip_permissions:
        env["CLAUDE_CODE_SKIP_PERMISSIONS"] = "1"
    if extra:
        env.update(extra)
    return env


def run_claudecode(
    session_name: str | None = None,
    prompt: str | None = None,
    continue_mode: bool = False,
    session_id: str | None = None,
    need_permission_error_fix: bool = False,
    resume_instruction: str = "",
    skip_permissions: bool = False,
    research_topic: str = "",
    model: str | None = None,
    max_turns: int | None = None,
) -> tuple[int, bool, str | None]:
    """Run claude CLI and return (returncode, terminated_due_to_permission, session_id).

    For new sessions, generates a UUID session_id upfront so it can be reused
    for resuming later.
    """

    env = _build_env(skip_permissions=skip_permissions)

    if continue_mode:
        assert session_name is None
        assert prompt is None
        assert session_id is not None

        msg = ""
        if resume_instruction:
            msg = f"Instruction: {resume_instruction}. "
        msg += "continue your job"
        if need_permission_error_fix:
            msg += ", permission error detected, please try some workaround, e.g. tmux command."

        cmd = [
            "claude",
            "-p",
            "--verbose",
            "--output-format", "stream-json",
            "--resume", session_id,
            msg,
        ]
    else:
        assert session_name is not None
        assert prompt is not None

        # Generate a deterministic session ID so we can resume later
        if session_id is None:
            session_id = str(uuid.uuid4())

        cmd = [
            "claude",
            "-p",
            "--verbose",
            "--output-format", "stream-json",
            "--session-id", session_id,
            "--name", session_name,
        ]
        if skip_permissions:
            cmd.append("--dangerously-skip-permissions")

    # Common flags
    if model:
        cmd.extend(["--model", model])
    if max_turns:
        cmd.extend(["--max-turns", str(max_turns)])

    # For new sessions, prompt goes at the end
    if not continue_mode:
        cmd.append(prompt)

    command_display = " ".join(cmd[:8]) + " ..." if len(cmd) > 8 else " ".join(cmd)
    print_dict(
        {
            "command": command_display,
            "continue_mode": continue_mode,
            "session_id": session_id,
            "research_topic": research_topic,
        },
        header="Launching claude",
    )

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    terminated_due_to_permission = False
    detected_session_id = session_id

    # Stream stdout (stream-json) and stderr
    for stream in (process.stdout, process.stderr):
        if stream:
            for line in stream:
                if not format_stream_json_line(line):
                    # Not JSON — print raw (stderr or non-json stdout)
                    print(line, end="")

                # Detect permission rejection
                if "rejected" in line.lower() and "permission" in line.lower():
                    print("[controller message]: Tool call was rejected by permission settings.")
                    terminated_due_to_permission = True

                # Try to capture session_id from stream-json events
                try:
                    event = json.loads(line.strip())
                    if isinstance(event, dict):
                        sid = event.get("session_id")
                        if sid and not detected_session_id:
                            detected_session_id = sid
                except (json.JSONDecodeError, ValueError):
                    pass

    process.wait()
    print(
        f"[controller message]: Return code: {process.returncode}, "
        f"permission_error={terminated_due_to_permission}"
    )
    return process.returncode, terminated_due_to_permission, detected_session_id


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _should_continue(terminated_due_to_permission: bool, running_flag: str) -> bool:
    if terminated_due_to_permission:
        print_dict(
            {"end reason": "[controller message]: Need Resume. Session terminated due to permission. Will attempt to continue."}
        )
        return True
    if os.path.exists(running_flag):
        print_dict({"end reason": "[controller message]: Need Resume."})
        return True
    else:
        print_dict(
            {"end reason": "[controller message]: Session terminated due to running_flag is gone. Looks like the agent has completed its task."}
        )
        return False


def _check_ssh_connectivity() -> None:
    """Verify SSH connectivity to all configured hosts before starting."""
    from alpha_auto_research.config import config
    from alpha_auto_research.blueprint_runner.ssh_runner import _run_cmd

    hosts = config.get("ssh", {}).get("hosts", [])
    if not hosts:
        print("[controller message]: WARNING: runner is 'ssh' but no hosts configured.")
        return
    for host_cfg in hosts:
        label = f"{host_cfg.get('user', 'root')}@{host_cfg['host']}:{host_cfg.get('port', 22)}"
        print(f"[controller message]: Checking SSH connectivity to {label} ...")
        result = _run_cmd(host_cfg, "echo ok")
        if result.returncode != 0:
            print(f"[controller message]: ERROR: SSH connection to {label} failed!")
            print(f"  stdout: {result.stdout.strip()}")
            print(f"  stderr: {result.stderr.strip()}")
            sys.exit(1)
        print(f"[controller message]: SSH connection to {label} OK.")


# ---------------------------------------------------------------------------
# Main run logic
# ---------------------------------------------------------------------------

def run(
    research_topic: str = "",
    blueprint: str = "",
    role: str = "",
    resume_session_id: str = "",
    resume_instruction: str = "",
    only_run_planning: bool = False,
    skip_permissions: bool = False,
    no_human_in_the_loop: bool = False,
    runner: str = "ssh",
    model: str | None = None,
    max_turns: int | None = None,
) -> int:

    install_skills()

    session_name = f"research_topic_{research_topic}_role_{role}_blueprint_{blueprint}"
    session_name = session_name.replace(" ", "_")

    if runner == "ssh":
        _check_ssh_connectivity()

    if only_run_planning:
        assert role == "leader", "only_run_planning is only applicable for leader role"

    if no_human_in_the_loop:
        assert role == "leader", "--no-human-in-the-loop is only applicable for leader role"
        assert not only_run_planning, "--no-human-in-the-loop conflicts with --only-run-planning"
        assert not resume_session_id, "--no-human-in-the-loop conflicts with --resume"
        assert not resume_instruction, "--no-human-in-the-loop conflicts with --resume-instruction"

    # ---- Build prompt ----
    if role == "leader":
        if no_human_in_the_loop:
            leader_skill_path = str(_PACKAGE_DIR / "skills" / "leader_experiment_no_human" / "SKILL.md")
        else:
            leader_skill_path = str(_PACKAGE_DIR / "skills" / "leader_experiment" / "SKILL.md")
        assert os.path.exists(leader_skill_path), f"skill not found: {leader_skill_path}"

        if os.path.exists(research_topic):
            running_flag = research_topic + ".running_flag"
            with open(research_topic, "r") as f:
                research_topic_text = f"Research topic:\n{f.read()}"
        else:
            running_flag = leader_skill_path + ".running_flag"
            research_topic_text = ""

        with open(running_flag, "w+") as f:
            f.write("Running")

        with open(leader_skill_path, "r") as f:
            skill_content = f.read()

        prompt = (
            "You are the main research agent, the research lead, responsible for designing, evaluating, and dispatching research plans.\n"
            f"current runner is **{runner}** runner.\n"
            f"---\n"
            f"Experiment skill:"
            f"---\n"
            f"{skill_content}\n"
            f"---\n"
            f"After all experiments are complete and the final report is written, please delete {running_flag}\n"
            f"{research_topic_text}\n"
            f"---\n"
            f"resume_instruction:\n"
            f"{resume_instruction}\n"
            f"---\n"
        )

        if only_run_planning:
            prompt += "---\n"
            prompt += "Additionally:\n"
            prompt += "The user wishes to only generate the research plan or report and exit without running the experiments.\n"

    elif role == "worker":
        worker_skill_path = str(_PACKAGE_DIR / "skills" / "worker_experiment" / "SKILL.md")
        worker_blueprint_path = os.path.abspath(blueprint)
        assert os.path.exists(worker_skill_path), f"skill not found: {worker_skill_path}"
        assert os.path.exists(worker_blueprint_path), f"blueprint not found: {worker_blueprint_path}"
        running_flag = worker_blueprint_path + ".running_flag"

        with open(running_flag, "w+") as f:
            f.write("Running")

        prompt = (
            f"Your task is to follow the instructions in {worker_skill_path} and complete the experiment described in blueprint {worker_blueprint_path}.\n"
            f"After the experiment is finally complete, please delete {running_flag}.\n"
            f"Current runner is **{runner}** runner.\n"
            f"Try everything you can to make the experiment running until reaching the time limit or completing the goal written in the blueprint.\n"
        )
    else:
        raise ValueError(f"Unknown role: {role}")

    if runner == "ssh":
        prompt += "---\n"
        prompt += "Special warning: to run multiple experiments in parallel in same server, you need to arrange CUDA_VISIBLE_DEVICES for each experiment in experiment blueprint.\n"

    # ---- First run or resume ----
    print("[controller message]: run claude 1st ...")
    session_id = None

    if resume_session_id:
        # Resume an existing session
        session_id = resume_session_id
        terminated_due_to_permission = False
        print_dict({"session_id": session_id}, header="Resuming session")
    else:
        returncode, terminated_due_to_permission, session_id = run_claudecode(
            session_name=session_name,
            prompt=prompt,
            continue_mode=False,
            session_id=None,
            need_permission_error_fix=False,
            resume_instruction="",
            skip_permissions=skip_permissions,
            research_topic=research_topic,
            model=model,
            max_turns=max_turns,
        )
        print(f"[controller message]: Session ID from first run: {session_id}")
        if only_run_planning:
            print_dict(
                {"end reason": "[controller message]: planning role, waiting user feedback."}
            )
            return returncode

    # ---- Continue loop ----
    while _should_continue(terminated_due_to_permission, running_flag):
        print("[controller message]: Continuing session ...")
        if session_id:
            returncode, terminated_due_to_permission, _ = run_claudecode(
                session_name=None,
                prompt=None,
                continue_mode=True,
                session_id=session_id,
                need_permission_error_fix=terminated_due_to_permission,
                resume_instruction=resume_instruction,
                skip_permissions=skip_permissions,
                research_topic=research_topic,
                model=model,
                max_turns=max_turns,
            )
            resume_instruction = ""  # only apply once
            if only_run_planning:
                print_dict(
                    {"end reason": "[controller message]: planning role, waiting user feedback."}
                )
                return returncode
        else:
            raise RuntimeError("No session ID available to continue.")

        print_dict({"end reason": "[controller message]: wait a few seconds before next round."})
        time.sleep(60)

    if role == "worker":
        still_training = "/still_training"
        if os.path.exists(still_training):
            os.remove(still_training)

    print("[controller message]: finished.")
    return returncode


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(prog="claudecode_runner")
    subparsers = parser.add_subparsers(dest="role", required=True)

    for sp_name in ("leader", "worker"):
        sp = subparsers.add_parser(sp_name)
        sp.add_argument("--research-topic", default="", help="Research topic or path to topic file")
        sp.add_argument("--runner", required=True, choices=["ssh", "pai"], help="Use ssh or pai (Alibaba Cloud)")
        sp.add_argument("--blueprint", default="", help="Path to blueprint .md file")
        sp.add_argument(
            "--resume", "--resume-session-id",
            default="",
            dest="resume_session_id",
            help="Resume a session by its UUID",
        )
        sp.add_argument("--resume-instruction", default="", help="Instruction for resuming")
        sp.add_argument("--only-run-planning", action="store_true", help="Run planning only and exit")
        sp.add_argument("--skip-permissions", action="store_true", help="Skip all permission checks (use --dangerously-skip-permissions)")
        sp.add_argument("--model", default=None, help="Model to use (e.g. sonnet, opus, claude-sonnet-4-6)")
        sp.add_argument("--max-turns", type=int, default=None, help="Maximum agentic turns")
        if sp_name == "leader":
            sp.add_argument(
                "--no-human-in-the-loop",
                action="store_true",
                help="Run fully autonomous without human review",
            )

    args = parser.parse_args()

    rc = run(
        research_topic=args.research_topic,
        blueprint=args.blueprint,
        role=args.role,
        resume_session_id=args.resume_session_id,
        resume_instruction=args.resume_instruction,
        only_run_planning=args.only_run_planning,
        skip_permissions=args.skip_permissions,
        no_human_in_the_loop=getattr(args, "no_human_in_the_loop", False),
        runner=args.runner,
        model=args.model,
        max_turns=args.max_turns,
    )
    sys.exit(rc)


if __name__ == "__main__":
    main()
