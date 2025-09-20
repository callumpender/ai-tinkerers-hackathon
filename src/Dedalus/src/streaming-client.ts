import WebSocket from 'ws';

class StreamingClient {
    private ws: WebSocket | null = null;
    private url: string;

    constructor(url: string) {
        this.url = url;
    }

    public connect(): Promise<void> {
        return new Promise((resolve, reject) => {
            this.ws = new WebSocket(this.url);

            this.ws.on('open', () => {
                console.log('Connected to WebSocket server');
                resolve();
            });

            this.ws.on('message', (data: WebSocket.Data) => {
                // Assuming the received data is audio data
                console.log('Received audio data:', data);
            });

            this.ws.on('error', (error: Error) => {
                console.error('WebSocket error:', error);
                reject(error);
            });

            this.ws.on('close', (code: number, reason: string) => {
                console.log(`WebSocket closed: ${code} - ${reason}`);
            });
        });
    }

    public sendAudio(data: Buffer): void {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(data);
        } else {
            console.error('WebSocket is not open. Cannot send audio data.');
        }
    }

    public close(): void {
        if (this.ws) {
            this.ws.close();
        }
    }
}

export { StreamingClient };
