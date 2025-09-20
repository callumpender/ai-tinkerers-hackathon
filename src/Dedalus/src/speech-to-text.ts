import fetch from 'node-fetch';
import FormData from 'form-data';
import fs from 'fs';
import path from 'path';

export interface TranscriptionOptions {
  model?: string;
  language?: string;
  timestamp_granularities?: ('word' | 'segment')[];
  response_format?: 'json' | 'text' | 'srt' | 'verbose_json' | 'vtt';
}

export interface TranscriptionResult {
  text: string;
  segments?: Array<{
    id: number;
    seek: number;
    start: number;
    end: number;
    text: string;
    tokens: number[];
    temperature: number;
    avg_logprob: number;
    compression_ratio: number;
    no_speech_prob: number;
  }>;
  words?: Array<{
    word: string;
    start: number;
    end: number;
  }>;
}

export class ElevenLabsSpeechToText {
  private apiKey: string;
  private baseUrl = 'https://api.elevenlabs.io';

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async transcribeFile(
    filePath: string,
    options: TranscriptionOptions = {}
  ): Promise<TranscriptionResult> {
    if (!fs.existsSync(filePath)) {
      throw new Error(`File not found: ${filePath}`);
    }

    const formData = new FormData();
    formData.append('file', fs.createReadStream(filePath));

    if (options.model) formData.append('model', options.model);
    if (options.language) formData.append('language', options.language);
    if (options.response_format) formData.append('response_format', options.response_format);
    if (options.timestamp_granularities) {
      formData.append('timestamp_granularities[]', options.timestamp_granularities.join(','));
    }

    const response = await fetch(`${this.baseUrl}/v1/speech-to-text`, {
      method: 'POST',
      headers: {
        'xi-api-key': this.apiKey,
        ...formData.getHeaders(),
      },
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`ElevenLabs API error: ${response.status} ${response.statusText} - ${errorText}`);
    }

    if (options.response_format === 'text') {
      const text = await response.text();
      return { text };
    }

    return await response.json() as TranscriptionResult;
  }

  async transcribeBuffer(
    audioBuffer: Buffer,
    filename: string,
    options: TranscriptionOptions = {}
  ): Promise<TranscriptionResult> {
    const formData = new FormData();
    formData.append('file', audioBuffer, {
      filename: filename,
      contentType: this.getMimeType(filename),
    });

    if (options.model) formData.append('model', options.model);
    if (options.language) formData.append('language', options.language);
    if (options.response_format) formData.append('response_format', options.response_format);
    if (options.timestamp_granularities) {
      formData.append('timestamp_granularities[]', options.timestamp_granularities.join(','));
    }

    const response = await fetch(`${this.baseUrl}/v1/speech-to-text`, {
      method: 'POST',
      headers: {
        'xi-api-key': this.apiKey,
        ...formData.getHeaders(),
      },
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`ElevenLabs API error: ${response.status} ${response.statusText} - ${errorText}`);
    }

    if (options.response_format === 'text') {
      const text = await response.text();
      return { text };
    }

    return await response.json() as TranscriptionResult;
  }

  private getMimeType(filename: string): string {
    const ext = path.extname(filename).toLowerCase();
    const mimeTypes: { [key: string]: string } = {
      '.mp3': 'audio/mpeg',
      '.wav': 'audio/wav',
      '.flac': 'audio/flac',
      '.aac': 'audio/aac',
      '.ogg': 'audio/ogg',
      '.webm': 'audio/webm',
      '.mp4': 'video/mp4',
      '.avi': 'video/avi',
      '.mkv': 'video/x-matroska',
    };
    return mimeTypes[ext] || 'audio/mpeg';
  }

  static fromEnv(envKey: string = 'ELEVENLABS_API_KEY'): ElevenLabsSpeechToText {
    const apiKey = process.env[envKey];
    if (!apiKey) {
      throw new Error(`Environment variable ${envKey} is not set`);
    }
    return new ElevenLabsSpeechToText(apiKey);
  }
}

export default ElevenLabsSpeechToText;
