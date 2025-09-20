import { promises as fs } from 'node:fs';
import path from 'node:path';

import { Tool, CallToolResult } from '@modelcontextprotocol/sdk/types.js';

import { DedalusClient } from '../client.js';
import type {
    SearchArgs,
    AudioTranscriptionArgs,
} from '../types.js';

/**
 * Tool definition for search
 */
export const searchToolDefinition: Tool = {
    name: "dedalus_search",
    description: "Description of what this tool does and when to use it.",
    inputSchema: {
        type: "object",
        properties: {
            // Define input schema
        },
        required: ["query"],
    },
};

/**
 * Type guard for search arguments
 */
function isSearchArgs(args: unknown): args is SearchArgs {
    return (
        typeof args === "object" &&
        args !== null &&
        "query" in args &&
        typeof (args as { query: unknown }).query === "string"
    );
}

/**
 * Handles search tool calls
 */
export async function handleSearchTool(
    client: DedalusClient, 
    args: unknown
): Promise<CallToolResult> {
    try {
        if (!args) {
            throw new Error("No arguments provided");
        }

        if (!isSearchArgs(args)) {
            throw new Error("Invalid arguments for dedalus_search");
        }

        const result = await client.performRequest(args);
        
        return {
            content: [{ type: "text", text: result }],
            isError: false,
        };
    } catch (error) {
        return {
            content: [
                {
                    type: "text",
                    text: `Error: ${error instanceof Error ? error.message : String(error)}`,
                },
            ],
            isError: true,
        };
    }
}

/**
 * Tool definition for audio transcription
 */
export const audioTranscriptionToolDefinition: Tool = {
    name: "dedalus_transcribe_audio",
    description: "Accept an .m4a audio file and acknowledge receipt.",
    inputSchema: {
        type: "object",
        properties: {
            filePath: {
                type: "string",
                description: "Absolute or workspace-relative path to the .m4a file to upload.",
            },
        },
        required: ["filePath"],
    },
};

function isAudioTranscriptionArgs(args: unknown): args is AudioTranscriptionArgs {
    return (
        typeof args === "object" &&
        args !== null &&
        typeof (args as { filePath?: unknown }).filePath === "string"
    );
}

export async function handleAudioTranscriptionTool(
    _client: DedalusClient,
    args: unknown
): Promise<CallToolResult> {
    try {
        if (!isAudioTranscriptionArgs(args)) {
            throw new Error("Invalid arguments for dedalus_transcribe_audio");
        }

        const resolvedPath = path.resolve(args.filePath);
        const stats = await fs.stat(resolvedPath).catch(() => {
            throw new Error(`Audio file not found at path: ${resolvedPath}`);
        });

        if (!stats.isFile()) {
            throw new Error(`Audio file not found at path: ${resolvedPath}`);
        }

        if (!resolvedPath.toLowerCase().endsWith('.m4a')) {
            throw new Error("Only .m4a files are supported by this tool");
        }

        // Read the file to emulate accepting the payload. We ignore the bytes afterwards.
        await fs.readFile(resolvedPath);

        return {
            content: [
                {
                    type: "text",
                    text: "Received audio file",
                },
            ],
        };
    } catch (error) {
        return {
            content: [
                {
                    type: "text",
                    text: `Error: ${error instanceof Error ? error.message : String(error)}`,
                },
            ],
            isError: true,
        };
    }
}
