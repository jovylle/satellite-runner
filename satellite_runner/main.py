#!/usr/bin/env python3
import subprocess
import time
import logging
import sys
from pathlib import Path

LOGFILE = Path.home() / "satellite_runner.log"

logging.basicConfig(
    filename=str(LOGFILE),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPLAY = "/opt/homebrew/bin/ffplay"

def mic_ready() -> bool:
    """Check if mic index :0 works."""
    try:
        subprocess.run(
            [FFMPEG, "-f", "avfoundation", "-i", ":0",
             "-t", "1", "-f", "null", "-"],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        logging.error("ffmpeg not found at %s", FFMPEG)
        sys.exit(1)

def run_satellite():
    """Run the Wyoming Satellite subprocess."""
    cmd = [
        sys.executable, "-m", "wyoming_satellite",
        "--uri", "tcp://0.0.0.0:10700",
        "--name", "MiniMic",
        "--wake-uri", "tcp://127.0.0.1:10400",
        "--wake-command-rate", "16000",
        "--wake-command-width", "2",
        "--wake-command-channels", "1",
        "--mic-command",
        f"{FFMPEG} -f avfoundation -i ':0' "
        "-ac 1 -ar 16000 -c:a pcm_s16le "
        "-filter:a highpass=f=100,lowpass=f=4000,afftdn=nf=-25,volume=3.0 "
        "-f s16le -nostdin -hide_banner -loglevel error -",
        "--mic-command-rate", "16000",
        "--mic-command-width", "2",
        "--mic-command-channels", "1",
        "--snd-command",
        f"{FFMPEG} -hide_banner -loglevel error "
        "-f s24le -ar 22050 -ac 1 -i - "
        "-c:a pcm_s16le -ar 16000 -ac 1 -f s16le pipe:1",
        "--snd-command-rate", "22050",
        "--snd-command-width", "3",
        "--snd-command-channels", "1",
        "--awake-wav", str(Path(__file__).parent / "sounds" / "wake.wav"),
        "--done-wav", str(Path(__file__).parent / "sounds" / "processing.wav"),
        "--no-zeroconf",
        "--debug"
    ]

    logging.info("Starting Wyoming Satellite process...")
    log_file = open(LOGFILE, "a")
    return subprocess.Popen(cmd, stdout=log_file, stderr=log_file)

def main():
    logging.info("===== Satellite runner started =====")
    # Play startup sound once
    startup_sound = Path(__file__).parent / "sounds" / "startup.wav"
    if startup_sound.exists():
        subprocess.Popen([
            FFPLAY, "-nodisp", "-autoexit", "-loglevel", "error",
            str(startup_sound)
        ])
        
    while True:
        if not mic_ready():
            logging.warning("Mic :0 not ready, retrying in 5s...")
            time.sleep(5)
            continue

        process = run_satellite()
        try:
            exit_code = process.wait()
            logging.warning("Satellite exited with code %s. Restarting in 5s...", exit_code)
        except KeyboardInterrupt:
            logging.info("Keyboard interrupt received, stopping runner.")
            process.terminate()
            break
        time.sleep(5)  # backoff before retry

if __name__ == "__main__":
    main()
