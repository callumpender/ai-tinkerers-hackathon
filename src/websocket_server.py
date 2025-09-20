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
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import logging

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

        # Loop to process audio stream
        while True:
            # Receive audio data from the client
            audio_data = await websocket.receive_bytes()
            logger.info(f"Received {len(audio_data)} bytes of audio data.")

            # TODO: Add actual audio processing and pause detection logic here
            # For now, we'll just mock the response
            is_there_a_pause = False  # Mocked value
            processed_audio = audio_data  # Mocked processing (echo back)

            # Send the response back to the client
            await websocket.send_json({"is_there_a_pause": is_there_a_pause})
            await websocket.send_bytes(processed_audio)
            logger.info("Sent processed audio data and pause status.")

            # Add a small delay to prevent a tight loop in this example
            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        logger.info("Client disconnected.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        await websocket.close(code=1011)
