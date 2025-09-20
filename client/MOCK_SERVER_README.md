# Mock WebSocket Server

This mock server simulates the backend behavior for the Audio Stream Dashboard client.

## Features

- **Random Pause Intervals**: Triggers pauses every 5-20 seconds (randomized)
- **Pause Duration**: Each pause lasts 2-3 seconds (randomized)
- **Discussion Tips**: Provides helpful conversation tips during pauses
- **WebSocket Communication**: Handles the same message types as the real backend

## Usage

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the mock server:
   ```bash
   npm run mock-server
   ```

3. Start the client application (in another terminal):
   ```bash
   npm run dev
   ```

4. The client will connect to `ws://localhost:8000/audio-stream` by default

## Discussion Tips

The mock server provides random tips such as:
- "Say less, listen more"
- "Ask open-ended questions"
- "Show empathy and understanding"
- "Take a moment to think before responding"
- And many more...

## Message Types

The server handles these message types:
- `status`: Updates conversation status (listening, speaking, paused)
- `pause_detected`: Triggers when a pause is detected
- `speech_detected`: Simulates speech detection
- `recommendations`: Sends discussion tips

## Stopping the Server

Press `Ctrl+C` to stop the mock server gracefully.
