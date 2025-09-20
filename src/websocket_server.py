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
import os
from datetime import datetime
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
       "is_there_a_pause" (bool) and the processed audio data as a binary
       message.

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

        # Create debug directory for audio batches
        debug_dir = "debug_audio_batches"
        os.makedirs(debug_dir, exist_ok=True)
        batch_counter = 0

        # Set up transcription callback
        latest_transcription = {"text": ""}

        def transcription_callback(text: str):
            latest_transcription["text"] = text
            logger.info(f"New transcription available: {text}")

        stt_processor.set_transcription_callback(transcription_callback)

        # Loop to process audio stream
        while True:
            try:
                # Receive 2-second audio batch from the client
                logger.info("⏳ Waiting for 2-second audio batch...")

                # Use asyncio.wait_for to add timeout for batch reception
                audio_batch = await asyncio.wait_for(
                    websocket.receive_bytes(),
                    timeout=10.0,  # 10 second timeout for 2-second batches
                )

                batch_counter += 1
                logger.info(f"📦 Received audio batch #{batch_counter}: {len(audio_batch)} bytes")

                # Save the 2-second batch for debugging
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                batch_filename = os.path.join(debug_dir, f"batch_{batch_counter:04d}_{timestamp}.webm")

                try:
                    with open(batch_filename, "wb") as f:
                        f.write(audio_batch)
                    logger.info(f"💾 Saved 2-second audio batch: {batch_filename}")

                    # Analyze the batch for speech-to-text debugging
                    if len(audio_batch) > 0:
                        # Check if it's all zeros (silence)
                        if all(b == 0 for b in audio_batch):
                            logger.warning("⚠️ Audio batch contains only zeros (complete silence)")
                        # Check for potential white noise patterns
                        elif len(set(audio_batch)) < 50:  # Very low variety
                            logger.warning("⚠️ Audio batch has very low variety - likely white noise or silence")
                        else:
                            logger.info(f"✅ Audio batch #{batch_counter} appears to contain varied audio data")

                        # Show byte distribution for debugging
                        if len(audio_batch) >= 1000:  # Sample first 1000 bytes
                            sample = audio_batch[:1000]
                            unique_bytes = len(set(sample))
                            logger.info(f"🔍 Batch analysis: {unique_bytes} unique byte values in first 1000 bytes")
                    else:
                        logger.warning("⚠️ Empty audio batch received")

                except Exception as e:
                    logger.error(f"Failed to save audio batch: {e}")

                # Process the complete 2-second batch for speech-to-text
                logger.info("🎯 Processing 2-second batch for speech-to-text...")
                await stt_processor.add_audio_chunk(audio_batch)

                # Send response back with transcription results
                response_data = {
                    "batch_number": batch_counter,
                    "batch_size_bytes": len(audio_batch),
                    "transcription": latest_transcription["text"]
                    if latest_transcription["text"]
                    else "No speech detected in this batch",
                }
                await websocket.send_json(response_data)
                logger.info(f"📤 Sent response for batch #{batch_counter}: '{latest_transcription['text']}'")

                # Reset transcription for next batch
                latest_transcription["text"] = ""

            except asyncio.TimeoutError:
                logger.info("⏰ Timeout waiting for audio batch - client may be processing or stopped")
                response_data = {"status": "waiting", "message": "Waiting for next 2-second audio batch..."}
                await websocket.send_json(response_data)

            except Exception as e:
                logger.error(f"Error processing audio data: {e}")
                break

    except WebSocketDisconnect:
        logger.info(f"🔌 Client disconnected. Processed {batch_counter} audio batches total.")

        # Flush any remaining audio in the buffer before closing
        if "stt_processor" in locals():
            await stt_processor.flush_buffer()
            logger.info("✅ Flushed remaining audio from speech-to-text buffer")

    except Exception as e:
        logger.error(f"❌ An error occurred: {e}")
        logger.info(
            f"📊 Session summary: Processed {batch_counter if 'batch_counter' in locals() else 0} audio batches before error"
        )

        # Flush any remaining audio in the buffer before closing
        if "stt_processor" in locals():
            await stt_processor.flush_buffer()
        await websocket.close(code=1011)
