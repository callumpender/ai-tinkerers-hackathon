import { DedalusResponse } from './types.js';

export class DedalusClient {
    private apiKey: string;
    private baseUrl: string = 'https://api.dedalus.com';

    constructor(apiKey: string) {
        this.apiKey = apiKey;
    }

    /**
     * Performs API request with proper error handling
     */
    async performRequest(params: unknown): Promise<string> {
        const response = await fetch(`${this.baseUrl}/endpoint`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.apiKey}`,
            },
            body: JSON.stringify(params),
        });

        if (!response.ok) {
            let errorText: string;
            try {
                errorText = await response.text();
            } catch {
                errorText = "Unable to parse error response";
            }
            throw new Error(
                `Dedalus API error: ${response.status} ${response.statusText}\n${errorText}`
            );
        }

        const data: DedalusResponse = await response.json();
        return this.formatResponse(data);
    }

    private formatResponse(data: DedalusResponse): string {
        // Format response according to service requirements
        return JSON.stringify(data, null, 2);
    }
}
