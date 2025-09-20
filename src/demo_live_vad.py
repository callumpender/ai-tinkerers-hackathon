#!/usr/bin/env python3
"""
Demo script showing how to query the LiveVADProcessor silence flags.
This demonstrates the high-level API for integrating with other applications.
"""

import time
import sys
import os
import threading

# Add the current directory to path to import live_vad
sys.path.append(os.path.dirname(__file__))

from live_vad import LiveVADProcessor


def check_lull_thread(processor: LiveVADProcessor, stop_event: threading.Event):
    """
    Thread function that continuously checks for silence flags.
    This demonstrates how to use the processor in a separate thread.
    
    Args:
        processor (LiveVADProcessor): The VAD processor instance
        stop_event (threading.Event): Event to signal when to stop the thread
    """
    print("Started lull checking thread...")
    
    while not stop_event.is_set():
        # Check silence flags using the processor
        silence_500ms, silence_2000ms = processor.get_silence_flags()
        _, speech_flag = processor.get_current_vad_result()
        
        # React to different silence states
        if silence_2000ms:
            print("  🔇 Long silence detected (2.0s+) - Agent could act now!")
        elif silence_500ms:
            print("  🤫 Short pause detected (0.5s+) - Monitoring...")
        elif speech_flag:
            print("  🗣️  Active speech detected")
        
        # Wait a bit before checking again
        time.sleep(0.5)
    
    print("Lull checking thread stopped.")


def main():
    """Demo: Start VAD processor and use it in a separate thread to check lull."""
    
    print("Starting Live VAD Demo with Threading...")
    print("This shows how to pass the processor to a thread for lull checking.")
    
    # Create and start the VAD processor
    processor = LiveVADProcessor(
        sample_rate=16000,
        hop_size=256,
        threshold=0.5
    )
    
    # Create event to signal thread termination
    stop_event = threading.Event()
    
    try:
        processor.start()
        print("\nMicrophone active. Speak to test voice activity detection.")
        print("Starting lull checking thread...")
        print("-" * 60)
        
        # Start the thread with the processor
        lull_thread = threading.Thread(
            target=check_lull_thread,
            args=(processor, stop_event),
            daemon=True
        )
        lull_thread.start()
        
        # Main loop shows detailed status
        for i in range(60):  # Run for 30 seconds
            time.sleep(0.5)
            
            # Query the processor for current status  
            silence_500ms, silence_2000ms = processor.get_silence_flags()
            probability, speech_flag = processor.get_current_vad_result()
            
            # Print detailed status
            status_msg = f"[{i*0.5:5.1f}s] "
            status_msg += f"Speech: {'YES' if speech_flag else 'NO '} ({probability:.3f}) | "
            status_msg += f"Silence: 0.5s={'YES' if silence_500ms else 'NO '} | "
            status_msg += f"2.0s={'YES' if silence_2000ms else 'NO '}"
            
            print(status_msg)
    
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Stop the lull checking thread
        stop_event.set()
        if 'lull_thread' in locals() and lull_thread.is_alive():
            lull_thread.join(timeout=1.0)
        
        processor.stop()
        print("Demo completed.")


if __name__ == "__main__":
    main()
