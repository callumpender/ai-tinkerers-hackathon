import { useState, useRef, useCallback } from "react";
import { ConversationStatus } from "@/components/AudioDashboard";

interface UseWebSocketProps {
  url: string;
  onStatusUpdate: (status: ConversationStatus) => void;
  onRecommendations: (recommendations: string[]) => void;
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
  onRecommendations
}: UseWebSocketProps): UseWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

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
        onStatusUpdate("listening");
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Handle different message types from backend
          switch (data.type) {
            case 'status':
              onStatusUpdate(data.status as ConversationStatus);
              break;
            case 'recommendations':
              onRecommendations(data.recommendations || []);
              break;
            case 'pause_detected':
              onStatusUpdate("paused");
              if (data.recommendations) {
                onRecommendations(data.recommendations);
              }
              break;
            case 'speech_detected':
              onStatusUpdate("speaking");
              break;
            case 'error':
              setError(data.message || 'Server error');
              break;
            default:
              console.log('Unknown message type:', data.type);
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
  }, [url, onStatusUpdate, onRecommendations]);

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
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      // Convert ArrayBuffer to base64 for JSON transmission
      const base64Audio = btoa(String.fromCharCode(...new Uint8Array(audioData)));

      const message = {
        type: 'audio_data',
        data: base64Audio,
        timestamp: Date.now()
      };

      wsRef.current.send(JSON.stringify(message));
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
