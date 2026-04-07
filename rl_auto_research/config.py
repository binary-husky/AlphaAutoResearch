"""
Centralized config loader.

Reads research_config.jsonc from the project root.
Usage: from rl_auto_research.config import config
"""

import json
import os
import re

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "research_config.jsonc")


def _strip_jsonc_comments(text: str) -> str:
    """Remove // comments from JSONC text."""
    lines = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("//"):
            continue
        line = re.sub(r'(?<=["\d\]\}\w])\s*//.*$', '', line)
        lines.append(line)
    return "\n".join(lines)


def _load_config() -> dict:
    if not os.path.exists(_CONFIG_PATH):
        raise FileNotFoundError(
            f"Config file not found: {_CONFIG_PATH}\n"
            f"Copy research_config.example.jsonc to research_config.jsonc and fill in your values."
        )
    with open(_CONFIG_PATH, "r") as f:
        raw = f.read()
    return json.loads(_strip_jsonc_comments(raw))


config = _load_config()
