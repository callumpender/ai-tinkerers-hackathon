import { useState, useRef, useCallback } from "react";
import { ConversationStatus } from "@/components/AudioDashboard";

interface UseWebSocketProps {
  url: string;
  onStatusUpdate: (status: ConversationStatus) => void;
  onRecommendations: (recommendations: string[]) => void;
  prompt?: string;
  duration?: number;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
  sendAudioData: (audioData: ArrayBuffer) => void;
  error: string | null;
}

export const useWebSocket = ({
  url,
  onStatusUpdate,
  onRecommendations,
  prompt = "Default conversation analysis prompt",
  duration = 30
}: UseWebSocketProps): UseWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const initialMessageSent = useRef(false);

  const connect = useCallback(async () => {
    try {
      setError(null);

      // If already connected, don't create a new connection
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        return;
      }

      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        reconnectAttempts.current = 0;
        initialMessageSent.current = false;

        // Send initial message with prompt and duration as required by Python server
        const initialMessage = {
          prompt: prompt,
          duration: duration
        };

        if (wsRef.current) {
          wsRef.current.send(JSON.stringify(initialMessage));
          initialMessageSent.current = true;
          onStatusUpdate("listening");
        }
      };

      wsRef.current.onmessage = (event) => {
        try {
          // Handle binary message (processed audio data)
          if (event.data instanceof ArrayBuffer) {
            console.log('Received processed audio data:', event.data.byteLength, 'bytes');
            // For now, we just log the processed audio data
            // Could be used for playback or further processing
            return;
          }

          // Handle JSON message (pause detection)
          const data = JSON.parse(event.data);

          if (data.hasOwnProperty('is_there_a_pause')) {
            if (data.is_there_a_pause) {
              onStatusUpdate("paused");
              // Use actual transcription from backend
              if (data.transcription && data.transcription.trim()) {
                onRecommendations([data.transcription]);
              }
            } else {
              onStatusUpdate("listening");
              // Also handle regular transcription updates
              if (data.transcription && data.transcription.trim()) {
                onRecommendations([data.transcription]);
              }
            }
          } else {
            console.log('Unknown message format:', data);
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      wsRef.current.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        onStatusUpdate("idle");

        // Attempt to reconnect unless manually disconnected
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          console.log(`Attempting to reconnect in ${delay}ms (attempt ${reconnectAttempts.current + 1}/${maxReconnectAttempts})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        }
      };

      // Wait for connection to open
      return new Promise<void>((resolve, reject) => {
        if (wsRef.current) {
          wsRef.current.addEventListener('open', () => resolve());
          wsRef.current.addEventListener('error', () => reject(new Error('Failed to connect to WebSocket')));
        }
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to connect to WebSocket';
      setError(errorMessage);
      throw err;
    }
  }, [url, onStatusUpdate, onRecommendations, prompt, duration]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }

    setIsConnected(false);
    setError(null);
    reconnectAttempts.current = 0;
  }, []);

  const sendAudioData = useCallback((audioData: ArrayBuffer) => {
    if (wsRef.current?.readyState === WebSocket.OPEN && initialMessageSent.current) {
      // Send raw binary audio data as expected by Python server
      wsRef.current.send(audioData);
    } else if (!initialMessageSent.current) {
      console.warn('WebSocket not ready, initial message not sent yet');
    } else {
      console.warn('WebSocket not connected, cannot send audio data');
    }
  }, []);

  return {
    isConnected,
    connect,
    disconnect,
    sendAudioData,
    error
  };
};
