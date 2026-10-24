#!/usr/bin/env python3
"""Offline, allowlisted diagnostic summaries. Python 3.10+, standard library only."""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import sys

VERSION = "0.1.0"
MAX_BYTES = 2 * 1024 * 1024
MAX_FILES = 8
SOURCE = "https://github.com/cszach/muse-discord/blob/main/TROUBLESHOOTING.md"
COMMUNITY = "https://discord.gg/sxjhCPdEG6"
# Only fixed IDs, labels and advice leave the classifier. Never include matches.
RULES = (
    ("token_rejected", r"TOKEN REJECTED|Discord rejected the token", "Discord token rejected", "Check whether the bot token was reset. Follow the upstream token-file setup; never paste the token into a help post."),
    ("gateway_intent", r"GATEWAY DISABLED\s*\(code 4014\)|Message Content is off", "Message Content intent unavailable", "Check Message Content intent in the Discord Developer Portal, then follow the upstream connection guide."),
    ("worker_prompt", r"WORKER PROMPT OUT OF DATE", "Worker prompt out of date", "Follow the upstream UPDATING.md worker-prompt step."),
    ("duplicate_reply", r"Skipping duplicate reply", "Duplicate reply suppressed", "Check for duplicate wake hooks or a hook plus a poller. A suppressed duplicate does not prove a missed reply."),
    ("rate_limit", r"RATE LIMITED:\s*backing off REST", "Discord REST rate limit", "Allow the backoff to finish; repeated restarts can extend the limit. Report whether this repeats."),
    ("channel_permission", r"Skipping replies in", "Reply skipped in a channel", "Check View Channel and Send Messages permissions for the bot in the affected channel."),
    ("settings_ui", r"Settings UI unavailable", "Settings UI unavailable", "Check that settings_ui.py exists and loads; consult the upstream update instructions."),
    ("missing_module", r"ModuleNotFoundError:\s*No module named", "Python dependency missing", "Check the intended Python environment and follow the upstream dependency installation instructions."),
)
PATTERNS = [(key, re.compile(pattern, re.I), title, advice) for key, pattern, title, advice in RULES]


def read_tail(path):
    """Bound reads, reject directories/devices, and drop a partial first line."""
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(path, flags)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("regular_file_required")
        start = max(0, info.st_size - MAX_BYTES)
        os.lseek(fd, start, os.SEEK_SET)
        data = bytearray()
        remaining = min(info.st_size, MAX_BYTES)
        while remaining:
            chunk = os.read(fd, min(65536, remaining))
            if not chunk:
                break
            data.extend(chunk)
            remaining -= len(chunk)
        if start:
            # The byte before the tail may be a newline, but dropping one complete
            # line conservatively is preferable to interpreting a partial event.
            _, _, data = data.partition(b"\n")
        return bytes(data).decode("utf-8", errors="replace"), bool(start)
    finally:
        os.close(fd)


def summarize(paths):
    if not 1 <= len(paths) <= MAX_FILES:
        raise ValueError("Provide between one and eight log files.")
    counts = {rule[0]: 0 for rule in RULES}
    inputs = []
    for index, path in enumerate(paths, 1):
        item = {"input": index}
        try:
            content, truncated = read_tail(path)
        except (OSError, ValueError) as error:
            item["status"] = "not_regular" if isinstance(error, ValueError) else "unreadable"
        else:
            item.update(status="read", tail_limited=truncated)
            for line in content.splitlines():
                for key, pattern, _, _ in PATTERNS:
                    if pattern.search(line):
                        counts[key] += 1
        inputs.append(item)
    return {
        "tool": "Muse Help Pack", "version": VERSION, "inputs": inputs,
        "signals": [{"id": key, "title": title, "matching_lines": counts[key], "next_check": advice}
                    for key, _, title, advice in RULES if counts[key]],
        "limits": "Signals are text matches, not a live health check. Old, quoted or repeated lines can match. No match does not mean healthy. Raw input and file paths are omitted.",
        "upstream_guide": SOURCE,
    }


def markdown(report):
    lines = ["# Muse help request", "", "> Draft: fill in the blanks and review before sharing.", "",
             "## Context", "", "- Goal: [fill in]", "- Expected result: [fill in]",
             "- What happened: [fill in]", "- Platform and muse-discord version: [fill in]",
             "- Steps to reproduce: [fill in]", "- Already tried: [fill in]", "",
             "## Offline log signals", ""]
    for item in report["inputs"]:
        suffix = " (last 2 MiB; partial first line discarded)" if item.get("tail_limited") else ""
        lines.append(f"- Input {item['input']}: {item['status']}{suffix}")
    lines.append("")
    if not report["signals"]:
        lines.append("No recognized signals found in readable input. This is not a clean bill of health.")
    for signal in report["signals"]:
        lines.extend([f"### {signal['title']}", "", f"Matching lines: {signal['matching_lines']}", "", signal["next_check"], ""])
    lines.extend(["", report["limits"], "", f"[Upstream troubleshooting guide]({SOURCE})", "",
                  "## Share only when ready", "", "Do not attach the original log or config. Remove secrets and private details from anything you add to this draft.",
                  f"Optional: [join the independent Muse Agent community]({COMMUNITY}), search existing help posts, then share one problem with this context. Account and billing issues belong with official support.", ""])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Create an offline help draft from known muse-discord log signals. Never copies raw log lines.")
    parser.add_argument("logs", nargs="+", help="Explicit log files; no directory scanning or config loading")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path, help="Create a NEW report file; refuses to overwrite")
    args = parser.parse_args(argv)
    if len(args.logs) > MAX_FILES:
        parser.error("at most eight input files are supported")
    report = summarize(args.logs)
    output = json.dumps(report, indent=2) + "\n" if args.format == "json" else markdown(report)
    if args.output:
        try:
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(output)
        except OSError:
            print("Could not create report. Choose a new writable output file; no existing file was overwritten.", file=sys.stderr)
            return 2
    else:
        print(output, end="")
    return 2 if any(item["status"] != "read" for item in report["inputs"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
