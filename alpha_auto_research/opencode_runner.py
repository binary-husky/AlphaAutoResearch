"""
Unified OpenCode agent runner — supports both leader and worker modes.

Leader role:  Orchestrates research via a blueprint, manages a running_flag file.
Worker role:  Runs inside a PAI DLC node, checks tmux session liveness.

"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from beast_logger import print_dict


_PACKAGE_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _parse_sessions_json(stdout: str) -> list[dict]:
    """Parse session list JSON, tolerating truncated output."""
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        # Output may be truncated for large session lists — try to salvage
        # by finding the last complete object (ends with '}')
        last_brace = stdout.rfind("}")
        if last_brace == -1:
            return []
        try:
            return json.loads(stdout[:last_brace + 1] + "\n]")
        except json.JSONDecodeError:
            return []


def _get_opencode_sessions() -> dict[str, str]:
    """Return a dict mapping session ID -> title for all current opencode sessions."""
    result = subprocess.run(
        ["opencode", "session", "list", "--format=json"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return {}
    sessions = _parse_sessions_json(result.stdout)
    return {s["id"]: s.get("title", "") for s in sessions}


def _get_opencode_session_from_title(title="") -> tuple[str, str] | None:
    """Return (id, title) of the most recently updated session with the given title, or None."""
    result = subprocess.run(
        ["opencode", "session", "list", "--format=json"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None
    sessions = _parse_sessions_json(result.stdout)
    if not sessions:
        return None
    filtered_sessions = [s for s in sessions if s.get("title", "") == title]
    if not filtered_sessions:
        return None
    latest = max(filtered_sessions, key=lambda s: s["updated"])
    return latest["id"], latest.get("title", "")


def _delete_opencode_session_from_title(title="") -> None:
    """Delete all sessions with the given title."""
    sessions = _get_opencode_sessions()
    for session_id, session_title in sessions.items():
        if session_title == title:
            subprocess.run(["opencode", "session", "delete", session_id])


def _prepare_yolo_config():
    """Copy opencode.json to opencode-yolo.json with permissive permissions."""
    config_dir = os.path.expanduser("~/.config/opencode")
    src = os.path.join(config_dir, "opencode.json")
    dst = os.path.join(config_dir, "opencode-yolo.json")

    if os.path.exists(src):
        with open(src, "r") as f:
            config = json.load(f)
    else:
        config = {"$schema": "https://opencode.ai/config.json"}

    config["permission"] = {"*": {"*": "allow"}}

    os.makedirs(config_dir, exist_ok=True)
    with open(dst, "w") as f:
        json.dump(config, f, indent=2)

    return dst


def run_opencode(args: list[str], *, continue_mode=False, session_id=None,
                 need_permission_error_fix=False, resume_instruction="",
                 skip_permissions=False, research_topic="") -> tuple[int, bool, str | None]:
    """Run opencode and return (returncode, terminated_due_to_permission, session_id).

    When starting a new session (not continue_mode), detects the newly created
    session ID right after the process spawns so it can be reused for resuming.
    """
    cmd = ["opencode"] + args

    if continue_mode:
        cmd = cmd[:-1]  # drop the original prompt

        if resume_instruction:
            msg = f"Instruction: {resume_instruction}"
        else:
            msg = "continue your job"

        if need_permission_error_fix:
            msg += ", permission error detected, please try some workaround, e.g. tmux command."
        cmd += ["-c", session_id, msg]

    env = None
    if skip_permissions:
        yolo_config = _prepare_yolo_config()
        env = {**os.environ, "OPENCODE_CONFIG": yolo_config}

    # Snapshot existing sessions before spawning so we can detect the new one
    existing_sessions = _get_opencode_sessions() if not continue_mode else {}

    command = " ".join(cmd)
    print_dict({"command": command, "continue_mode": continue_mode, "session_id": session_id, "research_topic": research_topic}, header="Launching opencode")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)

    # Detect new session ID right after spawn (only for new sessions)
    detected_session_id = session_id  # keep existing for continue_mode
    if not continue_mode:
        for _ in range(30):  # poll for up to 30 seconds
            print("[controller message]: detecting new session ID...")
            time.sleep(1)
            current_sessions = _get_opencode_sessions()
            new_session_ids = set(current_sessions) - set(existing_sessions)

            if new_session_ids:
                detected_session_id = new_session_ids.pop()
                title = current_sessions[detected_session_id]
                print_dict({"session_id": detected_session_id, "title": title, "command": command}, header="Created new session")
                break
        else:
            raise RuntimeError("Failed to detect new opencode session ID after 30s. Aborting.")
    else:
        current_sessions = _get_opencode_sessions()
        title = current_sessions[session_id]
        print_dict({"session_id": session_id, "title": title, "command": command}, header="Resume old session")


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
    return process.returncode, terminated_due_to_permission, detected_session_id


def _ensure_opencode_web(skip_permissions=False, role="leader"):
    from alpha_auto_research.utils.smart_daemon import LaunchCommandWhenAbsent

    env_dict = {**os.environ}
    if skip_permissions:
        yolo_config = _prepare_yolo_config()
        env_dict["OPENCODE_CONFIG"] = yolo_config

    print("[controller message]: Starting opencode web...")
    opencode_web = LaunchCommandWhenAbsent(
        full_argument_list=["opencode web"],
        tag="opencode_web_service",
        use_pty=True,
    )
    opencode_web.launch(
        launch_wait_time=10,
        success_std_string="Web interface",
        env_dict=env_dict,
    )

    # Start kite-client for remote monitoring if configured
    from alpha_auto_research.config import config
    remote_cfg = config.get("remote_monitor", {})
    remote_url = remote_cfg.get("remote_url")
    api_key = remote_cfg.get("api_key")
    if remote_url and api_key:
        print(f"[controller message]: Starting kite-client -> {remote_url}")
        command = ["kite-client", "--server", remote_url, "--apikey", api_key, "--map", f"4096:opencode_web_{role}"]
        command_str = " ".join(command)
        kite = LaunchCommandWhenAbsent(
            full_argument_list=[command_str],
            tag="kite_client_service",
            use_pty=True,
        )
        kite.launch(
            launch_wait_time=20,
            success_std_string="forwarding_success",
            env_dict=env_dict,
        )
        print("[controller message]: kite-client started for remote monitoring.")
    else:
        print("[controller message]: remote_monitor config not found, skipping kite-client startup.")


# ---------------------------------------------------------------------------
# Leader role
# ---------------------------------------------------------------------------

def _should_continue(terminated_due_to_permission: bool, running_flag: str) -> bool:
    if terminated_due_to_permission:
        print_dict({"end reason": "[controller message]: Need Resume. Session terminated due to permission. Will attempt to continue."})
        return True
    if os.path.exists(running_flag):
        print_dict({"end reason": "[controller message]: Need Resume."})
        return True
    else:
        print_dict({"end reason": "[controller message]: Session terminated due to running_flag is gone. Looks like the agent has completed its task."})
        return False


def _check_ssh_connectivity() -> None:
    """Verify SSH connectivity to all configured hosts before starting. Exits on failure."""
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


def run(research_topic: str = "", blueprint:str="", role: str = "",
        resume_latest_session: bool = False, resume_instruction: str = "",
        only_run_planning: bool = False, skip_permissions: bool = False,
        no_human_in_the_loop: bool = False, runner: str = "ssh") -> int:

    session_title = f"research_topic {research_topic} role {role} blueprint {blueprint}"
    session_title = session_title.replace(" ", "_")  # avoid issues with spaces in title

    if runner == "ssh":
        _check_ssh_connectivity()

    if only_run_planning:
        assert role == "leader", "only_run_planning role is only applicable for leader role"

    if no_human_in_the_loop:
        assert role == "leader", "--no-human-in-the-loop is only applicable for leader role"
        assert not only_run_planning, "--no-human-in-the-loop conflicts with --only-run-planning"
        assert not resume_latest_session, "--no-human-in-the-loop conflicts with --resume"
        assert not resume_instruction, "--no-human-in-the-loop conflicts with --resume-instruction"

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

        prompt = (
            "You are the main research agent, the research lead, responsible for designing, evaluating, and dispatching research plans.\n"
            f"Experiment skill: {leader_skill_path}, current runner is **{runner}** runner.\n"
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

    from alpha_auto_research.config import config
    if runner == "ssh":
        prompt += "---\n"
        prompt += "Special warning: to run multiple experiments in parallel in same server, you need to arrange CUDA_VISIBLE_DEVICES for each experiment in experiment blueprint.\n"



    _ensure_opencode_web(skip_permissions=skip_permissions, role=role)
    run_args = ["run", "--title", session_title, f"--attach=http://localhost:4096", prompt]

    print("[controller message]: run opencode 1st ...")
    session_id = None
    if resume_latest_session:
        terminated_due_to_permission = False
        latest = _get_opencode_session_from_title(title=session_title)
        if latest:
            session_id, title = latest
            print_dict({"session_id": session_id, "title": title}, header="Resuming latest session")
        else:
            raise RuntimeError("No opencode session found to resume.")
    else:
        # delete existing session with the same title to avoid confusion
        _delete_opencode_session_from_title(title=session_title)
        returncode, terminated_due_to_permission, session_id = run_opencode(run_args, skip_permissions=skip_permissions, research_topic=research_topic)
        print(f"[controller message]: Session ID from first run: {session_id}")
        if only_run_planning:
            print_dict({"end reason": "[controller message]: planning role, waiting user feedback (alpha-rl-resume-planning or alpha-rl-begin-experiments)."})
            return returncode


    # begin opencode agent
    while _should_continue(terminated_due_to_permission, running_flag):
        print("[controller message]: Continuing session ...")
        if session_id:
            returncode, terminated_due_to_permission, _ = run_opencode(
                run_args,
                continue_mode=True,
                session_id=session_id,
                need_permission_error_fix=terminated_due_to_permission,
                resume_instruction=resume_instruction,
                skip_permissions=skip_permissions,
                research_topic=research_topic,
            )
            resume_instruction = ""  # only apply the resume_instruction for one time
            if only_run_planning:
                print_dict({"end reason": "[controller message]: planning role, waiting user feedback (alpha-rl-resume-planning or alpha-rl-begin-experiments)."})
                return returncode
        else:
            raise RuntimeError("No session ID detected to continue.")

        print_dict({"end reason": "[controller message]: wait a few seconds before next round."})
        time.sleep(60)  # wait a bit before checking the session status again

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
    parser = argparse.ArgumentParser(prog="opencode_runner")
    subparsers = parser.add_subparsers(dest="role", required=True)
    from alpha_auto_research.config import config
    # Common arguments
    for sp_name in ("leader", "worker"):
        sp = subparsers.add_parser(sp_name)
        sp.add_argument("--research-topic", default="", help="Extra instruction")
        sp.add_argument("--runner", required=True, choices=["ssh", "pai"], help="use ssh, or pai (alibaba cloud platform)")
        sp.add_argument("--blueprint", default="", help="Path to research skill .md")
        sp.add_argument("--resume", "--resume-latest-session", action="store_true", dest="resume_latest_session", help="Resume the latest session")
        sp.add_argument("--resume-instruction", default="", help="Instruction for resuming")
        sp.add_argument("--only-run-planning", action="store_true", help="Run once and exit")
        sp.add_argument("--skip-permissions", action="store_true", help="Use permissive opencode config (allow all tools)")
        if sp_name == "leader":
            sp.add_argument("--no-human-in-the-loop", action="store_true", help="Run fully autonomous without human review (uses no_human skill)")
    args = parser.parse_args()

    rc = run(
        research_topic=args.research_topic,
        blueprint=args.blueprint,
        role=args.role,
        resume_latest_session=args.resume_latest_session,
        resume_instruction=args.resume_instruction,
        only_run_planning=args.only_run_planning,
        skip_permissions=args.skip_permissions,
        no_human_in_the_loop=getattr(args, "no_human_in_the_loop", False),
        runner=args.runner,
    )
    sys.exit(rc)


if __name__ == "__main__":
    main()
