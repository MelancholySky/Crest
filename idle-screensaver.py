#!/usr/bin/env python3
"""Idle screensaver: Launch crest after N seconds of terminal inactivity.

Usage:
    python3 idle-screensaver.py [--idle-time SECONDS] [--pattern PATTERN] [--color COLOR]

Examples:
    python3 idle-screensaver.py                                    # 5 min default
    python3 idle-screensaver.py --idle-time 60                     # 1 minute
    python3 idle-screensaver.py --pattern wave --color matrix      # Custom pattern
    python3 idle-screensaver.py --idle-time 120 --pattern ripple

Press Ctrl+C or any key to cancel/exit the screensaver.
"""

from __future__ import annotations

import argparse
import getpass
import os
import subprocess
import sys
import time


def parse_who_idle(text: str, user: str) -> int:
    """Parse `who -u` output and return the user's idle time in seconds.

    Fields per line: USER LINE DATE TIME IDLE PID [COMMENT].
    The user is only idle when ALL their pts/tty sessions are idle, so
    the smallest idle time among their sessions is returned. Returns 0
    if the user has no pts/tty session. Malformed lines are skipped.
    """
    smallest = None
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 6:
            continue
        if parts[0] != user or not parts[1].startswith(("pts", "tty")):
            continue
        idle_field = parts[4]
        try:
            if idle_field == ".":
                seconds = 0
            elif idle_field == "old":
                seconds = 86400  # idle for over 24 hours
            elif ":" in idle_field:
                hours, minutes = idle_field.split(":", 1)
                seconds = int(hours) * 3600 + int(minutes) * 60
            else:
                continue
        except ValueError:
            continue
        if smallest is None or seconds < smallest:
            smallest = seconds
    return smallest if smallest is not None else 0


def get_idle_time() -> float:
    """Get terminal idle time in seconds (Linux/Unix).

    Uses 'who -u' output for the current user's sessions.
    Falls back to 0 if unable to determine.
    """
    try:
        result = subprocess.run(
            ["who", "-u"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        if result.returncode == 0:
            user = os.environ.get("USER") or getpass.getuser()
            return parse_who_idle(result.stdout, user)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return 0


def launch_screensaver(
    pattern: str = "plasma",
    color: str = "matrix",
    speed: float = 0.08,
    delay: float = 0.05,
) -> None:
    """Launch the crest screensaver animation."""
    try:
        subprocess.run(
            [
                "python3",
                "-m",
                "crest.cli",
                "animate",
                "--pattern",
                pattern,
                "--color",
                color,
                "--speed",
                str(speed),
                "--delay",
                str(delay),
            ],
            check=False,
        )
    except KeyboardInterrupt:
        print("\nScreensaver cancelled.", file=sys.stderr)
    except FileNotFoundError:
        print("Error: crest CLI not found. Install with: pip install -e .", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Monitor idle time and launch screensaver when threshold reached."""
    parser = argparse.ArgumentParser(
        description="Launch crest screensaver after idle time.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 idle-screensaver.py                    # 5 min (default)
  python3 idle-screensaver.py --idle-time 60     # 1 minute
  python3 idle-screensaver.py --pattern wave     # Different pattern
  python3 idle-screensaver.py --idle-time 300 --pattern ripple --color ocean
        """,
    )
    parser.add_argument(
        "--idle-time",
        type=int,
        default=300,
        help="Idle time before screensaver (seconds, minimum 1, default 300/5min)",
    )
    parser.add_argument(
        "--pattern",
        default="plasma",
        help="Crest pattern: wave, plasma, ripple, gradient, mandala (default: plasma)",
    )
    parser.add_argument(
        "--color",
        default="matrix",
        help="Crest colour map: matrix, ocean, fire, rainbow, etc. (default: matrix)",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=0.08,
        help="Animation speed (default: 0.08)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.05,
        help="Frame delay in seconds (default: 0.05)",
    )

    args = parser.parse_args()
    if args.idle_time < 1:
        print("error: --idle-time must be at least 1 second", file=sys.stderr)
        sys.exit(2)

    print(f"Idle screensaver active (idle timeout: {args.idle_time}s)")
    print("Press Ctrl+C to exit monitoring")
    print()

    last_activity_time = time.time()
    screensaver_active = False

    try:
        while True:
            current_idle = get_idle_time()

            if current_idle >= args.idle_time:
                if not screensaver_active:
                    print(f"Idle threshold reached ({current_idle}s >= {args.idle_time}s)")
                    print(f"Launching screensaver: {args.pattern} with {args.color} theme")
                    print()
                    screensaver_active = True
                    launch_screensaver(
                        pattern=args.pattern,
                        color=args.color,
                        speed=args.speed,
                        delay=args.delay,
                    )
                    screensaver_active = False
                    print("Screensaver ended. Resuming idle monitoring.")
                    print()
                    last_activity_time = time.time()
            else:
                if screensaver_active:
                    screensaver_active = False
                    last_activity_time = time.time()

            # Check idle time every second
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nIdle screensaver monitoring stopped.", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
