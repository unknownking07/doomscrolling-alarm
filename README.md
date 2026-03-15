# Doomscrolling Alarm

**Get back to work.** This tool detects when you switch away from Claude to doomscroll on other apps — and immediately plays the legendary "Why Are You Gay?" video to shame you back into productivity.

## How It Works

1. Monitors which app is currently in focus
2. The moment you leave Claude for *any* other app — the video plays
3. Come back to Claude — the video stops
4. Repeat until you learn your lesson

## Supported Platforms

| Platform | Active Window Detection | Video Player |
|----------|------------------------|--------------|
| macOS    | AppleScript            | QuickTime Player |
| Windows  | Win32 API + psutil     | Default media player |

## Setup

### Prerequisites

- Python 3.8+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (to auto-download the video on first run)

### Install

```bash
git clone https://github.com/unknownking07/doomscrolling-alarm.git
cd doomscrolling-alarm
pip install -r requirements.txt
```

**Windows only:** also install `psutil`:
```bash
pip install psutil
```

### Run

```bash
python main.py
```

The script forks into the background (macOS/Linux) and starts watching.

### Stop

```bash
python main.py stop
```

### Run in foreground (for debugging)

```bash
python main.py --foreground
```

## How It Really Works

```
You: *opens YouTube*
Script: 🎬 "Why are you gay?"
You: *switches back to Claude*
Script: *stops video*
You: *opens Twitter*
Script: 🎬 "Why are you gay?"
You: *closes Twitter forever*
Script: mission accomplished
```

## macOS Permissions

On macOS, you may need to grant your terminal **Accessibility** permissions:

**System Settings → Privacy & Security → Accessibility → Enable your terminal app**

## License

MIT — do whatever you want with it. Just stop doomscrolling.
