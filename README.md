# Muse Help Pack

**Turn a confusing muse-discord log into a focused help request—without copying the log.**

An offline Python CLI for people bringing their Muse into Discord. It recognizes eight documented error signals, suggests the next check, and builds a Markdown help-request draft. No dependencies, accounts, API keys, telemetry, or network calls.

```text
GATEWAY DISABLED (code 4014) → Message Content intent unavailable
Skipping duplicate reply   → Check for duplicate wake hooks
RATE LIMITED: backing off  → Let the backoff finish
```

## Try the included demo

Download this repository, open its folder in a terminal, then run with Python 3.10 or newer:

```sh
python3 muse_help_pack.py examples/synthetic.log
```

On Windows, use `py -3` in place of `python3`. See the [complete example output](examples/help-request.md). The example contains only synthetic data.

## Make your help request

Pass the log files explicitly. The program never scans a directory or reads config files on its own.

```sh
python3 muse_help_pack.py /path/to/muse-discord/monitor.log --output report.md
# Include the previous run if useful:
python3 muse_help_pack.py /path/to/monitor.log /path/to/monitor.log.1 --format json
```

1. Read the suggested checks and the linked upstream troubleshooting guide.
2. Fill in your goal, expected result, actual result, platform/version, reproduction steps, and what you tried.
3. Review what you added. Share the draft, **not** your original logs or config.

`--output` creates a new file and refuses to overwrite anything. Without it, the draft goes to standard output. Exit `0` means the report was generated, even if signals were found. Exit `2` means an input could not be read, too many inputs were supplied, or output creation failed. A partial report identifies failed inputs by number; their paths are never printed by the tool.

## What it recognizes

| Signal | Suggested investigation |
| --- | --- |
| Rejected token | Reset or stale bot token |
| Gateway 4014 / Message Content off | Privileged intent configuration |
| Worker prompt out of date | Upstream update steps |
| Duplicate reply skipped | Duplicate wake hooks/pollers |
| REST rate limit | Backoff and repeat frequency |
| Reply skipped in a channel | Channel permissions |
| Settings UI unavailable | Missing or unloadable settings UI |
| Python module missing | Python environment/dependencies |

Matches count **lines**, not incidents. Multiple signals may match one line. Combining overlapping logs can double-count events. The tool reads at most the last 2 MiB of each of eight files and discards a partial first line. It does not establish event timing or whether a problem is still present.

## Why this exists alongside the upstream doctor

[muse-discord](https://github.com/cszach/muse-discord) already ships `bin/doctor.py`, which checks the running installation. Use that for live health. Help Pack is a separate, offline handoff: it helps you describe a problem without pasting private logs. It never executes upstream scripts, changes configuration, restarts processes, contacts Discord, or posts anything.

Rules were checked against the [upstream troubleshooting guide](https://github.com/cszach/muse-discord/blob/main/TROUBLESHOOTING.md) on October 24, 2026 (blob `6ee5fb34d260d9f645d0fa4c3519a6a2990f3386`). No upstream implementation code is included. Future log changes may require new signatures.

## Privacy by omission

Only fixed signal names, fixed advice, counts, and read-status flags enter the output. No raw text, match excerpts, filenames, timestamps, IDs, system inventory, or environment variables are included. This is **not a general-purpose log redactor**: unknown errors are omitted, not sanitized. Quoted or misleading input can trigger a signal. No match does not mean the bot is healthy.

The report can reveal which error categories occurred. Review it before sharing. Anything you manually add is your responsibility to review; this tool does not sanitize later edits. Logs remain on your machine, and opening the community/docs links is optional.

## Get help and share what you build

[Join the independent Muse Agent community](https://discord.gg/sxjhCPdEG6). Search existing help posts, then bring one problem and your reviewed draft. You can also share your projects and learn with other Muse builders. Joining is optional; the tool works fully offline. Account and billing issues belong with official product support.

This community project is not affiliated with or endorsed by Meta or Discord. The invite was verified as resolving to **Muse Agent** on October 24, 2026; invitations may change later.

## Development

```sh
python3 -m unittest discover -s tests -v
```

Tests cover every signature, private-content omission, corrupt UTF-8, bounded reads, missing files, special files, CLI exit codes, and overwrite refusal. CI is configured for Python 3.10/3.14 on Linux, macOS, and Windows.

Contributions: include a synthetic log line and test for each new signature, link its public documentation, and keep all generated prose fixed. Do not submit real logs, tokens, private messages, or member data in issues or pull requests.

MIT licensed. See [LICENSE](LICENSE).
