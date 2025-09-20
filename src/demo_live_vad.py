#!/usr/bin/env python3
"""
Demo script showing how to query the LiveVADProcessor silence flags.
This demonstrates the high-level API for integrating with other applications.
"""

import time
import sys
import os

# Add the current directory to path to import live_vad
sys.path.append(os.path.dirname(__file__))

from live_vad import LiveVADProcessor


def main():
    """Demo: Start VAD processor and periodically query silence flags."""
    
    print("Starting Live VAD Demo...")
    print("This shows how to query silence flags from another application.")
    
    # Create and start the VAD processor
    processor = LiveVADProcessor(
        sample_rate=16000,
        hop_size=256,
        threshold=0.5
    )
    
    try:
        processor.start()
        print("\nMicrophone active. Speak to test voice activity detection.")
        print("Monitoring silence flags every 0.5 seconds...")
        print("-" * 60)
        
        for i in range(60):  # Run for 30 seconds
            time.sleep(0.5)
            
            # Query the processor for current status
            silence_500ms, silence_2000ms = processor.get_silence_flags()
            probability, speech_flag = processor.get_current_vad_result()
            
            # Print status
            status_msg = f"[{i*0.5:5.1f}s] "
            status_msg += f"Speech: {'YES' if speech_flag else 'NO '} ({probability:.3f}) | "
            status_msg += f"Silence: 0.5s={'YES' if silence_500ms else 'NO '} | "
            status_msg += f"2.0s={'YES' if silence_2000ms else 'NO '}"
            
            print(status_msg)
            
            # Example: React to silence flags
            if silence_500ms and not silence_2000ms:
                print("  → Short pause detected (0.5s silence)")
            elif silence_2000ms:
                print("  → Long silence detected (2.0s silence)")
            elif speech_flag:
                print("  → Active speech detected")
    
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        processor.stop()
        print("Demo completed.")


if __name__ == "__main__":
    main()
