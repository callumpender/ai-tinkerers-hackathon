"""
Standalone Speech-to-Text module using ElevenLabs API.

This module provides functionality to transcribe audio data using ElevenLabs
Speech-to-Text API. Since ElevenLabs STT doesn't support real-time streaming,
this module buffers audio chunks and processes them in batches.
"""

import os
import asyncio
import logging
from io import BytesIO
from typing import Optional, Callable
import tempfile
import wave
from elevenlabs.client import ElevenLabs


class SpeechToTextProcessor:
    """
    A processor for converting audio streams to text using ElevenLabs STT API.

    This class handles buffering of audio chunks and batch processing them
    through ElevenLabs STT API since real-time streaming is not yet available.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        buffer_duration: float = 3.0,
        sample_rate: int = 16000,
        channels: int = 1,
        sample_width: int = 2,
        log_file_path: str = "transcription_log.txt"
    ):
        """
        Initialize the Speech-to-Text processor.

        Args:
            api_key: ElevenLabs API key. If None, will try to get from environment.
            buffer_duration: Duration in seconds to buffer audio before transcription.
            sample_rate: Audio sample rate in Hz.
            channels: Number of audio channels.
            sample_width: Sample width in bytes (2 for 16-bit audio).
            log_file_path: Path to log file for transcriptions.
        """
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ElevenLabs API key not provided. Set ELEVENLABS_API_KEY environment variable.")

        self.client = ElevenLabs(api_key=self.api_key)
        self.buffer_duration = buffer_duration
        self.sample_rate = sample_rate
        self.channels = channels
        self.sample_width = sample_width
        self.log_file_path = log_file_path

        # Audio buffer
        self.audio_buffer = BytesIO()
        self.buffer_start_time = None

        # Callbacks
        self.transcription_callback: Optional[Callable[[str], None]] = None

        # Logger
        self.logger = logging.getLogger(__name__)

    def set_transcription_callback(self, callback: Callable[[str], None]):
        """Set a callback function to be called when transcription is available."""
        self.transcription_callback = callback

    async def add_audio_chunk(self, audio_data: bytes):
        """
        Add an audio chunk to the buffer for processing.

        Args:
            audio_data: Raw audio data bytes.
        """
        if self.buffer_start_time is None:
            self.buffer_start_time = asyncio.get_event_loop().time()

        self.audio_buffer.write(audio_data)

        # Check if buffer duration has been reached
        current_time = asyncio.get_event_loop().time()
        if current_time - self.buffer_start_time >= self.buffer_duration:
            await self._process_buffer()

    async def _process_buffer(self):
        """Process the current audio buffer and transcribe it."""
        if self.audio_buffer.tell() == 0:
            return  # No data in buffer

        try:
            # Get audio data from buffer
            self.audio_buffer.seek(0)
            audio_data = self.audio_buffer.read()

            # Create a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name

                # Write WAV file
                with wave.open(temp_path, 'wb') as wav_file:
                    wav_file.setnchannels(self.channels)
                    wav_file.setsampwidth(self.sample_width)
                    wav_file.setframerate(self.sample_rate)
                    wav_file.writeframes(audio_data)

            # Transcribe using ElevenLabs
            transcription = await self._transcribe_file(temp_path)

            if transcription and transcription.strip():
                await self._handle_transcription(transcription)

            # Clean up temp file
            os.unlink(temp_path)

        except Exception as e:
            self.logger.error(f"Error processing audio buffer: {e}")
        finally:
            # Reset buffer
            self.audio_buffer.seek(0)
            self.audio_buffer.truncate(0)
            self.buffer_start_time = None

    async def _transcribe_file(self, file_path: str) -> Optional[str]:
        """
        Transcribe an audio file using ElevenLabs STT API.

        Args:
            file_path: Path to the audio file to transcribe.

        Returns:
            Transcribed text or None if transcription failed.
        """
        try:
            # Run the synchronous API call in a thread pool
            loop = asyncio.get_event_loop()

            def sync_transcribe():
                with open(file_path, 'rb') as audio_file:
                    return self.client.speech_to_text.convert(
                        file=audio_file,
                        model_id="scribe_v1",
                        language_code="eng"  # You can make this configurable
                    )

            result = await loop.run_in_executor(None, sync_transcribe)

            # Extract text from the result
            if hasattr(result, 'text'):
                return result.text
            elif isinstance(result, str):
                return result
            else:
                self.logger.warning(f"Unexpected transcription result format: {type(result)}")
                return str(result)

        except Exception as e:
            self.logger.error(f"Error transcribing audio: {e}")
            return None

    async def _handle_transcription(self, transcription: str):
        """Handle a completed transcription."""
        self.logger.info(f"Transcription: {transcription}")

        # Log to file
        await self._log_transcription(transcription)

        # Call callback if set
        if self.transcription_callback:
            self.transcription_callback(transcription)

    async def _log_transcription(self, transcription: str):
        """Log transcription to file."""
        try:
            import datetime
            timestamp = datetime.datetime.now().isoformat()
            log_entry = f"[{timestamp}] {transcription}\n"

            # Append to log file
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)

        except Exception as e:
            self.logger.error(f"Error logging transcription: {e}")

    async def flush_buffer(self):
        """Process any remaining audio in the buffer."""
        if self.audio_buffer.tell() > 0:
            await self._process_buffer()