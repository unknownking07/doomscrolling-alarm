import subprocess
import time
import signal
import sys
import os
import platform
from pathlib import Path

CLAUDE_APPS = {"Claude", "Electron"}
VIDEO_PATH = Path(__file__).parent.joinpath("assets", "why-are-you-gay.mp4").resolve()
POLL_INTERVAL = 0.5
PID_FILE = Path(__file__).parent.joinpath(".doomscroll.pid").resolve()
SYSTEM = platform.system()

# --- Active window detection ---

def get_frontmost_app_macos() -> str:
    result = subprocess.run(
        ["osascript", "-e",
         'tell application "System Events" to get name of first application process whose frontmost is true'],
        capture_output=True, text=True, check=False,
    )
    return result.stdout.strip()


def get_frontmost_app_windows() -> str:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()

    # Get the process ID from the window handle
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

    # Get process name from PID
    try:
        import psutil
        proc = psutil.Process(pid.value)
        return proc.name().replace(".exe", "")
    except Exception:
        # Fallback: get window title
        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value


def get_frontmost_app() -> str:
    if SYSTEM == "Darwin":
        return get_frontmost_app_macos()
    elif SYSTEM == "Windows":
        return get_frontmost_app_windows()
    else:
        raise RuntimeError(f"Unsupported platform: {SYSTEM}")


# --- Video playback ---

_video_process = None


def play_video(video_path: Path) -> None:
    global _video_process

    if SYSTEM == "Darwin":
        script = f'''
        tell application "QuickTime Player"
            activate
            set doc to open POSIX file "{video_path}"
            tell doc
                play
            end tell
        end tell
        '''
        subprocess.run(["osascript", "-e", script], capture_output=True, check=False)

    elif SYSTEM == "Windows":
        # Open with default media player
        _video_process = subprocess.Popen(
            ["cmd", "/c", "start", "", str(video_path)],
            shell=False,
        )


def close_video(video_path: Path) -> None:
    global _video_process

    if SYSTEM == "Darwin":
        video_name = video_path.name
        script = f'''
        tell application "QuickTime Player"
            repeat with d in documents
                try
                    if (name of d) is "{video_name}" then
                        stop d
                        close d saving no
                    end if
                end try
            end repeat
        end tell
        '''
        subprocess.run(["osascript", "-e", script], capture_output=True, check=False)

    elif SYSTEM == "Windows":
        # Kill the video player process
        if _video_process:
            try:
                _video_process.terminate()
            except Exception:
                pass
            _video_process = None
        # Also try to kill common media players that might have opened
        for player in ["wmplayer", "Movies & TV", "msedge", "chrome", "vlc"]:
            subprocess.run(
                ["taskkill", "/f", "/im", f"{player}.exe"],
                capture_output=True, check=False,
            )


# --- Video download ---

def download_video() -> bool:
    print("Downloading video...")
    result = subprocess.run(
        [
            "yt-dlp",
            "-f", "mp4",
            "-o", str(VIDEO_PATH),
            "https://www.youtube.com/watch?v=ooOELrGMn14",
        ],
        check=False,
    )
    return result.returncode == 0


# --- Process management ---

def stop_existing():
    """Stop any already-running instance."""
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            if SYSTEM == "Windows":
                subprocess.run(
                    ["taskkill", "/f", "/pid", str(old_pid)],
                    capture_output=True, check=False,
                )
            else:
                os.kill(old_pid, signal.SIGTERM)
            print(f"Stopped previous instance (PID {old_pid})")
        except (ProcessLookupError, ValueError):
            pass
        PID_FILE.unlink(missing_ok=True)


def cleanup(video_playing, *_):
    if video_playing:
        close_video(VIDEO_PATH)
    PID_FILE.unlink(missing_ok=True)
    sys.exit(0)


def daemonize():
    """Fork into background (macOS/Linux only). On Windows, runs in foreground."""
    if SYSTEM == "Windows":
        # On Windows, use pythonw or just run in foreground
        return

    if "--foreground" not in sys.argv:
        pid = os.fork()
        if pid > 0:
            print(f"Doomscroll alarm running in background (PID {pid})")
            print("Run 'python3 main.py stop' to stop it.")
            sys.exit(0)
        os.setsid()


# --- Video player app names (don't count as "left Claude") ---

VIDEO_PLAYER_APPS = {
    "QuickTime Player",       # macOS
    "wmplayer",               # Windows Media Player
    "Microsoft.Media.Player", # Windows 11 Media Player
    "vlc",                    # VLC
}


def is_claude_or_video_player(app: str) -> bool:
    if app in CLAUDE_APPS or app in VIDEO_PLAYER_APPS:
        return True
    # On Windows, the process name might vary
    app_lower = app.lower()
    if "claude" in app_lower:
        return True
    return False


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        stop_existing()
        print("Doomscroll alarm stopped.")
        return

    if not VIDEO_PATH.exists():
        if not download_video():
            print("Failed to download video. Place it manually at:", VIDEO_PATH)
            return

    stop_existing()
    daemonize()

    PID_FILE.write_text(str(os.getpid()))

    video_playing = False
    signal.signal(signal.SIGTERM, lambda *_: cleanup(video_playing))

    print("Watching for app switches... (leave Claude and find out)")

    try:
        while True:
            app = get_frontmost_app()

            if video_playing and app in VIDEO_PLAYER_APPS:
                time.sleep(POLL_INTERVAL)
                continue

            if not is_claude_or_video_player(app):
                if not video_playing:
                    play_video(VIDEO_PATH)
                    video_playing = True
            else:
                if video_playing:
                    close_video(VIDEO_PATH)
                    video_playing = False

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        pass
    finally:
        if video_playing:
            close_video(VIDEO_PATH)
        PID_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
