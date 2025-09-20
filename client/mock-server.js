import { WebSocketServer } from 'ws';
import http from 'http';

// Discussion tips for the mock responses
const discussionTips = [
  "Say less, listen more",
  "Ask open-ended questions",
  "Show empathy and understanding",
  "Take a moment to think before responding",
  "Acknowledge their perspective first",
  "Use 'I' statements instead of 'you' statements",
  "Focus on finding common ground",
  "Be patient and don't interrupt",
  "Ask for clarification when needed",
  "Summarize what you heard to confirm understanding",
  "Stay calm and composed",
  "Look for win-win solutions",
  "Express appreciation for their time",
  "Be specific about your needs",
  "Listen for underlying concerns"
];

class MockWebSocketServer {
  constructor(port = 8000) {
    this.port = port;
    this.server = null;
    this.wss = null;
    this.clients = new Set();
    this.pauseIntervals = new Map(); // Track pause intervals per client
  }

  start() {
    // Create HTTP server
    this.server = http.createServer();

    // Create WebSocket server
    this.wss = new WebSocketServer({
      server: this.server,
      path: '/audio-stream'
    });

    this.wss.on('connection', (ws, req) => {
      console.log('Client connected to mock WebSocket server');
      this.clients.add(ws);

      // Send initial status
      this.sendMessage(ws, {
        type: 'status',
        status: 'listening'
      });

      // Start the random pause simulation for this client
      this.startPauseSimulation(ws);

      ws.on('message', (data) => {
        try {
          const message = JSON.parse(data);
          console.log('Received message:', message.type);

          if (message.type === 'audio_data') {
            // Simulate processing audio data
            this.simulateAudioProcessing(ws);
          }
        } catch (error) {
          console.error('Error parsing message:', error);
        }
      });

      ws.on('close', () => {
        console.log('Client disconnected');
        this.clients.delete(ws);
        this.stopPauseSimulation(ws);
      });

      ws.on('error', (error) => {
        console.error('WebSocket error:', error);
        this.clients.delete(ws);
        this.stopPauseSimulation(ws);
      });
    });

    this.server.listen(this.port, () => {
      console.log(`Mock WebSocket server running on port ${this.port}`);
      console.log(`WebSocket endpoint: ws://localhost:${this.port}/audio-stream`);
    });
  }

  startPauseSimulation(ws) {
    const scheduleNextPause = () => {
      // Random interval between 5-20 seconds
      const interval = Math.random() * (20000 - 5000) + 5000;

      const timeoutId = setTimeout(() => {
        this.triggerPause(ws);
        // Schedule next pause
        scheduleNextPause();
      }, interval);

      this.pauseIntervals.set(ws, timeoutId);
    };

    scheduleNextPause();
  }

  stopPauseSimulation(ws) {
    const timeoutId = this.pauseIntervals.get(ws);
    if (timeoutId) {
      clearTimeout(timeoutId);
      this.pauseIntervals.delete(ws);
    }
  }

  triggerPause(ws) {
    if (ws.readyState !== WebSocket.OPEN) return;

    // Send pause detected message
    this.sendMessage(ws, {
      type: 'pause_detected',
      status: 'paused',
      recommendations: [this.getRandomTip()]
    });

    // After 2-3 seconds, resume listening
    const pauseDuration = Math.random() * 1000 + 2000; // 2-3 seconds
    setTimeout(() => {
      if (ws.readyState === WebSocket.OPEN) {
        this.sendMessage(ws, {
          type: 'status',
          status: 'listening'
        });
      }
    }, pauseDuration);
  }

  simulateAudioProcessing(ws) {
    // Randomly simulate speech detection
    if (Math.random() < 0.3) { // 30% chance
      setTimeout(() => {
        if (ws.readyState === WebSocket.OPEN) {
          this.sendMessage(ws, {
            type: 'speech_detected',
            status: 'speaking'
          });

          // After a short delay, go back to listening
          setTimeout(() => {
            if (ws.readyState === WebSocket.OPEN) {
              this.sendMessage(ws, {
                type: 'status',
                status: 'listening'
              });
            }
          }, 1000 + Math.random() * 2000);
        }
      }, 100);
    }
  }

  getRandomTip() {
    return discussionTips[Math.floor(Math.random() * discussionTips.length)];
  }

  sendMessage(ws, message) {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    }
  }

  stop() {
    if (this.wss) {
      this.wss.close();
    }
    if (this.server) {
      this.server.close();
    }
    console.log('Mock WebSocket server stopped');
  }
}

// Start the mock server
const mockServer = new MockWebSocketServer();
mockServer.start();

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\nShutting down mock server...');
  mockServer.stop();
  process.exit(0);
});

export default MockWebSocketServer;
