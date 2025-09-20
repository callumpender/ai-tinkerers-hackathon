#!/usr/bin/env python3
"""
Live Voice Activity Detection with Microphone Input
Connects to microphone and runs silence detection in separate thread.
"""

import sys
import os
import threading
import queue
import time
import signal
from collections import deque

# Add TEN VAD to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../include")))

import numpy as np
import pyaudio
from ten_vad import TenVad


class SilenceDetector:
    """Thread-safe silence detector that tracks speech activity over time windows."""
    
    def __init__(self, hop_size_ms=16):
        self.hop_size_ms = hop_size_ms
        self.frames_500ms = int(500 / hop_size_ms)  # ~31 frames for 0.5 seconds
        self.frames_2000ms = int(2000 / hop_size_ms)  # ~125 frames for 2 seconds
        
        # Thread-safe deques for tracking recent speech flags
        self.recent_flags_500ms = deque(maxlen=self.frames_500ms)
        self.recent_flags_2000ms = deque(maxlen=self.frames_2000ms)
        
        # Thread lock for safe access
        self._lock = threading.Lock()
        
        # Current silence flags
        self._silence_500ms = False
        self._silence_2000ms = False
    
    def update(self, speech_flag):
        """Thread-safe update with new speech flag."""
        with self._lock:
            self.recent_flags_500ms.append(speech_flag)
            self.recent_flags_2000ms.append(speech_flag)
            
            # Update silence flags
            if len(self.recent_flags_500ms) >= self.frames_500ms:
                self._silence_500ms = sum(self.recent_flags_500ms) == 0
            
            if len(self.recent_flags_2000ms) >= self.frames_2000ms:
                self._silence_2000ms = sum(self.recent_flags_2000ms) == 0
    
    def get_flags(self):
        """Thread-safe getter for silence flags."""
        with self._lock:
            return self._silence_500ms, self._silence_2000ms
    
    def get_status(self):
        """Get detailed status information."""
        with self._lock:
            return {
                'silence_500ms': self._silence_500ms,
                'silence_2000ms': self._silence_2000ms,
                'buffer_500ms_size': len(self.recent_flags_500ms),
                'buffer_2000ms_size': len(self.recent_flags_2000ms),
                'buffer_500ms_ready': len(self.recent_flags_500ms) >= self.frames_500ms,
                'buffer_2000ms_ready': len(self.recent_flags_2000ms) >= self.frames_2000ms
            }


