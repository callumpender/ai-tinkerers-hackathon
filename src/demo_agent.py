"""
Demo script to test the delayed_prompt_sender agent function.
This simulates the agent behavior without requiring a full websocket server.
"""

import asyncio
import json
import logging
import threading
import time
from unittest.mock import Mock
from live_vad import LiveVADProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockWebSocket:
    """Mock WebSocket for testing the agent without a real websocket connection."""
    
    def __init__(self):
        self.sent_messages = []
    
    async def send_json(self, data):
        """Mock send_json method that stores messages instead of sending them."""
        self.sent_messages.append(data)
        logger.info(f"MockWebSocket received: {json.dumps(data, indent=2)}")
        return True

def demo_delayed_prompt_sender(prompt: str, websocket: MockWebSocket, log_file_path: str, vad_processor: LiveVADProcessor, debug: bool = False):
    """
    Demo version of the delayed_prompt_sender function for testing.
    This is a simplified version that doesn't use OpenAI but demonstrates the tool logic.
    """
    
    def read_file():
        """Read content from the log file or return random content if debug mode."""
        if debug:
            # Return random content for debugging
            import random
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
    
    def send_lull_status(lull_data: dict):
        """Send lull status to the websocket to keep frontend informed."""
        try:
            status_message = {
                "lull_status": lull_data,
                "timestamp": time.time()
            }
            
            # Send via mock websocket
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(websocket.send_json(status_message))
            loop.close()
            
            logger.info(f"Sent lull status to frontend: {lull_data}")
            return True
        except Exception as e:
            logger.error(f"Error sending lull status: {e}")
            return False
    
    def check_lull():
        """
        Check for silence periods using VAD processor.
        
        Raises:
            ValueError: If vad_processor is not provided
        """
        if vad_processor is None:
            raise ValueError("VAD processor is required for check_lull function. Please provide a valid LiveVADProcessor instance.")
        
        # Use real VAD processor
        silence_500ms, silence_2000ms = vad_processor.get_silence_flags()
        result = {
            "silence5": silence_500ms,   # 0.5+ seconds of silence
            "silence20": silence_2000ms  # 2.0+ seconds of silence
        }
        
        logger.info(f"Lull check result: {result}")
        
        # Send lull status to websocket to keep frontend informed
        send_lull_status(result)
        
        return result
    
    def write_to_ws(message: str):
        """Send a message to the websocket client and clear the file."""
        try:
            # Clear the file first
            clear_result = clear_file()
            
            # Create message
            ws_message = {
                "agent_message": message,
                "timestamp": time.time()
            }
            
            # Send via mock websocket (this would be async in real version)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(websocket.send_json(ws_message))
            loop.close()
            
            logger.info(f"Agent sent message: {message} (file cleared: {clear_result})")
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    # Demo agent logic - simplified version of the OpenAI workflow
    time.sleep(4)  # Initial delay
    logger.info("Demo agent starting continuous monitoring...")
    
    try:
        # Simulate continuous monitoring loop
        for cycle in range(5):  # Run 5 monitoring cycles for demo
            logger.info(f"--- Monitoring Cycle {cycle + 1} ---")
            
            # Step 1: Always check lull first
            lull_result = check_lull()
            
            # Step 2: If silence5 is True, read and analyze file
            confidence_assessment = None
            if lull_result["silence5"]:
                logger.info("silence5 detected - reading and analyzing file...")
                file_content = read_file()
                
                # Simple confidence assessment based on content
                if len(file_content.strip()) > 20:
                    confidence_assessment = "You are confident"
                else:
                    confidence_assessment = "You are not confident"
                
                logger.info(f"Confidence assessment: {confidence_assessment}")
            
            # Step 3: If silence20 is True, send the confidence message
            if lull_result["silence20"] and confidence_assessment:
                logger.info("silence20 detected - sending confidence message...")
                write_to_ws(confidence_assessment)
            
            # Wait before next cycle
            time.sleep(2)
        
        logger.info("Demo agent completed monitoring cycles")
        
    except Exception as e:
        logger.error(f"Error in demo agent: {e}")

def main():
    """Main demo function."""
    print("🤖 Starting Delayed Prompt Sender Demo")
    print("=" * 50)
    
    # Set up demo parameters
    prompt = "Please analyze my speech confidence"
    log_file_path = "/Users/claudecharest/personal/ai-tinkerers-hackathon/src/demo_transcription.txt"
    
    # Create mock websocket
    mock_ws = MockWebSocket()
    
    # Create and start VAD processor
    vad_processor = LiveVADProcessor(
        sample_rate=16000,
        hop_size=256,
        threshold=0.5
    )
    vad_processor.start()
    print("🎤 Started VAD processor for real silence detection")
    
    # Check for debug mode (can be set via environment variable or hardcoded for demo)
    import os
    debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    if debug_mode:
        print("🐛 DEBUG MODE: Agent will use random content instead of reading files")
    
    # Create and start the agent thread
    agent_thread = threading.Thread(
        target=demo_delayed_prompt_sender,
        args=(prompt, mock_ws, log_file_path, vad_processor, debug_mode),
        daemon=True
    )
    
    print(f"📝 Prompt: {prompt}")
    print(f"📁 Log file: {log_file_path}")
    print("⏰ Agent will start in 4 seconds...")
    print()
    
    agent_thread.start()
    
    try:
        # Wait for agent to complete
        agent_thread.join()
        
        print("\n" + "=" * 50)
        print("📊 Demo Results Summary:")
        print(f"Total messages sent: {len(mock_ws.sent_messages)}")
        
        for i, message in enumerate(mock_ws.sent_messages, 1):
            print(f"  Message {i}: {message}")
        
        print("\n✅ Demo completed!")
    
    finally:
        # Clean up VAD processor
        vad_processor.stop()
        print("🛑 Stopped VAD processor")

if __name__ == "__main__":
    main()
