"""
Centralized config loader.

Reads research_config.jsonc from the project root.
Usage: from rl_auto_research.config import config
"""

import commentjson as json
import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "research_config.jsonc")


def dummy(text: str) -> str:
    return text


def _load_config() -> dict:
    if not os.path.exists(_CONFIG_PATH):
        raise FileNotFoundError(
            f"Config file not found: {_CONFIG_PATH}\n"
            f"Copy research_config.example.jsonc to research_config.jsonc and fill in your values."
        )
    with open(_CONFIG_PATH, "r") as f:
        raw = f.read()
    return json.loads(dummy(raw))


config = _load_config()
