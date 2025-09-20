from __future__ import annotations

import json
import sys
import queue
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
from uuid import uuid4

try:
    import numpy as np
except ImportError:  # pragma: no cover - dependency missing at runtime
    np = None

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover - dependency missing at runtime
    sd = None

try:
    import soundfile as sf
except ImportError:  # pragma: no cover - dependency missing at runtime
    sf = None

from mutagen.mp4 import MP4, MP4StreamInfoError

JSONDict = Dict[str, Any]


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: JSONDict

    def as_json(self) -> JSONDict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


AUDIO_TOOL = ToolDefinition(
    name="dedalus_transcribe_audio",
    description="Accept an .m4a audio file, report its duration, and acknowledge receipt.",
    input_schema={
        "type": "object",
        "properties": {
            "filePath": {
                "type": "string",
                "description": "Absolute or workspace-relative path to the .m4a file to upload.",
            },
        },
        "required": ["filePath"],
    },
)

MIC_RECORD_TOOL = ToolDefinition(
    name="dedalus_record_microphone",
    description="Capture 5 seconds from the default microphone and report loudness statistics.",
    input_schema={"type": "object", "properties": {}, "required": []},
)


def read_requests(stdin: Iterable[str]) -> Iterable[JSONDict]:
    for raw_line in stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError as exc:
            write_response({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Invalid JSON: {exc}"},
            })


def write_response(message: JSONDict) -> None:
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def handle_initialize(request_id: Optional[int]) -> JSONDict:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": "2025-06-18",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "org/dedalus", "version": "0.3.0"},
        },
    }


def handle_list_tools(request_id: Optional[int]) -> JSONDict:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"tools": [AUDIO_TOOL.as_json(), MIC_RECORD_TOOL.as_json()]},
    }


def resolve_audio_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def compute_duration_seconds(path: Path) -> Optional[float]:
    try:
        audio = MP4(path)
    except (MP4StreamInfoError, FileNotFoundError, PermissionError) as exc:
        raise ValueError(str(exc)) from exc

    info = getattr(audio, "info", None)
    if info and getattr(info, "length", None):
        return float(info.length)
    return None


def handle_call_tool(request_id: Optional[int], params: JSONDict) -> Optional[JSONDict]:
    name = params.get("name")
    args = params.get("arguments", {}) or {}

    if name == AUDIO_TOOL.name:
        return handle_audio_tool(request_id, args)
    if name == MIC_RECORD_TOOL.name:
        return handle_microphone_tool(request_id)

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "content": [
                {"type": "text", "text": f"Unknown tool: {name}"},
            ],
            "isError": True,
        },
    }


def handle_audio_tool(request_id: Optional[int], args: JSONDict) -> JSONDict:
    if not isinstance(args, dict) or not isinstance(args.get("filePath"), str):
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": "Error: Invalid arguments for dedalus_transcribe_audio",
                    }
                ],
                "isError": True,
            },
        }

    raw_path = args["filePath"]
    path = resolve_audio_path(raw_path)

    if not path.exists() or not path.is_file():
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: Audio file not found at path: {path}",
                    }
                ],
                "isError": True,
            },
        }

    if path.suffix.lower() != ".m4a":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": "Error: Only .m4a files are supported by this tool",
                    }
                ],
                "isError": True,
            },
        }

    try:
        duration = compute_duration_seconds(path)
    except ValueError as exc:  # pragma: no cover - rare failure path
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: Unable to read audio metadata - {exc}",
                    }
                ],
                "isError": True,
            },
        }

    payload = {
        "message": "Received audio file",
        "durationSeconds": duration,
        "filePath": str(path),
    }

    final_response = {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(payload, indent=2),
                }
            ],
        },
    }

    write_response(final_response)
    return None


def ensure_audio_dependencies() -> Optional[str]:
    if sd is None:
        return "sounddevice is not installed"
    if sf is None:
        return "soundfile is not installed"
    if np is None:
        return "numpy is not installed"
    return None


