import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
    InitializedNotificationSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { DedalusClient } from './client.js';
import {
    searchToolDefinition,
    handleSearchTool,
} from './tools/index.js';

export function createStandaloneServer(apiKey: string): Server {
    const serverInstance = new Server(
        {
            name: "org/dedalus",
            version: "0.2.0",
        },
        {
            capabilities: {
                tools: {},
            },
        }
    );

    const dedalusClient = new DedalusClient(apiKey);

    serverInstance.setNotificationHandler(InitializedNotificationSchema, async () => {
        console.log('Dedalus MCP client initialized');
    });

    serverInstance.setRequestHandler(ListToolsRequestSchema, async () => ({
        tools: [searchToolDefinition],
    }));

    serverInstance.setRequestHandler(CallToolRequestSchema, async (request) => {
        const { name, arguments: args } = request.params;

        switch (name) {
            case "dedalus_search":
                return await handleSearchTool(dedalusClient, args);
            default:
                return {
                    content: [{ type: "text", text: `Unknown tool: ${name}` }],
                    isError: true,
                };
        }
    });

    return serverInstance;
}

export class DedalusServer {
    private apiKey: string;

    constructor(apiKey: string) {
        this.apiKey = apiKey;
    }

    getServer(): Server {
        return createStandaloneServer(this.apiKey);
    }
}

import * as http from 'http';
import * as WebSocket from 'ws';

export function startWebSocketServer() {
    const server = http.createServer();
    const wss = new WebSocket.Server({ noServer: true });

    wss.on('connection', ws => {
        console.log('Client connected');
        ws.on('message', message => {
            console.log(`Received message: ${message}`);
            ws.send(`Echo: ${message}`);
        });
        ws.on('close', () => {
            console.log('Client disconnected');
        });
    });

    server.on('upgrade', (request, socket, head) => {
        const pathname = request.url;

        if (pathname === '/ws') {
            wss.handleUpgrade(request, socket, head, ws => {
                wss.emit('connection', ws, request);
            });
        } else {
            socket.destroy();
        }
    });

    server.listen(8000, () => {
        console.log('WebSocket server started on port 8000');
    });
}
