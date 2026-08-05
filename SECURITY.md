# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes       |
| < 0.1.0 | No        |

Only the latest released version receives fixes. Older tags are not patched.

## Reporting a vulnerability

Please report security issues privately. **Do not open a public issue.**

Use GitHub's private vulnerability reporting:
[Report a vulnerability](https://github.com/MelancholySky/Crest/security/advisories/new)

Include where you can:

- Version affected (`crest --version`) and how it was installed (PyPI, AUR, source)
- Python version and operating system
- Steps to reproduce, ideally a minimal command
- What the impact is, or what you think it might be

Proof-of-concept code is welcome. Please don't include real credentials or
personal data in a report.

## What to expect

- **Acknowledgement:** within 7 days
- **Initial assessment:** within 14 days
- **Fix or decision:** depends on severity; you'll get an update either way

This is a small project maintained by one person, so timelines are best-effort
rather than guaranteed. If you haven't heard back in 14 days, a nudge on the
advisory thread is fine.

## Disclosure

Coordinated disclosure is preferred. Once a fix is released, the advisory will
be published through the GitHub Advisory Database. Reporters are credited by
name or handle unless they ask not to be.

If a report is valid but no fix is practical, that will be stated publicly
rather than left unaddressed.

## Scope

`crest` is a terminal-art CLI. It has no network access, no authentication, no
persistent state, and no core runtime dependencies beyond the Python standard
library. Optional PNG export uses Pillow.

**In scope:**

- Code execution or injection via CLI arguments or the interactive wizard
- Path traversal or unsafe file writes via `--output` on `crest export`
- Unsafe handling of terminal escape sequences in rendered output
- Denial of service through pathological `--width` / `--height` values
- Supply-chain issues in the published PyPI package
- Anything in the release or packaging workflows under `.github/workflows`

**Out of scope:**

- Vulnerabilities in Pillow or other optional dependencies — report those upstream
- Terminal emulator bugs triggered by valid ANSI output
- Resource use from deliberately large dimensions the user chose themselves
- Anything requiring an already-compromised local machine

If you're unsure whether something is in scope, report it anyway.

## Safe harbour

Good-faith research on your own systems will not be met with legal action.
Please don't test against machines you don't own or have permission to use.
