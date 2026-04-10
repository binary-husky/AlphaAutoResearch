"""Pretty-print helpers for opencode JSON (JSONL) output."""

import json
from datetime import datetime
from beast_logger import print_dict

_CONTENT_PREVIEW_LIMIT = 2000  # max chars to show per field


def _truncate(text: str, limit: int = _CONTENT_PREVIEW_LIMIT) -> str:
    """Truncate text to *limit* characters, appending '...' if shortened."""
    if not text:
        return ""
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + f"... ({len(text)} chars total)"


def _format_tool_use(part: dict) -> None:
    """Pretty-print a tool_use event."""
    tool = part.get("tool", "?")
    state = part.get("state", {})
    status = state.get("status", "?")
    title = state.get("title", "")
    inp = state.get("input", {})
    out = state.get("output", "")
    timing = state.get("time", {})

    # Build a concise summary dict
    summary: dict = {"tool": tool, "status": status}
    if title:
        summary["title"] = title

    # Tool-specific input summaries
    if tool == "bash":
        summary["command"] = _truncate(inp if isinstance(inp, str) else inp.get("command", ""))
    elif tool in ("read", "write", "edit"):
        summary["file"] = inp.get("filePath", inp.get("file_path", ""))
        if tool == "write":
            content = inp.get("content", "")
            summary["content_length"] = f"{len(content)} chars"
        elif tool == "edit":
            summary["old"] = _truncate(inp.get("old_string", inp.get("oldText", "")))
            summary["new"] = _truncate(inp.get("new_string", inp.get("newText", "")))
    elif tool in ("grep", "glob"):
        summary["pattern"] = inp.get("pattern", "")
        if inp.get("path"):
            summary["path"] = inp.get("path")
    else:
        # Generic: show input keys
        if isinstance(inp, dict) and inp:
            summary["input_keys"] = list(inp.keys())
        elif isinstance(inp, str):
            summary["input"] = _truncate(inp)

    # Output summary
    if out:
        summary["output"] = _truncate(out if isinstance(out, str) else json.dumps(out))

    # Timing
    if timing:
        start = timing.get("start")
        end = timing.get("end")
        if start and end:
            summary["duration"] = f"{(end - start) / 1000:.1f}s"

    print_dict(summary, header=f"Tool: {tool}")


def _format_text_event(part: dict) -> None:
    """Pretty-print a text/assistant message event."""
    content = part.get("content", "")
    if isinstance(content, list):
        # Content blocks
        for block in content:
            if isinstance(block, dict):
                print(block.get("text", json.dumps(block)))
            else:
                print(block)
    elif content:
        print(content)


def format_json_line(line: str) -> bool:
    """Try to parse *line* as an opencode JSON event and pretty-print it.

    Returns True if the line was handled as JSON, False otherwise.
    """
    line = line.strip()
    if not line:
        return False
    try:
        event = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return False

    if not isinstance(event, dict):
        return False

    etype = event.get("type", "")
    part = event.get("part", {})

    if etype == "tool_use":
        _format_tool_use(part)
    elif etype == "text":
        _format_text_event(part)
    elif etype == "step_start":
        ts = event.get("timestamp")
        ts_str = datetime.fromtimestamp(ts / 1000).strftime("%H:%M:%S") if ts else ""
        print(f"\n--- step start {ts_str} ---")
    elif etype == "step_end":
        ts = event.get("timestamp")
        ts_str = datetime.fromtimestamp(ts / 1000).strftime("%H:%M:%S") if ts else ""
        print(f"--- step end {ts_str} ---\n")
    else:
        # Unknown event type — print type + compact summary
        summary = {"type": etype}
        if part.get("tool"):
            summary["tool"] = part["tool"]
        if part.get("content"):
            summary["content"] = _truncate(
                part["content"] if isinstance(part["content"], str) else json.dumps(part["content"])
            )
        print_dict(summary, header=f"Event: {etype}")

    return True
