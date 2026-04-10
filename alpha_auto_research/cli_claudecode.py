"""
Convenience CLI entry points for claudecode_runner — mirrors cli.py but for Claude Code.

Each function injects the appropriate default flags and forwards remaining
argv to the main claudecode_runner.
"""

import sys

from alpha_auto_research.claudecode_runner import main as _main


def _inject_and_run(extra_args: list[str]):
    sys.argv = [sys.argv[0], "leader", "--skip-permissions", *extra_args, *sys.argv[1:]]
    _main()


def new_planning():
    """alpha-rl-cc-new-planning — plan from scratch."""
    _inject_and_run(["--only-run-planning"])


def resume_planning():
    """alpha-rl-cc-resume-planning — resume an existing plan."""
    _inject_and_run(["--resume", "--only-run-planning"])


def begin_experiments():
    """alpha-rl-cc-begin-experiments — start executing experiments."""
    _inject_and_run([])


def resume_experiment():
    """alpha-rl-cc-resume-experiment — resume experiment execution."""
    _inject_and_run(["--resume"])


def new_research_no_human():
    """alpha-rl-cc-new-research-no-human — fully autonomous research, no human review."""
    _inject_and_run(["--no-human-in-the-loop"])
