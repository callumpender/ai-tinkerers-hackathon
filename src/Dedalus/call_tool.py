import json
import os
import selectors
import subprocess
from pathlib import Path
from typing import TextIO

AUDIO_PATH = "/Users/hansgunnoo/Documents/ai_tinkerers_hackathon/test_lull.m4a"  # <= update this


def read_line(stream: TextIO, *, label: str, timeout: float = 5.0) -> str:
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
    ["python", "-m", "dedalus_mcp.server"],
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


def send(msg: dict, *, label: str) -> str:
    payload = json.dumps(msg)
    print(f"[debug] sending {label}: {payload}")
    proc.stdin.write(payload + "\n")
    proc.stdin.flush()
    response = read_line(proc.stdout, label=label)
    print(f"[debug] received {label}: {response}")
    return response


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
)

call_response = send(
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
)

print("initialize ->", initialize_response)
print("tools/call ->", call_response)

proc.terminate()
