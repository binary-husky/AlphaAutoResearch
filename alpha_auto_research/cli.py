"""
Convenience CLI entry points that mirror the aliases in begin_research.bash.

Each function injects the appropriate default flags and forwards remaining
argv to the main opencode_runner.
"""

import sys

from alpha_auto_research.opencode_runner import main as _main


def _inject_and_run(extra_args: list[str]):
    sys.argv = [sys.argv[0], "leader", *extra_args, *sys.argv[1:]]
    _main()


def new_planning():
    """alpha-new-plan — plan from scratch."""
    _inject_and_run(["--only-run-planning"])


def resume_planning():
    """alpha-resume-plan — resume an existing plan."""
    _inject_and_run(["--resume", "--only-run-planning"])


def resume_experiment():
    """alpha-resume — resume experiment execution (also starts experiments after planning)."""
    _inject_and_run(["--resume"])


def fully_auto():
    """alpha-auto — fully autonomous research, no human review."""
    _inject_and_run(["--no-human-in-the-loop"])


def beta():
    """beta <blueprint_path> — run a worker with the given blueprint."""
    if len(sys.argv) < 2:
        print("Usage: beta <blueprint_path>")
        sys.exit(1)
    blueprint_path = sys.argv[1]
    sys.argv = [sys.argv[0], "worker", "--blueprint", blueprint_path, *sys.argv[2:]]
    _main()
