"""
SSH experiment launcher.

Launches a blueprint on a remote host (or localhost) inside a tmux session,
mirroring the PAI runner's tmux-based approach.
"""

import hashlib
import os
import subprocess
import time
from textwrap import dedent

from alpha_auto_research.config import config
from alpha_auto_research.blueprint_runner.base import ExperimentSubagent




def _setup_localhost_ssh() -> None:
    """Set up password-free SSH to localhost."""
    ssh_dir = os.path.expanduser("~/.ssh")
    key_path = os.path.join(ssh_dir, "id_ed25519_sk")
    pub_key_path = os.path.join(ssh_dir, "id_ed25519_sk.pub")
    auth_keys_path = os.path.join(ssh_dir, "authorized_keys")

    print("Setting up password-free SSH to localhost...")

    if not os.path.exists(key_path):
        print("Generating SSH key for localhost...")
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-f", key_path, "-N", ""],
            capture_output=True
        )

    if os.path.exists(pub_key_path):
        print("Generating SSH key for localhost...")
        with open(pub_key_path, "r") as f:
            pub_key = f.read().strip()
        existing = ""
        if os.path.exists(auth_keys_path):
            with open(auth_keys_path, "r") as f:
                existing = f.read()
        if pub_key not in existing:
            with open(auth_keys_path, "a") as f:
                f.write(pub_key + "\n")
        os.chmod(auth_keys_path, 0o600)


def _run_cmd(host_cfg: dict, remote_cmd: str) -> subprocess.CompletedProcess:
    """Run a command on the target host — locally or via SSH."""
    cmd = ["ssh", "-o", "StrictHostKeyChecking=no"]
    if host_cfg.get("port"):
        cmd += ["-p", str(host_cfg["port"])]
    cmd.append(f"{host_cfg.get('user', 'root')}@{host_cfg['host']}")
    cmd.append(remote_cmd)
    return subprocess.run(cmd, capture_output=True, text=True)


def _tmux_session_name(blueprint_path: str) -> str:
    """Generate a unique tmux session name from blueprint path."""
    short_hash = hashlib.md5(blueprint_path.encode()).hexdigest()[:8]
    base = os.path.basename(blueprint_path).replace(".", "_")
    return f"exp_{base}_{short_hash}"


