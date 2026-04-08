"""
Convenience CLI entry points that mirror the aliases in begin_research.bash.

Each function injects the appropriate default flags and forwards remaining
argv to the main opencode_runner.
"""

import sys

from rl_auto_research.opencode_runner import main as _main


def _inject_and_run(extra_args: list[str]):
    sys.argv = [sys.argv[0], "leader", "--skip-permissions", *extra_args, *sys.argv[1:]]
    _main()


def new_planning():
    """alpha_rl_research_new_planning — plan from scratch."""
    _inject_and_run(["--only-run-planning"])


def resume_planning():
    """alpha_rl_research_resume_planning — resume an existing plan."""
    _inject_and_run(["--resume", "--only-run-planning"])


def begin_experiments():
    """alpha_rl_research_begin_experiments — start executing experiments."""
    _inject_and_run(["--resume"])


def resume_experiment():
    """alpha_rl_research_resume_experiment — resume experiment execution."""
    _inject_and_run(["--resume"])


def new_research_no_human():
    """alpha_rl_research_new_research_no_human — fully autonomous research, no human review."""
    _inject_and_run(["--no-human-in-the-loop"])
