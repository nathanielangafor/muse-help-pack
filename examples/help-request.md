# Muse help request

> Draft: fill in the blanks and review before sharing.

## Context

- Goal: [fill in]
- Expected result: [fill in]
- What happened: [fill in]
- Platform and muse-discord version: [fill in]
- Steps to reproduce: [fill in]
- Already tried: [fill in]

## Offline log signals

- Input 1: read

### Message Content intent unavailable

Matching lines: 1

Check Message Content intent in the Discord Developer Portal, then follow the upstream connection guide.

### Duplicate reply suppressed

Matching lines: 2

Check for duplicate wake hooks or a hook plus a poller. A suppressed duplicate does not prove a missed reply.

### Discord REST rate limit

Matching lines: 1

Allow the backoff to finish; repeated restarts can extend the limit. Report whether this repeats.


Signals are text matches, not a live health check. Old, quoted or repeated lines can match. No match does not mean healthy. Raw input and file paths are omitted.

[Upstream troubleshooting guide](https://github.com/cszach/muse-discord/blob/main/TROUBLESHOOTING.md)

## Share only when ready

Do not attach the original log or config. Remove secrets and private details from anything you add to this draft.
Optional: [join the independent Muse Agent community](https://discord.gg/sxjhCPdEG6), search existing help posts, then share one problem with this context. Account and billing issues belong with official support.
