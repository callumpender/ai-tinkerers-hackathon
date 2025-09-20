"""
This module implements a FastAPI WebSocket server for handling real-time
audio streaming and processing.

The server exposes a WebSocket endpoint at `/ws` that accepts a connection
from a client. It is designed to receive an initial message containing a text
prompt and a duration, followed by a continuous stream of audio data.

In response, the server sends back a boolean indicating if there is a pause
in the audio and the processed audio stream.
"""

import asyncio
import logging
import time
import random
from speech_to_text_module import SpeechToTextProcessor

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for audio streaming and processing.

    This endpoint handles the WebSocket connection from the client. It first
    waits for an initial JSON message containing the prompt and duration.
    After receiving the initial data, it enters a loop to process the
    continuous stream of audio.

    The communication protocol is as follows:
    1. Client connects to the WebSocket endpoint.
    2. Client sends a JSON message with "prompt" (str) and "duration" (int).
    3. Client starts sending audio data as binary messages.
    4. Server receives audio data and sends back a JSON message with
       "is_there_a_pause" (bool), the base64-encoded processed audio chunk,
       and any available transcription text.

    Args:
        websocket (WebSocket): The WebSocket connection object.
    """
    await websocket.accept()
    logger.info("WebSocket connection accepted.")

    try:
        # Receive the initial message with prompt and duration
        initial_message = await websocket.receive_json()
        prompt = initial_message.get("prompt")
        duration = initial_message.get("duration")
        logger.info(f"Received initial message with prompt: '{prompt}' and duration: {duration}s")

        if not isinstance(prompt, str) or not isinstance(duration, int):
            await websocket.close(code=1003, reason="Invalid initial message format")
            logger.warning("Invalid initial message format. Closing connection.")
            return

        # Initialize speech-to-text processor
        stt_processor = SpeechToTextProcessor(
            buffer_duration=1.0,  # Process audio every 1 second
            log_file_path=f"transcription_log_{prompt.replace(' ', '_')}.txt",
        )

        batch_counter = 0

        # Set up transcription callback and accumulated transcript
        latest_transcription = {"text": ""}
        accumulated_transcript = []

        # Random pause timing
        last_pause_time = time.time()
        next_pause_interval = random.uniform(5, 15)  # Random between 5-15 seconds

        def transcription_callback(text: str):
            latest_transcription["text"] = text
            if text.strip():
                accumulated_transcript.append(text)
            logger.info(f"New transcription available: {text}")

        stt_processor.set_transcription_callback(transcription_callback)

        # Loop to process audio stream
        while True:
            try:
                # Receive 100ms audio chunk from the client
                audio_chunk = await asyncio.wait_for(
                    websocket.receive_bytes(),
                    timeout=5.0,  # 5 second timeout for 100ms chunks
                )

                batch_counter += 1
                logger.info(f"Received audio chunk #{batch_counter}: {len(audio_chunk)} bytes")

                # Process the audio chunk for speech-to-text
                await stt_processor.add_audio_chunk(audio_chunk)

                # Check if it's time for a random pause
                current_time = time.time()
                time_since_last_pause = current_time - last_pause_time

                if time_since_last_pause >= next_pause_interval:
                    # Time for a pause event - send accumulated transcript
                    full_transcript = " ".join(accumulated_transcript)
                    response_data = {"is_there_a_pause": True, "transcription": full_transcript}
                    logger.info(f"Pause event triggered. Full transcript: '{full_transcript}'")

                    # Reset for next pause interval
                    last_pause_time = current_time
                    next_pause_interval = random.uniform(5, 15)
                    accumulated_transcript.clear()
                else:
                    # Regular response with latest transcription
                    response_data = {"is_there_a_pause": False, "transcription": latest_transcription["text"]}

                await websocket.send_json(response_data)

                if latest_transcription["text"]:
                    logger.info(f"Transcription: '{latest_transcription['text']}'")

                # Reset latest transcription after sending
                latest_transcription["text"] = ""

            except asyncio.TimeoutError:
                logger.info("Timeout waiting for audio chunk - client may have paused")
                response_data = {"status": "waiting", "message": "Waiting for audio..."}
                await websocket.send_json(response_data)

            except Exception as e:
                logger.error(f"Error processing audio data: {e}")
                break

    except WebSocketDisconnect:
        logger.info(f"Client disconnected. Processed {batch_counter} audio batches total.")

        # Flush any remaining audio in the buffer before closing
        if "stt_processor" in locals():
            await stt_processor.flush_buffer()
            logger.info("Flushed remaining audio from speech-to-text buffer")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.info(
            f"Session summary: Processed {batch_counter if 'batch_counter' in locals() else 0} audio batches before error"
        )

        # Flush any remaining audio in the buffer before closing
        if "stt_processor" in locals():
            await stt_processor.flush_buffer()
        await websocket.close(code=1011)
