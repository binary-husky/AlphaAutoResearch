"""
Convenience CLI entry points for general_runner.

Each function injects the appropriate default flags and forwards remaining
argv to the general_runner.  The ``--backend`` flag controls whether Claude
Code or OpenCode is used (defaults to ``claude``).
"""

import sys

from alpha_auto_research.general_runner import main as _main


def _inject_and_run(extra_args: list[str]):
    sys.argv = [sys.argv[0], "leader", "--runner", "ssh", *extra_args, *sys.argv[1:]]
    _main()


def new_planning():
    """alpha-g-new-plan — plan from scratch."""
    _inject_and_run(["--only-run-planning"])


def resume_planning():
    """alpha-g-resume-plan — resume an existing plan."""
    _inject_and_run(["--resume", "--only-run-planning"])


def resume_experiment():
    """alpha-g-resume — resume experiment execution (also starts experiments after planning)."""
    _inject_and_run(["--resume"])


def fully_auto():
    """alpha-g-auto — fully autonomous research, no human review."""
    _inject_and_run(["--no-human-in-the-loop"])