class LiveVADProcessor:
    """Live VAD processor that handles microphone input and silence detection."""
    
    def __init__(self, sample_rate=16000, hop_size=256, threshold=0.5):
        """
        Initialize live VAD processor.
        
        Args:
            sample_rate: Audio sample rate (16kHz required by TEN VAD)
            hop_size: Frame size in samples (256 = 16ms at 16kHz)
            threshold: VAD threshold (0.0-1.0)
        """
        self.sample_rate = sample_rate
        self.hop_size = hop_size
        self.threshold = threshold
        
        # Initialize VAD and silence detector
        self.ten_vad = TenVad(hop_size, threshold)
        self.silence_detector = SilenceDetector(hop_size_ms=16)
        
        # Audio streaming
        self.audio_queue = queue.Queue(maxsize=100)
        self.pyaudio = pyaudio.PyAudio()
        self.stream = None
        
        # Threading
        self.processing_thread = None
        self.running = False
        
        # Statistics
        self.frame_count = 0
        self.start_time = None
        self.last_speech_probability = 0.0
        self.last_speech_flag = 0
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback for incoming audio data."""
        if status:
            print(f"Audio callback status: {status}")
        
        # Convert bytes to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.int16)
        
        # Add to processing queue
        try:
            self.audio_queue.put(audio_data, block=False)
        except queue.Full:
            pass  # Drop frame if queue is full
        
        return (None, pyaudio.paContinue)
    
    def _process_audio_thread(self):
        """Audio processing thread - runs VAD and updates silence detector."""
        while self.running:
            try:
                # Get audio chunk from queue
                audio_chunk = self.audio_queue.get(timeout=0.1)
                
                # Ensure we have exactly hop_size samples
                if len(audio_chunk) >= self.hop_size:
                    # Take first hop_size samples
                    frame_data = audio_chunk[:self.hop_size]
                    
                    # Process with VAD
                    probability, speech_flag = self.ten_vad.process(frame_data)
                    
                    # Update silence detector
                    self.silence_detector.update(speech_flag)
                    
                    # Update statistics
                    self.frame_count += 1
                    self.last_speech_probability = probability
                    self.last_speech_flag = speech_flag
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in audio processing: {e}")
    
    def start(self):
        """Start microphone capture and processing."""
        print("Starting live VAD processor...")
        print(f"Sample rate: {self.sample_rate}Hz, Frame size: {self.hop_size} samples")
        
        self.running = True
        self.start_time = time.time()
        
        # Start audio processing thread
        self.processing_thread = threading.Thread(target=self._process_audio_thread, daemon=True)
        self.processing_thread.start()
        
        # Start microphone stream
        self.stream = self.pyaudio.open(
            format=pyaudio.paInt16,
            channels=1,  # Mono
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.hop_size,
            stream_callback=self._audio_callback
        )
        
        self.stream.start_stream()
        print("Microphone stream started. Listening...")
    
    def stop(self):
        """Stop microphone capture and processing."""
        print("Stopping live VAD processor...")
        self.running = False
        
        # Stop audio stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        # Wait for processing thread
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)
        
        # Cleanup PyAudio
        self.pyaudio.terminate()
        print("Stopped.")
    
    def get_silence_flags(self):
        """Get current silence detection flags."""
        return self.silence_detector.get_flags()
    
    def get_current_vad_result(self):
        """Get the most recent VAD result."""
        return self.last_speech_probability, self.last_speech_flag
    
    def get_detailed_status(self):
        """Get comprehensive status information."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        silence_status = self.silence_detector.get_status()
        
        return {
            'frames_processed': self.frame_count,
            'elapsed_time': elapsed,
            'fps': self.frame_count / elapsed if elapsed > 0 else 0,
            'queue_size': self.audio_queue.qsize(),
            'last_probability': self.last_speech_probability,
            'last_speech_flag': self.last_speech_flag,
            'silence_500ms': silence_status['silence_500ms'],
            'silence_2000ms': silence_status['silence_2000ms'],
            'buffers_ready': {
                '500ms': silence_status['buffer_500ms_ready'],
                '2000ms': silence_status['buffer_2000ms_ready']
            }
        }


def main():
    """Main function - connects to microphone and monitors silence flags."""
    
    # Handle Ctrl+C gracefully
    processor = None
    
    def signal_handler(sig, frame):
        print("\nShutdown signal received...")
        if processor:
            processor.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Create and start processor
        processor = LiveVADProcessor(
            sample_rate=16000,
            hop_size=256,
            threshold=0.5
        )
        
        processor.start()
        
        print("\n" + "="*60)
        print("LIVE VOICE ACTIVITY DETECTION")
        print("="*60)
        print("Speak into your microphone...")
        print("Silence flags: 500ms=no speech in 0.5s, 2000ms=no speech in 2s")
        print("Press Ctrl+C to stop")
        print("="*60)
        
        # Main monitoring loop
        while True:
            time.sleep(0.1)  # Update every 100ms
            
            # Get current status
            status = processor.get_detailed_status()
            
            # Format status line
            status_line = (
                f"\rFrames: {status['frames_processed']:6d} | "
                f"Speech: {status['last_speech_flag']} ({status['last_probability']:.3f}) | "
                f"Silence: 500ms={int(status['silence_500ms'])} 2s={int(status['silence_2000ms'])} | "
                f"FPS: {status['fps']:5.1f} | "
                f"Queue: {status['queue_size']:2d}"
            )
            
            # Add buffer readiness indicators
            if not status['buffers_ready']['500ms']:
                status_line += " [warming up 500ms]"
            elif not status['buffers_ready']['2000ms']:
                status_line += " [warming up 2s]"
            
            print(status_line, end='', flush=True)
    
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        if processor:
            processor.stop()


if __name__ == "__main__":
    main()
