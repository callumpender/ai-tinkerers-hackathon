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
import base64
import json
import logging
import os
import time
import random
import threading
import time
from speech_to_text_module import SpeechToTextProcessor
from live_vad import LiveVADProcessor

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


def delayed_prompt_sender(prompt: str, websocket: WebSocket, log_file_path: str, vad_processor: LiveVADProcessor, debug: bool = False):
    """
    Agent that sleeps for 10 seconds then uses OpenAI to analyze transcription data.
    Has access to read_file and clear_file tools.
    
    Args:
        prompt (str): The original prompt
        websocket (WebSocket): The WebSocket connection
        log_file_path (str): Path to the transcription log file
        vad_processor (LiveVADProcessor): The VAD processor for checking silence flags
        debug (bool): If True, read_file returns random content instead of reading actual file
    """
    def read_file():
        """Read content from the log file or return random content if debug mode."""
        if debug:
            # Return random content for debugging
            debug_options = [
                "I'm feeling confident about my presentation today. I think I've prepared well and I'm ready to share my ideas.",
                "Um, I'm not sure if this is the right approach. Maybe we should consider other options before moving forward."
            ]
            content = random.choice(debug_options)
            logger.info(f"Agent read DEBUG content: {content[:50]}...")
            return content
        
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Agent read {len(content)} characters from file")
            return content
        except FileNotFoundError:
            logger.warning(f"Log file {log_file_path} not found")
            return ""
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return ""
    
    def clear_file():
        """Clear the content of the log file."""
        try:
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write("")
            logger.info(f"Agent cleared file: {log_file_path}")
            return True
        except Exception as e:
            logger.error(f"Error clearing file: {e}")
            return False
    
    def check_lull():
        """
        Check for silence periods in the audio stream using the VAD processor.
        
        Returns:
            dict: Contains silence5 and silence20 flags
        """
        # Get actual silence flags from the VAD processor
        silence_500ms, silence_2000ms = vad_processor.get_silence_flags()
        
        result = {
            "silence5": silence_500ms,  # 0.5+ seconds of silence
            "silence20": silence_2000ms  # 2.0+ seconds of silence
        }
        
        logger.info(f"Lull check result: {result}")
        
        # Send lull status to websocket to keep frontend informed
        send_lull_status(result)
        
        return result
    
    def send_lull_status(lull_data: dict):
        """Send lull status to the websocket to keep frontend informed."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            status_message = {
                "lull_status": lull_data,
                "timestamp": time.time()
            }
            
            loop.run_until_complete(websocket.send_json(status_message))
            loop.close()
            logger.info(f"Sent lull status to frontend: {lull_data}")
            return True
        except Exception as e:
            logger.error(f"Error sending lull status to websocket: {e}")
            return False
    
    def write_to_ws(message: str):
        """Send a message to the websocket client and clear the file."""
        try:
            clear_result = clear_file()
            
            # Then send the message
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            ws_message = {
                "agent_message": message,
                "timestamp": time.time()
            }
            
            loop.run_until_complete(websocket.send_json(ws_message))
            loop.close()
            logger.info(f"Agent sent message to websocket: {message} (file cleared: {clear_result})")
            return True
        except Exception as e:
            logger.error(f"Error sending message to websocket: {e}")
            return False
    
    # Agent tools definition for OpenAI
    tools = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read the current content of the transcription log file",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_lull",
                "description": "Check for silence periods in the audio stream. Returns silence5 (.5 + seconds of silence) and silence20 (2 + seconds of silence) flags.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "write_to_ws",
                "description": "Send a confidence message to the websocket client and automatically clear the transcription file. Should be either 'You are confident' or 'You are not confident' based on transcription analysis.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The confidence message to send. Should be 'You are confident' or 'You are not confident'"
                        }
                    },
                    "required": ["message"]
                }
            }
        }
    ]
    
    time.sleep(4)
    
    try:
        # Initialize OpenAI client
        client = OpenAI()  # Uses OPENAI_API_KEY environment variable
        
        # Create the agent prompt
        system_prompt = f"""You are an AI agent continuously monitoring transcription data. You have access to three tools:
1. read_file() - Read the current transcription log file content
2. check_lull() - Check for silence periods (returns silence5 (0.5+ seconds) and silence20 (2+ seconds) flags)
3. write_to_ws(message) - Send a confidence message to the websocket client (this automatically clears the file)

Your monitoring logic:
1. CONTINUOUSLY check for silence using check_lull()
2. WHEN silence5 flag is True (0.5+ seconds of silence):
   - Read the transcription file 
   - Analyze the confidence level of the text
