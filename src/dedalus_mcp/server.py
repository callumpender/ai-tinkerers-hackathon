from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

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

import tempfile
import asyncio
import threading
import os

from mutagen.mp4 import MP4, MP4StreamInfoError
import openai

JSONDict = Dict[str, Any]


async def process_transcript_with_gpt(transcript_path: str = "transcript.txt") -> str:
    """
    Read transcript file and process it with GPT to generate a response.

    Args:
        transcript_path: Path to the transcript file

    Returns:
        GPT response text
    """
    try:
        # Check if transcript file exists
        if not os.path.exists(transcript_path):
            # Fallback to live_transcription.txt if transcript.txt doesn't exist
            transcript_path = "live_transcription.txt"
            if not os.path.exists(transcript_path):
                return "No transcript file found to process"

        # Read the transcript content
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_content = f.read().strip()

        if not transcript_content:
            return "Transcript file is empty"

        # Initialize OpenAI client
        client = openai.AsyncOpenAI()

        # Generate response using GPT
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are Dedalus, an AI assistant that analyzes speech transcripts and provides helpful responses. Provide concise, relevant feedback based on the transcript content."
                },
                {
                    "role": "user",
                    "content": f"Please analyze this speech transcript and provide a helpful response:\n\n{transcript_content}"
                }
            ],
            max_tokens=500,
            stream=False
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error processing transcript with GPT: {str(e)}"


async def stream_gpt_response_via_websocket(gpt_response: str, websocket_url: str = "ws://localhost:8001/ws/gpt"):
    """
    Stream GPT response back via websocket.

    Args:
        gpt_response: The GPT response text to stream
        websocket_url: WebSocket URL to connect to
    """
    try:
        import websockets
        from datetime import datetime

        async with websockets.connect(websocket_url) as websocket:
            # Send the GPT response as a message
            message = {
                "type": "gpt_response",
                "content": gpt_response,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(message))

            # Wait for acknowledgment
            response = await websocket.recv()
            ack_message = json.loads(response)
            print(f"GPT response acknowledged: {ack_message.get('message', 'Unknown')}", file=sys.stderr)

    except Exception as e:
        print(f"Error streaming GPT response via websocket: {e}", file=sys.stderr)


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


def handle_call_tool(request_id: Optional[int], params: JSONDict) -> JSONDict:
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

    duration_seconds = 5
    sample_rate = 16_000
    channels = 1

    try:
        recording = sd.rec(
            int(duration_seconds * sample_rate),
            samplerate=sample_rate,
            channels=channels,
            dtype="float32",
        )
        sd.wait()
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

    mono = np.squeeze(recording)
    peak = float(np.max(np.abs(mono)))
    rms = float(np.sqrt(np.mean(np.square(mono))))

    if rms < 0.01:
        loudness = "very quiet"
    elif rms < 0.05:
        loudness = "moderate"
    else:
        loudness = "loud"

    target_path = Path.cwd() / "microphone_capture.wav"
    sf.write(target_path, recording, sample_rate)

    # Determine if this is a "true signal" - significant audio activity
    true_signal = rms > 0.02 and peak > 0.1  # Audio above baseline noise

    payload = {
        "message": "Captured 5 seconds from microphone",
        "durationSeconds": duration_seconds,
        "sampleRate": sample_rate,
        "rms": rms,
        "peak": peak,
        "loudnessCategory": loudness,
        "savedFile": str(target_path),
        "trueSignal": true_signal,
    }

    # If true signal detected, trigger GPT processing in background
    if true_signal:
        def trigger_gpt_processing():
            try:
                # Run the async GPT processing
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Process transcript with GPT
                gpt_response = loop.run_until_complete(process_transcript_with_gpt())
                payload["gptResponse"] = gpt_response

                # Stream response via websocket
                loop.run_until_complete(stream_gpt_response_via_websocket(gpt_response))
                loop.close()

            except Exception as e:
                print(f"Error in GPT processing: {e}", file=sys.stderr)

        # Run in background thread to not block the response
        threading.Thread(target=trigger_gpt_processing, daemon=True).start()

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
        write_response(handle_call_tool(request_id, params))
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
    for request in read_requests(sys.stdin):
        dispatch_request(request)


if __name__ == "__main__":
    run()
