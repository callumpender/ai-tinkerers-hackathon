import json
import os
import selectors
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, TextIO

AUDIO_PATH = "/Users/hansgunnoo/Documents/ai_tinkerers_hackathon/test_lull.m4a"  # <= update this


def read_line(stream: TextIO, *, label: str, timeout: float = 8.0) -> str:
    """Read a single line with a timeout so we can debug stalls."""
    selector = selectors.DefaultSelector()
    selector.register(stream, selectors.EVENT_READ)
    events = selector.select(timeout)
    selector.unregister(stream)

    if not events:
        raise TimeoutError(f"Timed out waiting for {label} response")

    line = stream.readline()
    if not line:
        raise RuntimeError(f"Process ended before {label} response")

    return line.rstrip()



REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHONPATH = str(REPO_ROOT / "src")

proc = subprocess.Popen(
    [sys.executable, "-m", "dedalus_mcp.server"],
    text=True,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=REPO_ROOT,
    env={**os.environ, "PYTHONPATH": PYTHONPATH},
)

# Debug: confirm the server banner appears on stderr.
try:
    banner = read_line(proc.stderr, label="server banner", timeout=2.0)
    print(f"[debug] banner: {banner}")
except TimeoutError:
    print("[debug] no banner emitted (expected on stderr)")


def read_json(stream: TextIO, *, label: str, timeout: float) -> Dict[str, Any]:
    raw = read_line(stream, label=label, timeout=timeout)
    parsed = json.loads(raw)
    print(f"[debug] received {label}: {raw}")
    return parsed


def send(msg: dict, *, label: str, expected_id: int) -> Dict[str, Any]:
    payload = json.dumps(msg)
    print(f"[debug] sending {label}: {payload}")
    proc.stdin.write(payload + "\n")
    proc.stdin.flush()
    while True:
        message = read_json(proc.stdout, label=label, timeout=12.0)
        if message.get("id") == expected_id:
            return message
        if message.get("method") == "dedalus/microphone-update":
            print(f"[stream] {message['params']['content'][0]['text']}")
            continue
        print(f"[debug] ignoring unexpected message: {message}")


try:
    initialize_response = send(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "1.0",
                "capabilities": {},
                "clientInfo": {"name": "manual-cli", "version": "0.1"},
            },
        },
        label="initialize",
        expected_id=1,
    )

    file_response = send(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "dedalus_transcribe_audio",
                "arguments": {"filePath": AUDIO_PATH},
            },
        },
        label="tools/call",
        expected_id=2,
    )

    print("initialize ->", initialize_response)
    print("file tool ->", file_response)

    microphone_response = None
    try:
        microphone_response = send(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "dedalus_record_microphone",
                    "arguments": {},
                },
            },
            label="tools/call (microphone)",
            expected_id=3,
        )
    except KeyboardInterrupt:
        print("\nInterrupted microphone stream; attempting graceful shutdown...")
        try:
            message = read_json(proc.stdout, label="microphone final", timeout=5.0)
            if message.get("id") == 3:
                microphone_response = message
                print("microphone tool ->", microphone_response)
            else:
                print(f"[debug] extra message after interrupt: {message}")
        except (TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
            print(f"[debug] no final response received: {exc}")
    else:
        print("microphone tool ->", microphone_response)
finally:
    proc.terminate()
    try:
        proc.wait(timeout=2.0)
    except subprocess.TimeoutExpired:
        proc.kill()
