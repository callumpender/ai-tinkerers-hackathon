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

    setAudioLevel(rms);

    if (isRecording) {
      animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
    }
  }, [isRecording]);

  const startRecording = useCallback(async () => {
    try {
      setError(null);

      // Check if mediaDevices is supported
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('MediaDevices API not supported in this browser');
      }

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });

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
          // Send each 100ms chunk immediately to backend
          const arrayBuffer = await event.data.arrayBuffer();
          onAudioData(arrayBuffer);
          audioChunks.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        // Clear chunks when recording stops
        audioChunks.length = 0;

        // Notify completion
        if (onRecordingComplete) {
          onRecordingComplete();
        }
      };

      // Start recording in 100ms batches for continuous streaming
      mediaRecorderRef.current.start(100); // 100ms batches
      setIsRecording(true);

      // Start audio level monitoring
      updateAudioLevel();

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
