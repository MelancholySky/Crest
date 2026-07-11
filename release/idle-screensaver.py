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
import subprocess
import sys
import time
from pathlib import Path


def get_idle_time() -> float:
    """Get terminal idle time in seconds (Linux/Unix).
    
    Uses 'who' command to check when the terminal was last active.
    Falls back to 0 if unable to determine.
    """
    try:
        import os
        result = subprocess.run(
            ["who", "-u"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "pts" in line or "tty" in line:
                    parts = line.split()
                    if len(parts) > 2:
                        try:
                            idle_str = parts[-1]
                            if idle_str == "." or ":" not in idle_str:
                                return 0
                            hours, minutes = idle_str.split(":")
                            return int(hours) * 3600 + int(minutes) * 60
                        except (ValueError, IndexError):
                            pass
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
        help="Idle time before screensaver (seconds, default 300/5min)",
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
