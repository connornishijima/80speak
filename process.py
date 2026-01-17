#!/usr/bin/env python3

import os
import json
import shutil
import subprocess
import traceback

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DECTALK_DIR = os.path.join(SCRIPT_DIR, "dectalk")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")

# TTS engine options: "dectalk", "espeak", "auto"
TTS_ENGINE = os.environ.get("TTS_ENGINE", "auto")


def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def check_dectalk_available():
    """Check if DECtalk can run via Wine."""
    if not shutil.which("wine"):
        return False
    say_exe = os.path.join(DECTALK_DIR, "say.exe")
    if not os.path.exists(say_exe):
        return False
    # Quick test to see if wine can execute
    result = subprocess.run(
        ["wine", "--version"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def check_espeak_available():
    """Check if espeak-ng is available."""
    return shutil.which("espeak-ng") is not None


def synthesize_dectalk(phrase, output_file):
    """Synthesize speech using DECtalk via Wine."""
    say_exe = os.path.join(DECTALK_DIR, "say.exe")
    command = ["wine", say_exe, "-w", output_file, phrase]
    print(f"Running: {' '.join(command)}")

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=DECTALK_DIR
    )
    return result.returncode == 0 and os.path.exists(output_file), result.stderr


def synthesize_espeak(phrase, output_file):
    """Synthesize speech using espeak-ng."""
    command = ["espeak-ng", "-w", output_file, phrase]
    print(f"Running: {' '.join(command)}")

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )
    return result.returncode == 0 and os.path.exists(output_file), result.stderr


def get_tts_engine():
    """Determine which TTS engine to use."""
    if TTS_ENGINE == "dectalk":
        return "dectalk"
    elif TTS_ENGINE == "espeak":
        return "espeak"
    else:  # auto
        if check_dectalk_available():
            return "dectalk"
        elif check_espeak_available():
            return "espeak"
        else:
            return None


def process_requests(requests_file="requests.json"):
    """Process text-to-speech requests from a JSON file."""
    requests_path = os.path.join(SCRIPT_DIR, requests_file)

    with open(requests_path, "r") as f:
        reqs = json.load(f)

    engine = get_tts_engine()
    if engine is None:
        print("ERROR: No TTS engine available. Install Wine+DECtalk or espeak-ng.")
        return

    print(f"PROCESSING REQUESTS using {engine}...")
    ensure_output_dir()

    for item in reqs:
        phrase = item["phrase"]
        session = item["session"]

        print("----------------------------------------")
        print(f"SESSION: {session}")
        print(f"PHRASE: {phrase}")
        print("Converting to speech...")

        output_file = os.path.join(OUTPUT_DIR, f"{session}.wav")

        # Remove existing file if present
        if os.path.exists(output_file):
            os.remove(output_file)

        # Synthesize using selected engine
        if engine == "dectalk":
            success, error = synthesize_dectalk(phrase, output_file)
        else:
            success, error = synthesize_espeak(phrase, output_file)

        if success:
            print(f"SUCCESS: Created {output_file}")
        else:
            print(f"ERROR: {error}")

        print("----------------------------------------")

    print("DONE!")

if __name__ == "__main__":
    try:
        process_requests()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure requests.json exists in the script directory.")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except Exception:
        traceback.print_exc()
