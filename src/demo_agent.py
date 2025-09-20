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

def demo_delayed_prompt_sender(prompt: str, websocket: MockWebSocket, log_file_path: str):
    """
    Demo version of the delayed_prompt_sender function for testing.
    This is a simplified version that doesn't use OpenAI but demonstrates the tool logic.
    """
    
    def read_file():
        """Read content from the log file."""
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
        Demo version of check_lull that simulates different silence states.
        """
        import random
        
        # Simulate different silence patterns for demo
        scenarios = [
            {"silence5": False, "silence20": False},  # No silence
            {"silence5": True, "silence20": False},   # Short pause (analyze but don't send)
            {"silence5": True, "silence20": True},    # Long pause (analyze and send)
        ]
        
        result = random.choice(scenarios)
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
    time.sleep(10)  # Initial delay
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
    
    # Create and start the agent thread
    agent_thread = threading.Thread(
        target=demo_delayed_prompt_sender,
        args=(prompt, mock_ws, log_file_path),
        daemon=True
    )
    
    print(f"📝 Prompt: {prompt}")
    print(f"📁 Log file: {log_file_path}")
    print(f"⏰ Agent will start in 10 seconds...")
    print()
    
    agent_thread.start()
    
    # Wait for agent to complete
    agent_thread.join()
    
    print("\n" + "=" * 50)
    print("📊 Demo Results Summary:")
    print(f"Total messages sent: {len(mock_ws.sent_messages)}")
    
    for i, message in enumerate(mock_ws.sent_messages, 1):
        print(f"  Message {i}: {message}")
    
    print("\n✅ Demo completed!")

if __name__ == "__main__":
    main()