def handle_microphone_tool(request_id: Optional[int]) -> JSONDict:
    dep_error = ensure_audio_dependencies()
    if dep_error:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: {dep_error}. Install dependencies listed in pyproject.toml.",
                    }
                ],
                "isError": True,
            },
        }

    sample_rate = 16_000
    channels = 1
    chunk_duration = 0.25  # seconds per streamed update
    chunk_frames = int(sample_rate * chunk_duration)

    audio_queue: "queue.Queue[np.ndarray]" = queue.Queue()
    stream_id = f"microphone-{uuid4().hex}"

    write_response(
        {
            "jsonrpc": "2.0",
            "method": "dedalus/microphone-update",
            "params": {
                "streamId": stream_id,
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({"status": "listening", "chunkSeconds": chunk_duration}),
                    }
                ],
            },
        }
    )

    def callback(indata, frames, _time, status):  # pragma: no cover - depends on audio hardware
        if status:
            write_response(
                {
                    "jsonrpc": "2.0",
                    "method": "dedalus/microphone-update",
                    "params": {
                        "streamId": stream_id,
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps({"warning": str(status)}),
                            }
                        ],
                    },
                }
            )
        audio_queue.put(indata.copy())

    try:
        stream = sd.InputStream(
            samplerate=sample_rate,
            channels=channels,
            dtype="float32",
            callback=callback,
            blocksize=chunk_frames,
        )
        stream.start()
    except Exception as exc:  # pragma: no cover - relies on system audio
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: Unable to access microphone - {exc}",
                    }
                ],
                "isError": True,
            },
        }

    captured_chunks = []
    total_frames = 0
    interrupted = False

    try:
        while True:
            chunk = audio_queue.get()
            captured_chunks.append(chunk)
            frames = chunk.shape[0]
            total_frames += frames
            mono_chunk = np.reshape(chunk, (-1,))
            chunk_rms = float(np.sqrt(np.mean(np.square(mono_chunk))))
            chunk_peak = float(np.max(np.abs(mono_chunk)))
            elapsed_seconds = total_frames / sample_rate

            write_response(
                {
                    "jsonrpc": "2.0",
                    "method": "dedalus/microphone-update",
                    "params": {
                        "streamId": stream_id,
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(
                                    {
                                        "elapsedSeconds": elapsed_seconds,
                                        "rms": chunk_rms,
                                        "peak": chunk_peak,
                                    }
                                ),
                            }
                        ],
                    },
                }
            )
    except KeyboardInterrupt:  # pragma: no cover - relies on manual interaction
        interrupted = True
    finally:
        stream.stop()
        stream.close()

    if captured_chunks:
        recording = np.concatenate(captured_chunks, axis=0)
    else:
        recording = np.zeros((0, channels), dtype="float32")

    mono = np.reshape(recording, (-1,))
    peak = float(np.max(np.abs(mono))) if mono.size else 0.0
    rms = float(np.sqrt(np.mean(np.square(mono)))) if mono.size else 0.0
    duration_seconds = recording.shape[0] / sample_rate if recording.size else 0.0

    if rms < 0.01:
        loudness = "very quiet"
    elif rms < 0.05:
        loudness = "moderate"
    else:
        loudness = "loud"

    target_path = Path.cwd() / "microphone_capture.wav"
    if recording.size:
        sf.write(target_path, recording, sample_rate)
    elif target_path.exists():
        target_path.unlink()

    status_text = "interrupted" if interrupted else "completed"

    payload = {
        "message": "Captured microphone audio",
        "durationSeconds": duration_seconds,
        "sampleRate": sample_rate,
        "rms": rms,
        "peak": peak,
        "loudnessCategory": loudness,
        "savedFile": str(target_path) if recording.size else None,
        "streamId": stream_id,
        "interrupted": interrupted,
    }

    write_response(
        {
            "jsonrpc": "2.0",
            "method": "dedalus/microphone-update",
            "params": {
                "streamId": stream_id,
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({"status": status_text}),
                    }
                ],
            },
        }
    )

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(payload, indent=2),
                }
            ],
        },
    }


def dispatch_request(request: JSONDict) -> None:
    method = request.get("method")
    request_id = request.get("id")

    if method == "initialize":
        write_response(handle_initialize(request_id))
    elif method == "tools/list":
        write_response(handle_list_tools(request_id))
    elif method == "tools/call":
        params = request.get("params") or {}
        response = handle_call_tool(request_id, params)
        if response is not None:
            write_response(response)
    else:
        write_response(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Unsupported method: {method}",
                },
            }
        )


def run() -> None:
    print("Dedalus MCP Python server listening on stdio", file=sys.stderr)
    try:
        for request in read_requests(sys.stdin):
            dispatch_request(request)
    except KeyboardInterrupt:
        print("Dedalus MCP server shutting down", file=sys.stderr)


if __name__ == "__main__":
    run()