3. WHEN silence20 flag is True (2+ seconds of silence):
   - Send confidence message using write_to_ws() - either "You are confident" or "You are not confident"
4. KEEP MONITORING - you may send multiple messages as the conversation continues

Important notes:
- You run continuously and may send multiple confidence assessments
- Only read/analyze when silence5 is True (indicates a natural pause)
- Only send messages when silence20 is True (indicates user is done speaking)
- When you call write_to_ws(), the transcription file will be automatically cleared
- Keep looping to monitor ongoing conversation

Base your confidence assessment on:
- Clarity and coherence of the transcribed text
- Length and completeness of the transcription
- Presence of garbled or nonsensical words
- Overall quality and usefulness of the content

Original user prompt was: "{prompt}"
File path: {log_file_path}"""

        # Make the OpenAI call with tools for continuous monitoring
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Start continuous monitoring. Check silence flags and respond appropriately based on the monitoring logic."}
            ],
            tools=tools,
            tool_choice="auto"
        )
        
        # Process tool calls if any
        message = response.choices[0].message
        tool_results = []
        
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                
                if tool_name == "read_file":
                    result = read_file()
                    tool_results.append({
                        "tool": "read_file",
                        "result": result
                    })
                elif tool_name == "check_lull":
                    result = check_lull()
                    tool_results.append({
                        "tool": "check_lull",
                        "result": result
                    })
                elif tool_name == "write_to_ws":
                    # Parse the message argument from the tool call
                    args = json.loads(tool_call.function.arguments)
                    message_text = args.get("message", "")
                    result = write_to_ws(message_text)
                    tool_results.append({
                        "tool": "write_to_ws",
                        "message": message_text,
                        "result": result,
                        "file_cleared": True
                    })
        
        # Send response back via websocket
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        response_data = {
            "agent_analysis": {
                "original_prompt": prompt,
                "file_path": log_file_path,
                "openai_response": message.content,
                "tool_calls_made": len(message.tool_calls) if message.tool_calls else 0,
                "tool_results": tool_results,
                "timestamp": time.time()
            }
        }
        
        loop.run_until_complete(websocket.send_json(response_data))
        loop.close()
        logger.info(f"Agent completed analysis with {len(tool_results)} tool calls")
        
    except Exception as e:
        logger.error(f"Error in agent: {e}")
        # Send error response
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            error_response = {
                "agent_error": {
                    "original_prompt": prompt,
                    "file_path": log_file_path,
                    "error": str(e),
                    "timestamp": time.time()
                }
            }
            loop.run_until_complete(websocket.send_json(error_response))
            loop.close()
        except:
            pass


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
        log_file_path = f"transcription_log_{prompt.replace(' ', '_')}.txt"
        stt_processor = SpeechToTextProcessor(
            buffer_duration=1.0,  # Process audio every 1 second
            log_file_path=log_file_path
        )

        # Initialize VAD processor for silence detection
        vad_processor = LiveVADProcessor(
            sample_rate=16000,
            hop_size=256,
            threshold=0.5
        )
        vad_processor.start()
        logger.info("Started VAD processor for silence detection")

        # Check for debug mode (can be set via environment variable)
        debug_mode = True
        if debug_mode:
            logger.info("🐛 DEBUG MODE")
        
        # Start the delayed prompt sender thread (agent)
        agent_thread = threading.Thread(
            target=delayed_prompt_sender,
            args=(prompt, websocket, log_file_path, vad_processor, debug_mode),
            daemon=True
        )
        agent_thread.start()
        logger.info("Started delayed prompt sender agent thread")

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

        # Start the delayed prompt sender thread
        prompt_thread = threading.Thread(
            target=delayed_prompt_sender,
            args=(prompt, websocket, log_file_path),
            daemon=True
        )
        prompt_thread.start()
        logger.info("Started delayed prompt sender thread")

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
        
        # Stop VAD processor
        if "vad_processor" in locals():
            vad_processor.stop()
            logger.info("Stopped VAD processor")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.info(
            f"Session summary: Processed {batch_counter if 'batch_counter' in locals() else 0} audio batches before error"
        )
        
        # Stop VAD processor on error
        if "vad_processor" in locals():
            vad_processor.stop()
            logger.info("Stopped VAD processor due to error")

        # Flush any remaining audio in the buffer before closing
        if "stt_processor" in locals():
            await stt_processor.flush_buffer()
        await websocket.close(code=1011)
