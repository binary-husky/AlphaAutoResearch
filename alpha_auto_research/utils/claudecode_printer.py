"""Pretty-print helpers for Claude Code stream-json output."""

import json
from beast_logger import print_dict

_CONTENT_PREVIEW_LIMIT = 2000  # max chars to show per field


def _truncate(text: str, limit: int = _CONTENT_PREVIEW_LIMIT) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + f"... ({len(text)} chars total)"


def _format_tool_use(msg: dict) -> None:
    """Pretty-print a tool use message from Claude Code stream-json."""
    tool = msg.get("tool", {})
    tool_name = tool.get("name", msg.get("tool_name", "?"))
    tool_input = tool.get("input", msg.get("input", {}))

    summary: dict = {"tool": tool_name}

    if tool_name in ("Bash", "bash"):
        summary["command"] = _truncate(
            tool_input if isinstance(tool_input, str) else tool_input.get("command", "")
        )
    elif tool_name in ("Read", "read"):
        summary["file"] = tool_input.get("file_path", tool_input.get("filePath", ""))
    elif tool_name in ("Write", "write"):
        summary["file"] = tool_input.get("file_path", tool_input.get("filePath", ""))
        content = tool_input.get("content", "")
        summary["content_length"] = f"{len(content)} chars"
    elif tool_name in ("Edit", "edit"):
        summary["file"] = tool_input.get("file_path", tool_input.get("filePath", ""))
        summary["old"] = _truncate(tool_input.get("old_string", tool_input.get("oldText", "")))
        summary["new"] = _truncate(tool_input.get("new_string", tool_input.get("newText", "")))
    elif tool_name in ("Grep", "grep"):
        summary["pattern"] = tool_input.get("pattern", "")
        if tool_input.get("path"):
            summary["path"] = tool_input["path"]
    elif tool_name in ("Glob", "glob"):
        summary["pattern"] = tool_input.get("pattern", "")
        if tool_input.get("path"):
            summary["path"] = tool_input["path"]
    else:
        if isinstance(tool_input, dict) and tool_input:
            summary["input_keys"] = list(tool_input.keys())
        elif isinstance(tool_input, str):
            summary["input"] = _truncate(tool_input)

    print_dict(summary, header=f"Tool: {tool_name}")


def _format_tool_result(msg: dict) -> None:
    """Pretty-print a tool result message."""
    content = msg.get("content", "")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                text = block.get("text", "")
                if text:
                    print(_truncate(text))
            elif isinstance(block, str):
                print(_truncate(block))
    elif content:
        print(_truncate(str(content)))


def format_stream_json_line(line: str) -> bool:
    """Parse a line from Claude Code --output-format=stream-json and pretty-print it.

    Returns True if the line was handled, False otherwise.
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

    # Claude Code stream-json event types:
    # assistant - assistant text/content
    # tool_use  - tool invocation
    # tool_result - tool output
    # result    - final result
    # system    - system/init events

    if etype == "assistant":
        content = event.get("message", {}).get("content", "")
        if isinstance(content, str) and content:
            print(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    print(block.get("text", ""))
        return True

    if etype == "content_block_delta":
        delta = event.get("delta", {})
        if delta.get("type") == "text_delta":
            text = delta.get("text", "")
            if text:
                print(text, end="")
        return True

    if etype == "tool_use":
        _format_tool_use(event)
        return True

    if etype == "tool_result":
        _format_tool_result(event)
        return True

    if etype == "result":
        subtype = event.get("subtype", "")
        result_text = event.get("result", "")
        cost = event.get("total_cost_usd", event.get("cost_usd"))
        session_id = event.get("session_id", "")
        summary = {"subtype": subtype}
        if session_id:
            summary["session_id"] = session_id
        if cost is not None:
            summary["cost_usd"] = cost
        if result_text:
            summary["result"] = _truncate(str(result_text))
        print_dict(summary, header="Result")
        return True

    if etype == "system":
        subtype = event.get("subtype", "")
        session_id = event.get("session_id", "")
        if session_id or subtype:
            summary = {}
            if subtype:
                summary["subtype"] = subtype
            if session_id:
                summary["session_id"] = session_id
            print_dict(summary, header="System")
        return True

    # Unknown event — show compact summary
    summary = {"type": etype}
    for key in ("session_id", "subtype", "message"):
        if key in event:
            val = event[key]
            if isinstance(val, str):
                summary[key] = _truncate(val)
    print_dict(summary, header=f"Event: {etype}")
    return True
