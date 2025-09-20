#!/usr/bin/env python3
"""
Simple test script for the speech-to-text integration.
This script tests the SpeechToTextProcessor module functionality.
"""

import asyncio
import os
import sys
import tempfile
import wave
import struct
import math
from pathlib import Path

# Add src directory to path so we can import our module
sys.path.insert(0, str(Path(__file__).parent / "src"))

from speech_to_text_module import SpeechToTextProcessor


def generate_test_audio(duration=2.0, frequency=440, sample_rate=16000):
    """Generate a simple sine wave audio for testing."""
    num_samples = int(duration * sample_rate)
    audio_data = []

    for i in range(num_samples):
        # Generate sine wave
        sample = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
        audio_data.append(struct.pack('<h', sample))

    return b''.join(audio_data)


async def test_basic_functionality():
    """Test basic functionality without requiring actual API key."""
    print("Testing SpeechToTextProcessor initialization...")

    # Test initialization without API key (should raise error)
    try:
        # Clear any existing API key for this test
        old_key = os.environ.get('ELEVENLABS_API_KEY')
        if 'ELEVENLABS_API_KEY' in os.environ:
            del os.environ['ELEVENLABS_API_KEY']

        processor = SpeechToTextProcessor()
        print("❌ Should have raised ValueError for missing API key")
        return False
    except ValueError as e:
        print(f"✅ Correctly raised error for missing API key: {e}")
    finally:
        # Restore API key if it existed
        if old_key:
            os.environ['ELEVENLABS_API_KEY'] = old_key

    # Test with dummy API key
    try:
        processor = SpeechToTextProcessor(api_key="dummy_key_for_testing")
        print("✅ Successfully initialized with dummy API key")
    except Exception as e:
        print(f"❌ Failed to initialize with dummy API key: {e}")
        return False

    # Test adding audio chunks
    try:
        test_audio = generate_test_audio(duration=1.0)
        chunk_size = len(test_audio) // 4  # Split into 4 chunks

        for i in range(4):
            start = i * chunk_size
            end = start + chunk_size if i < 3 else len(test_audio)
            chunk = test_audio[start:end]

            # This will add to buffer but not transcribe (since we have dummy API key)
            await processor.add_audio_chunk(chunk)
            print(f"✅ Added audio chunk {i+1}/4 ({len(chunk)} bytes)")

        # Test buffer flush
        await processor.flush_buffer()
        print("✅ Successfully flushed buffer")

    except Exception as e:
        print(f"❌ Error during audio processing: {e}")
        return False

    print("✅ All basic functionality tests passed!")
    return True


async def test_with_real_api():
    """Test with real API key if available."""
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("⚠️  No ELEVENLABS_API_KEY found. Skipping real API test.")
        print("   Set ELEVENLABS_API_KEY environment variable to test actual transcription.")
        return True

    print("Testing with real ElevenLabs API...")

    try:
        processor = SpeechToTextProcessor(
            api_key=api_key,
            buffer_duration=1.0,  # Short duration for testing
            log_file_path="test_transcription.txt"
        )

        # Set up callback to capture transcription
        transcriptions = []
        def capture_transcription(text):
            transcriptions.append(text)
            print(f"📝 Transcription received: {text}")

        processor.set_transcription_callback(capture_transcription)

        # Generate longer test audio
        test_audio = generate_test_audio(duration=2.0, frequency=440)

        # Add audio in small chunks to simulate streaming
        chunk_size = 1024
        for i in range(0, len(test_audio), chunk_size):
            chunk = test_audio[i:i+chunk_size]
            await processor.add_audio_chunk(chunk)
            await asyncio.sleep(0.1)  # Simulate real-time streaming

        # Flush remaining buffer
        await processor.flush_buffer()

        # Wait a bit for any pending transcriptions
        await asyncio.sleep(2.0)

        print(f"✅ Test completed. Received {len(transcriptions)} transcription(s).")

        # Check if log file was created
        if os.path.exists("test_transcription.txt"):
            print("✅ Transcription log file created successfully")
            with open("test_transcription.txt", 'r') as f:
                content = f.read()
                print(f"📄 Log file content:\n{content}")

        return True

    except Exception as e:
        print(f"❌ Error during real API test: {e}")
        return False


async def main():
    """Run all tests."""
    print("🧪 Starting speech-to-text module tests...\n")

    # Test basic functionality
    basic_test_passed = await test_basic_functionality()
    print()

    # Test with real API if available
    api_test_passed = await test_with_real_api()
    print()

    if basic_test_passed and api_test_passed:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))