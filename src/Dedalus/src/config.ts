import dotenv from 'dotenv';
dotenv.config();

export interface Config {
    apiKey: string;
    port: number;
    isProduction: boolean;
}

export function loadConfig(): Config {
    const apiKey = process.env['DEDALUS_API_KEY'];
    if (!apiKey) {
        throw new Error('DEDALUS_API_KEY environment variable is required');
    }

    const port = parseInt(process.env.PORT || '8080', 10);
    const isProduction = process.env.NODE_ENV === 'production';

    return { apiKey, port, isProduction };
}
