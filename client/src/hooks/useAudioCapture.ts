import { useState, useRef, useCallback } from "react";

interface UseAudioCaptureProps {
  onAudioData: (audioData: ArrayBuffer) => void;
  onRecordingComplete?: () => void;
  sampleRate?: number;
}

interface UseAudioCaptureReturn {
  isRecording: boolean;
  audioLevel: number;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  error: string | null;
}

export const useAudioCapture = ({
  onAudioData,
  onRecordingComplete,
  sampleRate = 16000
}: UseAudioCaptureProps): UseAudioCaptureReturn => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  const updateAudioLevel = useCallback(() => {
    if (!analyserRef.current) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);

    // Calculate RMS level
    const rms = Math.sqrt(
      dataArray.reduce((sum, value) => sum + (value / 255) ** 2, 0) / dataArray.length
    );

    // Additional debugging for audio analysis
    const maxValue = Math.max(...dataArray);
    const minValue = Math.min(...dataArray);
    const avgValue = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;

    // Log audio stats periodically (every ~1 second)
    const now = Date.now();
    if (!updateAudioLevel.lastLog || now - updateAudioLevel.lastLog > 1000) {
      console.log(`Audio stats - RMS: ${rms.toFixed(3)}, Max: ${maxValue}, Min: ${minValue}, Avg: ${avgValue.toFixed(1)}`);

      // Detect potential white noise (very flat frequency response)
      const variance = dataArray.reduce((sum, value) => sum + Math.pow(value - avgValue, 2), 0) / dataArray.length;
      const stdDev = Math.sqrt(variance);

      if (stdDev < 5 && avgValue > 50) {
        console.warn('⚠️ Possible white noise detected - low variance in frequency spectrum');
      } else if (rms < 0.01) {
        console.warn('⚠️ Very low audio signal - microphone may not be capturing sound');
      } else if (rms > 0.1) {
        console.log('✅ Strong audio signal detected');
      }

      updateAudioLevel.lastLog = now;
    }

    setAudioLevel(rms);

    if (isRecording) {
      animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
    }
  }, [isRecording]);

  const startRecording = useCallback(async () => {
    try {
      setError(null);

      console.log('Requesting microphone access...');

      // Check if mediaDevices is supported
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('MediaDevices API not supported in this browser');
      }

      // Request microphone access with detailed constraints
      const constraints = {
        audio: {
          channelCount: 1,
          sampleRate,
          echoCancellation: true,
          noiseSuppression: false, // Disable noise suppression for debugging
          autoGainControl: false,  // Disable auto gain control for debugging
        }
      };

      console.log('Audio constraints:', constraints);

      const stream = await navigator.mediaDevices.getUserMedia(constraints);

      // Log stream information
      const audioTracks = stream.getAudioTracks();
      console.log('Audio tracks:', audioTracks.length);

      if (audioTracks.length > 0) {
        const track = audioTracks[0];
        console.log('Audio track settings:', track.getSettings());
        console.log('Audio track constraints:', track.getConstraints());
        console.log('Audio track capabilities:', track.getCapabilities());
        console.log('Audio track enabled:', track.enabled);
        console.log('Audio track muted:', track.muted);
        console.log('Audio track readyState:', track.readyState);
      } else {
        console.warn('No audio tracks found in the stream');
      }

      streamRef.current = stream;

      // Set up audio context for level monitoring
      audioContextRef.current = new AudioContext({ sampleRate });
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      source.connect(analyserRef.current);

      // Set up MediaRecorder for audio capture
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm; codecs=opus'
      });

      const audioChunks: Blob[] = [];

      mediaRecorderRef.current.ondataavailable = async (event) => {
        if (event.data.size > 0) {
          console.log(`📦 2-second audio batch captured: ${event.data.size} bytes, type: ${event.data.type}`);
          audioChunks.push(event.data);
        } else {
          console.warn('Empty audio batch received');
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        // Send the 2-second batch for speech-to-text processing
        if (audioChunks.length > 0) {
          console.log(`🎯 Sending 2-second batch (${audioChunks.length} chunks) to backend for speech-to-text`);

          const batchBlob = new Blob(audioChunks, { type: audioChunks[0].type });
          const arrayBuffer = await batchBlob.arrayBuffer();

          console.log(`📤 Sending audio batch: ${arrayBuffer.byteLength} bytes`);
          onAudioData(arrayBuffer);

          // Create downloadable batch for debugging
          const url = URL.createObjectURL(batchBlob);
          const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
          const a = document.createElement('a');
          a.href = url;
          a.download = `audio_batch_${timestamp}.webm`;
          a.style.display = 'none';
          document.body.appendChild(a);
          a.click(); // Auto-download for debugging
          document.body.removeChild(a);

          console.log(`💾 Audio batch saved as: audio_batch_${timestamp}.webm`);
        }

        // Clear chunks for next batch
        audioChunks.length = 0;

        // Notify completion for this batch
        if (onRecordingComplete) {
          onRecordingComplete();
        }
      };

      // Start recording in 2-second batches for speech-to-text processing
      mediaRecorderRef.current.start(2000); // 2-second batches
      setIsRecording(true);

      // Start audio level monitoring
      updateAudioLevel();

      console.log('🎙️ Started recording in 2-second batches for speech-to-text processing');

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to access microphone';
      setError(errorMessage);
      console.error('Error starting audio capture:', err);
    }
  }, [onAudioData, sampleRate, updateAudioLevel]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    analyserRef.current = null;
    mediaRecorderRef.current = null;
    setIsRecording(false);
    setAudioLevel(0);
  }, [isRecording]);

  return {
    isRecording,
    audioLevel,
    startRecording,
    stopRecording,
    error
  };
};
