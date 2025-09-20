import dotenv from 'dotenv';
import { ElevenLabsSpeechToText } from './speech-to-text.js';
import fs from 'fs';

dotenv.config();

async function demonstrateTranscription() {
  try {
    const speechToText = ElevenLabsSpeechToText.fromEnv();

    console.log('ElevenLabs Speech-to-Text Example');
    console.log('=====================================\n');

    // Example 1: Transcribe from file path
    console.log('Example 1: Transcribing audio file...');
    const audioFilePath = './example-audio.mp3';

    if (fs.existsSync(audioFilePath)) {
      const fileResult = await speechToText.transcribeFile(audioFilePath, {
        response_format: 'verbose_json',
        timestamp_granularities: ['word', 'segment']
      });

      console.log('File transcription result:');
      console.log('Text:', fileResult.text);
      console.log('Segments:', fileResult.segments?.length || 0);
      console.log('Words with timestamps:', fileResult.words?.length || 0);
    } else {
      console.log(`Audio file not found: ${audioFilePath}`);
      console.log('Please provide an audio file to test file transcription.');
    }

    console.log('\n' + '='.repeat(50) + '\n');

    // Example 2: Transcribe from buffer (useful for streaming data)
    console.log('Example 2: Transcribing from buffer...');

    if (fs.existsSync(audioFilePath)) {
      const audioBuffer = fs.readFileSync(audioFilePath);

      const bufferResult = await speechToText.transcribeBuffer(audioBuffer, 'audio.mp3', {
        response_format: 'json',
        language: 'en'
      });

      console.log('Buffer transcription result:');
      console.log('Text:', bufferResult.text);
    } else {
      console.log('No audio file available for buffer example.');
    }

    console.log('\n' + '='.repeat(50) + '\n');

    // Example 3: Different response formats
    console.log('Example 3: Different response formats...');

    if (fs.existsSync(audioFilePath)) {
      const textResult = await speechToText.transcribeFile(audioFilePath, {
        response_format: 'text'
      });

      console.log('Text-only result:', textResult.text);
    }

  } catch (error) {
    console.error('Error during transcription:', error);

    if (error instanceof Error) {
      if (error.message.includes('Environment variable')) {
        console.log('\nPlease set up your .env file with your ElevenLabs API key:');
        console.log('1. Copy .env.example to .env');
        console.log('2. Add your ElevenLabs API key to the ELEVENLABS_API_KEY variable');
        console.log('3. Get your API key from https://elevenlabs.io/docs/introduction');
      }
    }
  }
}

// Example of how to use with different audio formats
async function demonstrateFormats() {
  console.log('\nSupported Audio Formats:');
  console.log('========================');
  console.log('Audio: MP3, WAV, FLAC, AAC, OGG, WebM');
  console.log('Video: MP4, AVI, MKV (audio will be extracted)');
  console.log('');
  console.log('Usage patterns:');
  console.log('- File transcription: speechToText.transcribeFile(filePath, options)');
  console.log('- Buffer transcription: speechToText.transcribeBuffer(buffer, filename, options)');
  console.log('- Environment setup: ElevenLabsSpeechToText.fromEnv()');
  console.log('');
  console.log('Available options:');
  console.log('- model: AI model to use (optional)');
  console.log('- language: Language code (e.g., "en", "es", "fr")');
  console.log('- response_format: "json", "text", "srt", "verbose_json", "vtt"');
  console.log('- timestamp_granularities: ["word", "segment"] for detailed timing');
}

if (import.meta.url === `file://${process.argv[1]}`) {
  demonstrateTranscription().then(() => {
    demonstrateFormats();
  });
}