/**
 * Arguments for Search tool
 */
export interface SearchArgs {
    query: string;
    options?: Record<string, unknown>;
}

/**
 * Arguments accepted by the audio transcription MCP tool
 */
export interface AudioTranscriptionArgs {
    /** Absolute or workspace-relative path to an .m4a file */
    filePath: string;
}

/**
 * External API response structure
 */
export interface DedalusResponse {
    data: unknown;
    metadata?: Record<string, unknown>;
}
