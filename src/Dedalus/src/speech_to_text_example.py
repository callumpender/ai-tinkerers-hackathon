#!/usr/bin/env python3
"""
ElevenLabs Speech-to-Text Example

This example demonstrates how to use the ElevenLabs API for speech-to-text transcription
using Python with support for various audio formats and response types.
"""

import os
import json
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ElevenLabsSpeechToText:
    """ElevenLabs Speech-to-Text client for Python."""

    def __init__(self, api_key: str):
        """Initialize with API key."""
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io"

    def transcribe_file(
        self,
        file_path: str,
        model: Optional[str] = None,
        language: Optional[str] = None,
        response_format: str = "json",
        timestamp_granularities: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Transcribe an audio file.

        Args:
            file_path: Path to the audio file
            model: AI model to use (optional)
            language: Language code (e.g., "en", "es", "fr")
            response_format: "json", "text", "srt", "verbose_json", "vtt"
            timestamp_granularities: List of granularities like ["word", "segment"]

        Returns:
            Transcription result as dictionary
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Prepare the request
        url = f"{self.base_url}/v1/speech-to-text"
        headers = {
            "xi-api-key": self.api_key
        }

        # Prepare form data
        data = {}
        if model:
            data["model"] = model
        if language:
            data["language"] = language
        if response_format:
            data["response_format"] = response_format
        if timestamp_granularities:
            data["timestamp_granularities[]"] = ",".join(timestamp_granularities)

        # Open and send file
        with open(file_path, "rb") as audio_file:
            files = {"file": audio_file}
            response = requests.post(url, headers=headers, data=data, files=files)

        # Handle response
        if not response.ok:
            raise Exception(f"ElevenLabs API error: {response.status_code} {response.reason} - {response.text}")

        if response_format == "text":
            return {"text": response.text}

        return response.json()

    def transcribe_buffer(
        self,
        audio_buffer: bytes,
        filename: str,
        model: Optional[str] = None,
        language: Optional[str] = None,
        response_format: str = "json",
        timestamp_granularities: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio from a buffer.

        Args:
            audio_buffer: Audio data as bytes
            filename: Filename for content type detection
            model: AI model to use (optional)
            language: Language code (e.g., "en", "es", "fr")
            response_format: "json", "text", "srt", "verbose_json", "vtt"
            timestamp_granularities: List of granularities like ["word", "segment"]

        Returns:
            Transcription result as dictionary
        """
        url = f"{self.base_url}/v1/speech-to-text"
        headers = {
            "xi-api-key": self.api_key
        }

        # Prepare form data
        data = {}
        if model:
            data["model"] = model
        if language:
            data["language"] = language
        if response_format:
            data["response_format"] = response_format
        if timestamp_granularities:
            data["timestamp_granularities[]"] = ",".join(timestamp_granularities)

        # Get MIME type
        mime_type = self._get_mime_type(filename)

        # Send buffer
        files = {"file": (filename, audio_buffer, mime_type)}
        response = requests.post(url, headers=headers, data=data, files=files)

        # Handle response
        if not response.ok:
            raise Exception(f"ElevenLabs API error: {response.status_code} {response.reason} - {response.text}")

        if response_format == "text":
            return {"text": response.text}

        return response.json()

    def _get_mime_type(self, filename: str) -> str:
        """Get MIME type from filename extension."""
        ext = Path(filename).suffix.lower()
        mime_types = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.flac': 'audio/flac',
            '.aac': 'audio/aac',
            '.ogg': 'audio/ogg',
            '.webm': 'audio/webm',
            '.mp4': 'video/mp4',
            '.avi': 'video/avi',
            '.mkv': 'video/x-matroska',
        }
        return mime_types.get(ext, 'audio/mpeg')

    @classmethod
    def from_env(cls, env_key: str = "ELEVENLABS_API_KEY") -> "ElevenLabsSpeechToText":
        """Create instance from environment variable."""
        api_key = os.getenv(env_key)
        if not api_key:
            raise ValueError(f"Environment variable {env_key} is not set")
        return cls(api_key)


def demonstrate_transcription():
    """Demonstrate various transcription methods."""
    try:
        # Initialize client from environment
        speech_to_text = ElevenLabsSpeechToText.from_env()

        print("ElevenLabs Speech-to-Text Example")
        print("=====================================\n")

        # Example 1: Transcribe from file path
        print("Example 1: Transcribing audio file...")
        audio_file_path = "example-audio.mp3"

        if Path(audio_file_path).exists():
            file_result = speech_to_text.transcribe_file(
                audio_file_path,
                response_format="verbose_json",
                timestamp_granularities=["word", "segment"]
            )

            print("File transcription result:")
            print("Text:", file_result.get("text", ""))
            print("Segments:", len(file_result.get("segments", [])))
            print("Words with timestamps:", len(file_result.get("words", [])))
        else:
            print(f"Audio file not found: {audio_file_path}")
            print("Please provide an audio file to test file transcription.")

        print("\n" + "=" * 50 + "\n")

        # Example 2: Transcribe from buffer
        print("Example 2: Transcribing from buffer...")

        if Path(audio_file_path).exists():
            with open(audio_file_path, "rb") as f:
                audio_buffer = f.read()

            buffer_result = speech_to_text.transcribe_buffer(
                audio_buffer,
                "audio.mp3",
                response_format="json",
                language="en"
            )

            print("Buffer transcription result:")
            print("Text:", buffer_result.get("text", ""))
        else:
            print("No audio file available for buffer example.")

        print("\n" + "=" * 50 + "\n")

        # Example 3: Different response formats
        print("Example 3: Different response formats...")

        if Path(audio_file_path).exists():
            text_result = speech_to_text.transcribe_file(
                audio_file_path,
                response_format="text"
            )

            print("Text-only result:", text_result.get("text", ""))

    except Exception as error:
        print("Error during transcription:", str(error))

        if "Environment variable" in str(error):
            print("\nPlease set up your .env file with your ElevenLabs API key:")
            print("1. Copy .env.example to .env")
            print("2. Add your ElevenLabs API key to the ELEVENLABS_API_KEY variable")
            print("3. Get your API key from https://elevenlabs.io/docs/introduction")


def demonstrate_formats():
    """Show supported formats and usage patterns."""
    print("\nSupported Audio Formats:")
    print("========================")
    print("Audio: MP3, WAV, FLAC, AAC, OGG, WebM")
    print("Video: MP4, AVI, MKV (audio will be extracted)")
    print("")
    print("Usage patterns:")
    print("- File transcription: speech_to_text.transcribe_file(file_path, **options)")
    print("- Buffer transcription: speech_to_text.transcribe_buffer(buffer, filename, **options)")
    print("- Environment setup: ElevenLabsSpeechToText.from_env()")
    print("")
    print("Available options:")
    print("- model: AI model to use (optional)")
    print("- language: Language code (e.g., 'en', 'es', 'fr')")
    print("- response_format: 'json', 'text', 'srt', 'verbose_json', 'vtt'")
    print("- timestamp_granularities: ['word', 'segment'] for detailed timing")


if __name__ == "__main__":
    demonstrate_transcription()
    demonstrate_formats()