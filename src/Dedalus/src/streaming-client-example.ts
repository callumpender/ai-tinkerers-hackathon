import { StreamingClient } from './streaming-client.js';
import { Buffer } from 'buffer';

async function main() {
    // Replace with your FastAPI WebSocket URL
    const wsUrl = 'ws://localhost:8000/ws';

    const client = new StreamingClient(wsUrl);

    try {
        await client.connect();

        // Example: Send a dummy audio chunk (Buffer)
        const dummyAudio = Buffer.from('dummy audio data');
        client.sendAudio(dummyAudio);

        // Close the connection after a delay
        setTimeout(() => {
            client.close();
        }, 2000);

    } catch (error) {
        console.error('Failed to connect or send data:', error);
    }
}

main();
