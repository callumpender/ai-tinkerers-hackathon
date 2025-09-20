#!/usr/bin/env python3
"""
Real-time microphone audio streaming client for speech-to-text.

This client captures audio from your microphone and streams it to the WebSocket server
for real-time speech-to-text transcription. Transcriptions are saved to a local file.

Requirements:
    pip install pyaudio websockets

Usage:
    1. Start the WebSocket server: `uv run uvicorn src.websocket_server:app --host 0.0.0.0 --port 8000`
    2. Set your ELEVENLABS_API_KEY environment variable
    3. Run this client: `python src/microphone_client.py`
"""

import asyncio
import websockets
import json
import pyaudio
import threading
import signal
import sys
from datetime import datetime


class MicrophoneStreamer:
    def __init__(
        self,
        websocket_url="ws://localhost:8000/ws",
        output_file="live_transcription.txt",
        sample_rate=16000,
        channels=1,
        chunk_size=1024
    ):
        self.websocket_url = websocket_url
        self.output_file = output_file
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size

        # Audio setup
        self.audio = pyaudio.PyAudio()
        self.stream = None

        # WebSocket
        self.websocket = None

        # Control flags
        self.running = False
        self.audio_queue = asyncio.Queue()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        print("\n🛑 Stopping microphone streaming...")
        self.running = False

    def audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio input."""
        if self.running:
            # Put audio data in queue for async processing
            try:
                asyncio.create_task(self.audio_queue.put(in_data))
            except RuntimeError:
                # Handle case where event loop isn't running
                pass
        return (None, pyaudio.paContinue)

    async def setup_audio(self):
        """Setup audio input stream."""
        print(f"🎤 Setting up microphone (Sample Rate: {self.sample_rate}Hz, Channels: {self.channels})")

        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self.audio_callback
            )
            print("✅ Microphone setup complete")
            return True
        except Exception as e:
            print(f"❌ Error setting up microphone: {e}")
            return False

    def cleanup_audio(self):
        """Clean up audio resources."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()

    async def write_transcription(self, text):
        """Write transcription to file with timestamp."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {text}\n")
            print(f"📝 Saved to {self.output_file}: {text}")
        except Exception as e:
            print(f"❌ Error writing to file: {e}")

    async def audio_sender(self):
        """Send audio data to WebSocket."""
        while self.running:
            try:
                # Get audio data from queue with timeout
                audio_data = await asyncio.wait_for(self.audio_queue.get(), timeout=0.1)

                if self.websocket:
                    await self.websocket.send(audio_data)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ Error sending audio: {e}")
                break

    async def message_receiver(self):
        """Receive messages from WebSocket."""
        while self.running:
            try:
                if not self.websocket:
                    await asyncio.sleep(0.1)
                    continue

                # Receive JSON response
                message = await asyncio.wait_for(self.websocket.recv(), timeout=0.5)

                if isinstance(message, str):
                    # JSON message with transcription
                    try:
                        data = json.loads(message)
                        transcription = data.get('transcription', '').strip()

                        if transcription:
                            print(f"🎤 Transcription: {transcription}")
                            await self.write_transcription(transcription)

                        is_pause = data.get('is_there_a_pause', False)
                        if is_pause:
                            print("⏸️  Pause detected")

                    except json.JSONDecodeError:
                        pass
                else:
                    # Binary audio data (we can ignore this echo)
                    pass

            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed:
                print("🔌 WebSocket connection closed")
                break
            except Exception as e:
                print(f"❌ Error receiving message: {e}")
                break

    async def connect_and_stream(self):
        """Main streaming function."""
        try:
            print(f"🔌 Connecting to {self.websocket_url}...")
            async with websockets.connect(self.websocket_url) as websocket:
                self.websocket = websocket
                print("✅ Connected to WebSocket server")

                # Send initial message
                initial_message = {
                    "prompt": f"Live microphone session {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    "duration": 3600  # 1 hour session
                }
                await websocket.send(json.dumps(initial_message))
                print(f"📨 Sent initial message: {initial_message}")

                # Start audio streaming
                if not await self.setup_audio():
                    return

                print("\n🎙️  Starting live transcription...")
                print("💬 Speak into your microphone. Transcriptions will appear here and be saved to file.")
                print("🛑 Press Ctrl+C to stop\n")

                # Clear output file
                with open(self.output_file, 'w') as f:
                    f.write(f"# Live Speech-to-Text Session Started: {datetime.now()}\n\n")

                # Start audio stream
                self.stream.start_stream()
                self.running = True

                # Run sender and receiver concurrently
                await asyncio.gather(
                    self.audio_sender(),
                    self.message_receiver()
                )

        except websockets.exceptions.ConnectionRefused:
            print("❌ Connection refused. Make sure the WebSocket server is running.")
            print("   Start server with: uv run uvicorn src.websocket_server:app --host 0.0.0.0 --port 8000")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.cleanup_audio()
            print("🧹 Cleaned up audio resources")

    async def run(self):
        """Run the microphone streamer."""
        print("🎤 Real-time Speech-to-Text Microphone Client")
        print("=" * 50)
        print(f"📁 Output file: {self.output_file}")
        print(f"🔗 WebSocket URL: {self.websocket_url}")
        print("⚠️  Make sure your ELEVENLABS_API_KEY is set!")
        print()

        await self.connect_and_stream()


async def main():
    """Main function."""
    streamer = MicrophoneStreamer()
    await streamer.run()


if __name__ == "__main__":
    # Check if PyAudio is available
    try:
        import pyaudio
    except ImportError:
        print("❌ PyAudio not found. Install it with:")
        print("   pip install pyaudio")
        print("   # On macOS: brew install portaudio && pip install pyaudio")
        print("   # On Ubuntu: sudo apt-get install python3-pyaudio")
        sys.exit(1)

    asyncio.run(main())