/**
 * Arguments for Search tool
 */
export interface SearchArgs {
    // Define tool-specific arguments
    query: string;
    options?: Record<string, unknown>;
}

/**
 * External API response structure
 */
export interface DedalusResponse {
    // Define API response structure
    data: unknown;
    metadata?: Record<string, unknown>;
}
