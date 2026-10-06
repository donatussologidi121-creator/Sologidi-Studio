"""The things Tamara can do on your Mac, plus the safety check that runs before risky ones."""
import os
import re
import shlex
import subprocess

MAX_OUTPUT = 4000

TOOLS = [
    {
        "name": "run_shell",
        "description": "Run a shell command on the user's Mac (zsh). Use for files, apps, system info, git, brew, scripts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "explanation": {"type": "string", "description": "One short spoken-style sentence: what this does."},
            },
            "required": ["command", "explanation"],
        },
    },
    {
        "name": "run_applescript",
        "description": "Run AppleScript to control Mac apps (Safari, Mail, Calendar, Music, Finder, volume, notifications...).",
        "input_schema": {
            "type": "object",
            "properties": {
                "script": {"type": "string"},
                "explanation": {"type": "string", "description": "One short spoken-style sentence: what this does."},
            },
            "required": ["script", "explanation"],
        },
    },
    {
        "name": "open_target",
        "description": "Open an app by name (e.g. 'Safari'), a website URL, or a file/folder path.",
        "input_schema": {
            "type": "object",
            "properties": {"target": {"type": "string"}},
            "required": ["target"],
        },
    },
    {
        "name": "read_file",
        "description": "Read a text file from the Mac.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Create or overwrite a text file on the Mac.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
                "explanation": {"type": "string", "description": "One short spoken-style sentence: what this does."},
            },
            "required": ["path", "content", "explanation"],
        },
    },
]

# Commands that only look at things and never change anything.
SAFE_COMMANDS = {
    "ls", "pwd", "date", "whoami", "uptime", "df", "du", "cat", "head", "tail", "wc", "echo",
    "which", "uname", "sw_vers", "hostname", "ps", "top", "pmset", "system_profiler", "ifconfig",
    "networksetup", "mdfind", "find", "grep", "stat", "file", "open", "say", "cal", "printenv",
}
UNSAFE_SYNTAX = re.compile(r"[;&|<>`]|\$\(|\bsudo\b|\brm\b|-delete|-exec")
SAFE_APPLESCRIPT = re.compile(
    r'^\s*(set volume [^\n]*|tell application "[^"]+" to activate|display notification [^\n]*)\s*$', re.I
)


def _clip(text):
    return text if len(text) <= MAX_OUTPUT else text[:MAX_OUTPUT] + "\n...[output cut]"


def _needs_confirmation(name, args):
    if name == "run_shell":
        try:
            first = shlex.split(args["command"])[0]
        except (ValueError, IndexError):
            return True
        return first not in SAFE_COMMANDS or bool(UNSAFE_SYNTAX.search(args["command"]))
    if name == "run_applescript":
        return not SAFE_APPLESCRIPT.match(args["script"])
    if name == "write_file":
        return True
    return False


def run_tool(name, args, confirm):
    """Execute a tool. `confirm(question)` asks the user out loud and returns True/False."""
    if _needs_confirmation(name, args):
        what = args.get("explanation", f"use {name}")
        if not confirm(f"I'm about to {what.rstrip('.').lower()}. Shall I go ahead?"):
            return "The user said no. Do not retry; ask what they'd prefer instead."
    try:
        if name == "run_shell":
            done = subprocess.run(
                args["command"], shell=True, executable="/bin/zsh", capture_output=True,
                text=True, timeout=60, cwd=os.path.expanduser("~"),
            )
            out = (done.stdout + done.stderr).strip() or "(no output)"
            return _clip(f"exit code {done.returncode}\n{out}")
        if name == "run_applescript":
            done = subprocess.run(["osascript", "-e", args["script"]], capture_output=True, text=True, timeout=60)
            return _clip((done.stdout + done.stderr).strip() or "done")
        if name == "open_target":
            target = args["target"]
            cmd = ["open", target] if re.match(r"^(https?://|/|~)", target) else ["open", "-a", target]
            if target.startswith("~"):
                cmd = ["open", os.path.expanduser(target)]
            done = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return "opened" if done.returncode == 0 else _clip(done.stderr.strip())
        if name == "read_file":
            with open(os.path.expanduser(args["path"]), "r", errors="replace") as f:
                return _clip(f.read())
        if name == "write_file":
            path = os.path.expanduser(args["path"])
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w") as f:
                f.write(args["content"])
            return f"wrote {path}"
        return f"Unknown tool: {name}"
    except subprocess.TimeoutExpired:
        return "That took too long and was stopped."
    except Exception as err:  # report errors back to Tamara instead of crashing
        return f"Error: {err}"
