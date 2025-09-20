import { Tool, CallToolResult } from '@modelcontextprotocol/sdk/types.js';
import { DedalusClient } from '../client.js';
import { SearchArgs } from '../types.js';

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
