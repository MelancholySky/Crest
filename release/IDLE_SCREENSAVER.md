# Idle Screensaver

Auto-launch the **crest** screensaver after a period of terminal inactivity.

## Quick Start

```bash
# Default: 5 minutes (300 seconds) idle timeout
python3 idle-screensaver.py

# Custom timeout: 1 minute
python3 idle-screensaver.py --idle-time 60

# Different pattern and color
python3 idle-screensaver.py --pattern wave --color ocean

# 2 minutes with fast ripple effect
python3 idle-screensaver.py --idle-time 120 --pattern ripple --speed 0.1
```

Press **Ctrl+C** to stop monitoring, or press **Ctrl+C** during the screensaver to exit it.

## How It Works

1. The script monitors terminal idle time using the `who -u` command
2. When idle time exceeds the threshold, **crest** launches automatically
3. Any terminal activity stops the screensaver and resumes monitoring
4. Perfect for long-running terminal sessions or demos

## Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--idle-time SECONDS` | 300 | Idle time before screensaver triggers (seconds) |
| `--pattern PATTERN` | plasma | Pattern to display: wave, plasma, ripple, gradient, mandala |
| `--color COLOR` | matrix | Colour map: matrix, ocean, fire, rainbow, viridis, etc. |
| `--speed SPEED` | 0.08 | Animation speed (higher = faster) |
| `--delay DELAY` | 0.05 | Frame delay in seconds (lower = smoother) |

## Use Cases

### Terminal Showcase
Use during demos or talks:
```bash
python3 idle-screensaver.py --idle-time 30 --pattern plasma --color matrix
```
Automatically launches the screensaver after 30 seconds of inactivity.

### Development Environment
Run in a dedicated terminal while working:
```bash
python3 idle-screensaver.py --idle-time 600 --pattern wave --color ocean
```
After 10 minutes of inactivity, the terminal comes alive with animation.

### Warp.dev Integration
Add to your shell profile to auto-enable when opening a new terminal:
```bash
# ~/.config/fish/config.fish or ~/.bashrc
# python3 /path/to/idle-screensaver.py --idle-time 300 &
```

## Customization Examples

### Slow Mandala (Meditative)
```bash
python3 idle-screensaver.py --idle-time 180 --pattern mandala --color viridis --speed 0.03 --delay 0.2
```

### Fast Ripple (Energetic)
```bash
python3 idle-screensaver.py --idle-time 120 --pattern ripple --color fire --speed 0.15 --delay 0.02
```

### Ocean Waves (Calming)
```bash
python3 idle-screensaver.py --idle-time 300 --pattern wave --color ocean --speed 0.05 --delay 0.1
```

### Rainbow Gradient (Festive)
```bash
python3 idle-screensaver.py --pattern gradient --color rainbow --speed 0.1 --delay 0.05
```

## Technical Details

### Platform Support
- **Linux**: Full support via `who -u`
- **macOS**: Should work, verify with `who -u`
- **Windows**: Limited support (WSL recommended)

### Performance
- Minimal CPU overhead while monitoring (1 check/second)
- Zero CPU when idle screensaver not active
- ~5% CPU during active screensaver (depends on terminal size)

### Known Limitations
- Idle time detection is based on system-level terminal activity
- SSH sessions may not report idle time accurately
- Some terminal emulators may not integrate perfectly with `who` command

## Troubleshooting

### Screensaver doesn't launch
1. Verify `crest` is installed: `python3 -m crest.cli --version`
2. Check idle time: `who -u`
3. Try shorter idle timeout: `--idle-time 30`

### Doesn't detect activity
Different terminals report idle time differently. Try:
```bash
who -u
# Look for your terminal session and note the idle time format
```

### High CPU usage
Reduce animation complexity:
```bash
python3 idle-screensaver.py --speed 0.04 --delay 0.1
```

## Integration Ideas

### Prompt Enhancement
Combine with your shell prompt to show when screensaver is running:
```fish
function fish_prompt
    if test -f /tmp/screensaver_active
        echo "🎨 "
    else
        echo "> "
    end
end
```

### Background Process
Run the screensaver in the background across sessions:
```bash
nohup python3 idle-screensaver.py > /dev/null 2>&1 &
echo $! > ~/.idle_screensaver.pid
```

To kill it later:
```bash
kill $(cat ~/.idle_screensaver.pid)
```

### Warp

You can run the idle screensaver in a dedicated Warp tab or split, but note
two caveats specific to Warp:

- Idle detection uses `who -u`, which Warp does not populate the same way as
  a classic terminal, so auto-launch-on-idle may not trigger reliably. Launch
  it manually instead:
  ```bash
  python3 idle-screensaver.py --idle-time 120
  ```
- Live animation (`crest animate`) relies on per-frame screen clears that
  Warp's UI capture does not handle smoothly. For a Warp-friendly still, use
  `crest render` or `crest export` to a PNG.

## See Also

- `matrix-screensaver.sh` / `matrix-screensaver.fish` — Quick one-shot launchers
- `crest animate` — Manual screensaver control
- `crest wizard` — Interactive pattern/color discovery

## Credits

- **hy3** — development and the core idea behind crest.
- **Melancholy Sky** — project author and maintainer.
