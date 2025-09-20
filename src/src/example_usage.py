#!/usr/bin/env python3
"""
Example usage of the speech-to-text WebSocket server.

This example shows how to connect to the WebSocket server and send audio data
for real-time speech-to-text transcription using ElevenLabs.

To use this example:
1. Set your ELEVENLABS_API_KEY environment variable
2. Start the WebSocket server: `uvicorn src.websocket_server:app --host 0.0.0.0 --port 8000`
3. Run this example: `python src/example_usage.py`
"""

import asyncio
import websockets
import json
import struct
import math


def generate_test_audio(duration=5.0, frequency=440, sample_rate=16000):
    """Generate a simple sine wave audio for testing."""
    num_samples = int(duration * sample_rate)
    audio_data = []

    for i in range(num_samples):
        # Generate sine wave
        sample = int(16000 * math.sin(2 * math.pi * frequency * i / sample_rate))
        audio_data.append(struct.pack('<h', sample))

    return b''.join(audio_data)


async def websocket_client_example():
    """Example WebSocket client that sends audio data and receives transcriptions."""
    uri = "ws://localhost:8000/ws"

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket server")

            # Send initial message with prompt and duration
            initial_message = {
                "prompt": "Test session for speech transcription",
                "duration": 30
            }
            await websocket.send(json.dumps(initial_message))
            print(f"Sent initial message: {initial_message}")

            # Generate test audio data
            print("Generating test audio...")
            test_audio = generate_test_audio(duration=10.0)
            chunk_size = 1024  # Send in 1KB chunks

            print(f"Sending {len(test_audio)} bytes of audio in {len(test_audio)//chunk_size} chunks...")

            # Send audio data in chunks
            for i in range(0, len(test_audio), chunk_size):
                chunk = test_audio[i:i+chunk_size]
                await websocket.send(chunk)
                print(f"Sent chunk {i//chunk_size + 1}")

                # Receive response
                try:
                    # Receive JSON response
                    json_response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    response_data = json.loads(json_response)

                    print(f"Received response: {response_data}")

                    if response_data.get('transcription'):
                        print(f"🎤 Transcription: {response_data['transcription']}")

                    # Receive audio data back
                    audio_response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    print(f"Received {len(audio_response)} bytes of processed audio")

                except asyncio.TimeoutError:
                    print("Timeout waiting for response")
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON response: {e}")

                # Small delay between chunks
                await asyncio.sleep(0.5)

            print("Finished sending audio data")

            # Wait a bit for any final transcriptions
            await asyncio.sleep(5.0)

    except websockets.exceptions.ConnectionClosed:
        print("Connection closed by server")
    except Exception as e:
        print(f"Error: {e}")


async def main():
    """Run the example client."""
    print("🎤 Starting WebSocket client example...")
    print("Make sure the server is running: uvicorn src.websocket_server:app --host 0.0.0.0 --port 8000")
    print("And that you have set your ELEVENLABS_API_KEY environment variable")
    print()

    await websocket_client_example()


if __name__ == "__main__":
    asyncio.run(main())