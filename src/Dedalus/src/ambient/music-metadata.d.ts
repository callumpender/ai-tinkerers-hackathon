declare module 'music-metadata' {
    export interface IAudioMetadata {
        format: {
            duration?: number;
        };
    }

    export interface IOptions {
        duration?: boolean;
    }

    export function parseFile(filePath: string, options?: IOptions): Promise<IAudioMetadata>;
}
