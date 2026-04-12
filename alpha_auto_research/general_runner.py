"""
General-purpose agent runner — supports both Claude Code and OpenCode backends,
and both leader and worker modes.

This module extracts the common orchestration logic (prompt building, resume
loop, SSH checks) into a shared ``run()`` function, while backend-specific
behaviour (session lookup, CLI invocation, output parsing) is encapsulated in
``ClaudeCodeCli`` and ``OpenCodeCli``, both subclasses of ``CodeAgentCli``.
"""

from __future__ import annotations

import abc
import argparse
import json
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from beast_logger import print_dict
from alpha_auto_research.utils.install_skills import install_skills

# ---------------------------------------------------------------------------
# Package paths
# ---------------------------------------------------------------------------

_PACKAGE_DIR = Path(__file__).resolve().parent


# ===================================================================
# Abstract base class
# ===================================================================

class CodeAgentCli(abc.ABC):
    """Thin abstraction over an AI-coding CLI (Claude Code, OpenCode, …)."""

    # -- identity ----------------------------------------------------------

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable backend name (e.g. ``"claude"``, ``"opencode"``)."""

    # -- session discovery -------------------------------------------------

    @abc.abstractmethod
    def find_session(self, session_name: str) -> str | None:
        """Return the session ID for the latest session whose name / title
        matches *session_name*, or ``None`` if no match is found."""

    @abc.abstractmethod
    def delete_sessions(self, session_name: str) -> None:
        """Delete all sessions whose name / title matches *session_name*."""

    # -- pre-run setup -----------------------------------------------------

    def setup(self, *, skip_permissions: bool = False, role: str = "leader") -> None:
        """Optional one-time setup before the first run (e.g. start a web UI).

        The default implementation is a no-op.
        """

    # -- run ---------------------------------------------------------------

    @abc.abstractmethod
    def run(
        self,
        *,
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
        """Run the underlying CLI and return
        ``(returncode, terminated_due_to_permission, session_id)``.
        """


# ===================================================================
# Claude Code backend
# ===================================================================

class ClaudeCodeCli(CodeAgentCli):

    _RESEARCH_CLAUDECODE_JSON = Path.cwd() / "research_claudecode.json"

    @property
    def name(self) -> str:
        return "claude"

    # -- config ------------------------------------------------------------

    def _load_config(self) -> dict:
        """Load research_claudecode.json from current working directory."""
        if not self._RESEARCH_CLAUDECODE_JSON.exists():
            raise FileNotFoundError(
                f"research_claudecode.json not found in cwd ({Path.cwd()}). "
                "Please create it (see research_claudecode.example.json for reference)."
            )
        with open(self._RESEARCH_CLAUDECODE_JSON, "r") as f:
            return json.load(f)

    # -- setup -------------------------------------------------------------

    def setup(self, *, skip_permissions: bool = False, role: str = "leader") -> None:
        config = self._load_config()
        print_dict(
            {"config": str(self._RESEARCH_CLAUDECODE_JSON)},
            header="Loaded research_claudecode.json",
        )

        # 1. Set env vars for MiniMax API (Anthropic-compatible endpoint)
        api_base = config.get("apiBaseUrl", "")
        api_key = config.get("apiKey", "")
        if api_base:
            os.environ["ANTHROPIC_BASE_URL"] = api_base
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
        # Clear conflicting Anthropic auth so Claude Code uses our key
        os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)

        print_dict(
            {"ANTHROPIC_BASE_URL": api_base, "ANTHROPIC_API_KEY": api_key[:12] + "..." if api_key else ""},
            header="API environment",
        )

        # 2. Write .claude/settings.local.json (project-local, gitignored)
        dot_claude = Path.cwd() / ".claude"
        dot_claude.mkdir(exist_ok=True)
        settings_local_path = dot_claude / "settings.local.json"

        settings_local: dict = {}
        if settings_local_path.exists():
            try:
                with open(settings_local_path, "r") as f:
                    settings_local = json.load(f)
            except (json.JSONDecodeError, OSError):
                settings_local = {}

        # Model
        model_name = config.get("model", "")
        if model_name:
            settings_local["model"] = model_name

        # Permissions — bypassPermissions when skip_permissions requested
        if skip_permissions:
            settings_local.setdefault("permissions", {})
            settings_local["permissions"]["defaultMode"] = "bypassPermissions"

        # API env vars in settings (belt-and-suspenders alongside os.environ)
        settings_local.setdefault("env", {})
        if api_base:
            settings_local["env"]["ANTHROPIC_BASE_URL"] = api_base
        if api_key:
            settings_local["env"]["ANTHROPIC_API_KEY"] = api_key

        with open(settings_local_path, "w") as f:
            json.dump(settings_local, f, indent=2)
        print_dict(
            {"path": str(settings_local_path), "model": model_name,
             "permissions": settings_local.get("permissions", {}).get("defaultMode", "default")},
            header="Wrote .claude/settings.local.json",
        )

        # 3. Ensure ~/.claude.json has hasCompletedOnboarding (skip first-run wizard)
        claude_dot_json = Path.home() / ".claude.json"
        dot_config: dict = {}
        if claude_dot_json.exists():
            try:
                with open(claude_dot_json, "r") as f:
                    dot_config = json.load(f)
            except (json.JSONDecodeError, OSError):
                dot_config = {}
        if not dot_config.get("hasCompletedOnboarding"):
            dot_config["hasCompletedOnboarding"] = True
            with open(claude_dot_json, "w") as f:
                json.dump(dot_config, f, indent=2)
            print_dict({"path": str(claude_dot_json)}, header="Set hasCompletedOnboarding")

        # 4. Ensure .claude/ is in .gitignore (settings.local.json should not be committed)
        gitignore_path = Path.cwd() / ".gitignore"
        if gitignore_path.exists():
            gitignore_content = gitignore_path.read_text()
            if ".claude/settings.local.json" not in gitignore_content:
                with open(gitignore_path, "a") as f:
                    f.write("\n# Claude Code local settings (auto-generated)\n.claude/settings.local.json\n")

    # -- session helpers ---------------------------------------------------

    @staticmethod
    def _project_dir() -> Path:
        cwd = os.getcwd()
        encoded = re.sub(r"[^a-zA-Z0-9]", "-", cwd)
        return Path.home() / ".claude" / "projects" / encoded

    def find_session(self, session_name: str) -> str | None:
        project_dir = self._project_dir()
        if not project_dir.is_dir():
            return None

        matches: list[tuple[float, str]] = []
        for jsonl_path in project_dir.glob("*.jsonl"):
            session_id = jsonl_path.stem
            try:
                with open(jsonl_path, "r") as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if (
                            entry.get("type") == "custom-title"
                            and entry.get("customTitle") == session_name
                        ):
                            mtime = jsonl_path.stat().st_mtime
                            matches.append((mtime, session_id))
                            break
            except OSError:
                continue

        if not matches:
            return None
        matches.sort(reverse=True)
        return matches[0][1]

    def delete_sessions(self, session_name: str) -> None:
        # Claude Code doesn't have a CLI delete command; silently skip.
        pass

    # -- env ---------------------------------------------------------------

    @staticmethod
    def _build_env(skip_permissions: bool = False) -> dict[str, str]:
        env = {**os.environ}
        env.pop("CLAUDECODE", None)
        env.setdefault("DISABLE_TELEMETRY", "1")
        env.setdefault("DISABLE_AUTO_UPDATER", "1")
        env.setdefault("IS_SANDBOX", "1")
        if skip_permissions:
            env["CLAUDE_CODE_SKIP_PERMISSIONS"] = "1"
        return env

    # -- run ---------------------------------------------------------------

    def run(
        self,
        *,
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
        from alpha_auto_research.utils.claudecode_printer import format_stream_json_line

        env = self._build_env(skip_permissions=skip_permissions)

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
                "claude", "-p", "--verbose",
                "--output-format", "stream-json",
                "--resume", session_id,
                msg,
            ]
        else:
            assert session_name is not None
            assert prompt is not None

            if session_id is None:
                session_id = str(uuid.uuid4())

            cmd = [
                "claude", "-p", "--verbose",
                "--output-format", "stream-json",
                "--session-id", session_id,
                "--name", session_name,
            ]
            if skip_permissions:
                cmd.append("--dangerously-skip-permissions")

        if model:
            cmd.extend(["--model", model])
        if max_turns:
            cmd.extend(["--max-turns", str(max_turns)])
        if not continue_mode:
            cmd.append(prompt)

        command_display = " ".join(cmd[:8]) + " ..." if len(cmd) > 8 else " ".join(cmd)
        print_dict(
            {"command": command_display, "continue_mode": continue_mode,
             "session_id": session_id, "research_topic": research_topic},
            header="Launching claude",
        )

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)

        terminated_due_to_permission = False
        detected_session_id = session_id

        for stream in (process.stdout, process.stderr):
            if stream:
                for line in stream:
                    if not format_stream_json_line(line):
                        print(line, end="")
                    if "rejected" in line.lower() and "permission" in line.lower():
                        print("[controller message]: Tool call was rejected by permission settings.")
                        terminated_due_to_permission = True
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


# ===================================================================
# OpenCode backend
# ===================================================================

class OpenCodeCli(CodeAgentCli):

    _RESEARCH_OPENCODE_JSON = Path.cwd() / "research_opencode.json"

    @property
    def name(self) -> str:
        return "opencode"

    # -- opencode config ---------------------------------------------------

    def _get_config_path(self, skip_permissions: bool = False) -> str:
        if not skip_permissions:
            return str(self._RESEARCH_OPENCODE_JSON)
        dst = Path.cwd() / "research_opencode.yolo.json"
        with open(self._RESEARCH_OPENCODE_JSON, "r") as f:
            config = json.load(f)
        config["permission"] = {"*": {"*": "allow"}}
        with open(dst, "w") as f:
            json.dump(config, f, indent=2)
        return str(dst)

    def _load_config(self) -> None:
        if not self._RESEARCH_OPENCODE_JSON.exists():
            raise FileNotFoundError(
                f"research_opencode.json not found in cwd ({Path.cwd()}). "
                "Please create it (see research_opencode.example.json for reference)."
            )
        os.environ["OPENCODE_CONFIG"] = str(self._RESEARCH_OPENCODE_JSON)
        print_dict({"OPENCODE_CONFIG": str(self._RESEARCH_OPENCODE_JSON)},
                   header="Loaded research_opencode.json")

    # -- session helpers ---------------------------------------------------

    @staticmethod
    def _parse_sessions_json(stdout: str) -> list[dict]:
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            last_brace = stdout.rfind("}")
            if last_brace == -1:
                return []
            try:
                return json.loads(stdout[: last_brace + 1] + "\n]")
            except json.JSONDecodeError:
                return []

    def _list_sessions(self) -> dict[str, str]:
        result = subprocess.run(
            ["opencode", "session", "list", "--format=json"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            return {}
        sessions = self._parse_sessions_json(result.stdout)
        return {s["id"]: s.get("title", "") for s in sessions}

    def find_session(self, session_name: str) -> str | None:
        result = subprocess.run(
            ["opencode", "session", "list", "--format=json"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            return None
        sessions = self._parse_sessions_json(result.stdout)
        if not sessions:
            return None
        filtered = [s for s in sessions if s.get("title", "") == session_name]
        if not filtered:
            return None
        latest = max(filtered, key=lambda s: s["updated"])
        return latest["id"]

    def delete_sessions(self, session_name: str) -> None:
        sessions = self._list_sessions()
        for session_id, title in sessions.items():
            if title == session_name:
                subprocess.run(["opencode", "session", "delete", session_id])

    # -- setup -------------------------------------------------------------

    def setup(self, *, skip_permissions: bool = False, role: str = "leader") -> None:
        self._load_config()

        from alpha_auto_research.utils.smart_daemon import LaunchCommandWhenAbsent

        env_dict = {**os.environ, "OPENCODE_CONFIG": self._get_config_path(skip_permissions)}

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

        from alpha_auto_research.config import config
        remote_cfg = config.get("remote_monitor", {})
        remote_url = remote_cfg.get("remote_url")
        api_key = remote_cfg.get("api_key")
        if remote_url and api_key:
            print(f"[controller message]: Starting kite-client -> {remote_url}")
            command_str = f"kite-client --server {remote_url} --apikey {api_key} --map 4096:opencode_web_{role}"
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

    # -- run ---------------------------------------------------------------

    def run(
        self,
        *,
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
        from alpha_auto_research.utils.opencode_printer import format_json_line

        if continue_mode:
            assert session_name is None
            assert prompt is None
            assert session_id is not None

            if resume_instruction:
                msg = f"Instruction: {resume_instruction}"
            else:
                msg = "continue your job"
            if need_permission_error_fix:
                msg += ", permission error detected, please try some workaround, e.g. tmux command."

            cmd = ["opencode", "run", "--session", session_id, msg]
        else:
            assert session_name is not None
            assert prompt is not None
            cmd = ["opencode", "run", "--format", "json", "--title", session_name,
                   "--attach", "http://localhost:4096", prompt]

        env = {**os.environ, "OPENCODE_CONFIG": self._get_config_path(skip_permissions)}

        existing_sessions = self._list_sessions() if not continue_mode else {}

        command = " ".join(cmd)
        print_dict(
            {"command": command, "continue_mode": continue_mode,
             "session_id": session_id, "research_topic": research_topic},
            header="Launching opencode",
        )
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)

        detected_session_id = session_id
        if not continue_mode:
            for _ in range(30):
                print("[controller message]: detecting new session ID...")
                time.sleep(1)
                current_sessions = self._list_sessions()
                new_ids = set(current_sessions) - set(existing_sessions)
                if new_ids:
                    detected_session_id = new_ids.pop()
                    title = current_sessions[detected_session_id]
                    print_dict({"session_id": detected_session_id, "title": title, "command": command},
                               header="Created new session")
                    break
            else:
                raise RuntimeError("Failed to detect new opencode session ID after 30s. Aborting.")
        else:
            current_sessions = self._list_sessions()
            title = current_sessions[session_id]
            print_dict({"session_id": session_id, "title": title, "command": command},
                       header="Resume old session")

        terminated_due_to_permission = False
        for stream in (process.stdout, process.stderr):
            if stream:
                for line in stream:
                    if not format_json_line(line):
                        print(line, end="")
                    if "The user rejected permission to use this specific tool call" in line:
                        print("[controller message]: Tool call was rejected by permission settings.")
                        terminated_due_to_permission = True

        process.wait()
        print(f"[controller message]: Return code: {process.returncode}, permission_error={terminated_due_to_permission}")
        return process.returncode, terminated_due_to_permission, detected_session_id


# ===================================================================
# Backend registry
# ===================================================================

_BACKENDS: dict[str, type[CodeAgentCli]] = {
    "claude": ClaudeCodeCli,
    "cc": ClaudeCodeCli,
    "opencode": OpenCodeCli,
}


def get_backend(name: str) -> CodeAgentCli:
    """Instantiate a backend by name (``"claude"`` / ``"cc"`` / ``"opencode"``)."""
    cls = _BACKENDS.get(name)
    if cls is None:
        raise ValueError(f"Unknown backend {name!r}. Choose from: {', '.join(_BACKENDS)}")
    return cls()


# ===================================================================
# Shared helpers
# ===================================================================

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


# ===================================================================
# Main orchestration
# ===================================================================

def run(
    backend: str = "claude",
    research_topic: str = "",
    blueprint: str = "",
    role: str = "",
    resume_latest_session: bool = False,
    resume_instruction: str = "",
    only_run_planning: bool = False,
    skip_permissions: bool = False,
    no_human_in_the_loop: bool = False,
    runner: str = "ssh",
    model: str | None = None,
    max_turns: int | None = None,
) -> int:

    cli = get_backend(backend)

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
        assert not resume_latest_session, "--no-human-in-the-loop conflicts with --resume"
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

    # ---- Backend-specific setup ----
    cli.setup(skip_permissions=skip_permissions, role=role)

    # ---- First run or resume ----
    print(f"[controller message]: run {cli.name} 1st ...")
    session_id = None

    if resume_latest_session:
        found_id = cli.find_session(session_name)
        if not found_id:
            raise RuntimeError(f"No {cli.name} session found with name: {session_name}")
        session_id = found_id
        terminated_due_to_permission = False
        print_dict({"session_id": session_id, "name": session_name}, header="Resuming session")
    else:
        cli.delete_sessions(session_name)
        returncode, terminated_due_to_permission, session_id = cli.run(
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
            print_dict({"end reason": "[controller message]: planning role, waiting user feedback."})
            return returncode

    # ---- Continue loop ----
    while _should_continue(terminated_due_to_permission, running_flag):
        print("[controller message]: Continuing session ...")
        if session_id:
            returncode, terminated_due_to_permission, _ = cli.run(
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
                print_dict({"end reason": "[controller message]: planning role, waiting user feedback."})
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


# ===================================================================
# CLI
# ===================================================================

def main():
    parser = argparse.ArgumentParser(prog="general_runner")
    subparsers = parser.add_subparsers(dest="role", required=True)

    for sp_name in ("leader", "worker"):
        sp = subparsers.add_parser(sp_name)
        sp.add_argument("--backend", default="claude", choices=list(_BACKENDS),
                        help="Code agent backend: claude/cc or opencode (default: claude)")
        sp.add_argument("--research-topic", default="", help="Research topic or path to topic file")
        sp.add_argument("--runner", required=True, choices=["ssh", "pai"],
                        help="Use ssh or pai (Alibaba Cloud)")
        sp.add_argument("--blueprint", default="", help="Path to blueprint .md file")
        sp.add_argument("--resume", "--resume-latest-session", action="store_true",
                        dest="resume_latest_session",
                        help="Resume the latest session (found by session name)")
        sp.add_argument("--resume-instruction", default="", help="Instruction for resuming")
        sp.add_argument("--only-run-planning", action="store_true", help="Run planning only and exit")
        sp.add_argument("--skip-permissions", action="store_true",
                        help="Skip all permission checks")
        sp.add_argument("--model", default=None,
                        help="Model to use (e.g. sonnet, opus, claude-sonnet-4-6)")
        sp.add_argument("--max-turns", type=int, default=None, help="Maximum agentic turns")
        if sp_name == "leader":
            sp.add_argument("--no-human-in-the-loop", action="store_true",
                            help="Run fully autonomous without human review")

    args = parser.parse_args()

    rc = run(
        backend=args.backend,
        research_topic=args.research_topic,
        blueprint=args.blueprint,
        role=args.role,
        resume_latest_session=args.resume_latest_session,
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