class SshExperimentSubagent(ExperimentSubagent):

    def _get_hosts(self) -> list[dict]:
        return config["ssh"]["hosts"]

    def _pick_host(self) -> dict:
        """Pick the first available host (round-robin could be added later)."""
        hosts = self._get_hosts()
        assert hosts, "No SSH hosts configured in research_config.jsonc"
        return hosts[0]

    def _build_launch_command(self, blueprint_path: str, session_name: str) -> str:

        project_root = os.path.join(os.path.abspath(
            os.path.dirname(__file__)
        ), "..", "..")

        still_training = f"/tmp/still_training_{session_name}"

        setup = ""
        print(f"Running in tmux window: {session_name}")

        return dedent(f"""\
            {setup}\\
            echo "set-option -g history-limit 100000" >> ~/.tmux.conf 2>/dev/null; \\
            tmux start-server 2>/dev/null || true && \\
            tmux new-session -d -s {session_name} && \\
            tmux send-keys -t {session_name} "cd {project_root}" Enter && \\
            tmux send-keys -t {session_name} "source .venv/bin/activate 2>/dev/null" Enter && \\
            tmux send-keys -t {session_name} "export SETUPTOOLS_USE_DISTUTILS=local" Enter && \\
            tmux send-keys -t {session_name} "export OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS=1800000" Enter && \\
            sleep 2 && \\
            tmux send-keys -t {session_name} "python -m alpha_auto_research.opencode_runner worker --runner=ssh --blueprint={blueprint_path}; rm -f {still_training}" Enter && \\
            touch {still_training}\
        """)

    def _job_id(self, host_cfg: dict, blueprint_path: str, session_name: str) -> str:
        """Construct a synthetic job ID: ssh://<user>@<host>:<port>/<session_name>/<blueprint_path>"""
        user = host_cfg.get("user", "root")
        host = host_cfg["host"]
        port = host_cfg.get("port", 22)
        return f"ssh://{user}@{host}:{port}/{session_name}{blueprint_path}"

    def _parse_job_id(self, job_id: str) -> tuple[dict, str, str]:
        """Parse a synthetic SSH job ID back into (host_cfg, session_name, blueprint_path)."""
        # ssh://user@host:port/session_name/abs/path/to/blueprint
        rest = job_id[len("ssh://"):]
        user_host, remainder = rest.split(":", 1)
        user, host = user_host.split("@", 1)
        port_str, path_part = remainder.split("/", 1)
        # path_part = "session_name/abs/path..."
        session_name, blueprint_path = path_part.split("/", 1)
        blueprint_path = "/" + blueprint_path
        return {"user": user, "host": host, "port": int(port_str)}, session_name, blueprint_path

    def launch(self, blueprint_path: str, exp_name: str) -> str:
        host_cfg = self._pick_host()
        blueprint_path = os.path.abspath(blueprint_path)
        session_name = _tmux_session_name(blueprint_path)
        launch_cmd = self._build_launch_command(blueprint_path, session_name)

        print(f"[ssh_runner] Launching {session_name} on {host_cfg['host']}...")
        result = _run_cmd(host_cfg, launch_cmd)
        if result.returncode != 0:
            if host_cfg["host"] in ("localhost", "127.0.0.1", "::1"):
                print(f"[ssh_runner] SSH to localhost failed, setting up password-free SSH...")
                _setup_localhost_ssh()
                result = _run_cmd(host_cfg, launch_cmd)
            if result.returncode != 0:
                print(f"[ssh_runner] stdout: {result.stdout}")
                print(f"[ssh_runner] stderr: {result.stderr}")
                raise RuntimeError(f"Launch failed on {host_cfg['host']}: {result.stderr}")

        job_id = self._job_id(host_cfg, blueprint_path, session_name)
        print(f"[ssh_runner] Launched: {job_id}")
        return job_id

    def monitor(self, job_id: str) -> str:
        """Poll the still_training flag file on the remote host."""
        host_cfg, session_name, blueprint_path = self._parse_job_id(job_id)
        still_training = f"/tmp/still_training_{session_name}"

        while True:
            result = _run_cmd(host_cfg, f"test -f {still_training}")
            if result.returncode != 0:
                print(f"[ssh_runner] {job_id}: finished.")
                return "Succeeded"
            print(f"[ssh_runner] {job_id}: still running...")
            time.sleep(30)

    def stop(self, job_id: str) -> None:
        host_cfg, session_name, blueprint_path = self._parse_job_id(job_id)
        still_training = f"/tmp/still_training_{session_name}"
        _run_cmd(host_cfg, f"rm -f {still_training} && tmux kill-session -t {session_name} 2>/dev/null || true")
        print(f"[ssh_runner] Stopped: {job_id}")

    def delete(self, job_id: str) -> None:
        self.stop(job_id)

    def scan_jobs(self) -> list[dict]:
        """List all exp_* tmux sessions across configured hosts."""
        results = []
        for host_cfg in self._get_hosts():
            host = host_cfg["host"]
            result = _run_cmd(host_cfg, "tmux list-sessions -F '#{session_name}' 2>/dev/null || true")
            for line in result.stdout.strip().splitlines():
                session_name = line.strip()
                if not session_name.startswith("exp_"):
                    continue
                still_training = f"/tmp/still_training_{session_name}"
                check = _run_cmd(host_cfg, f"test -f {still_training}")
                status = "Running" if check.returncode == 0 else "Stopped"
                results.append({
                    "job_id": f"ssh://{host_cfg.get('user', 'root')}@{host}:{host_cfg.get('port', 22)}/{session_name}",
                    "display_name": f"{session_name}@{host}",
                    "status": status,
                    "create_time": "",
                })
        return results
