# Ultimate Agents Hackathon

This project is our submission for the Ultimate Agents Hackathon, the biggest hackathon yet in London. We are building with cutting-edge AI agent tools to compete for fun, and to learn.

## The Team

- Hans
- Claude
- Spyros
- Callum

## Getting started
This project makes use of `pyenv` for python version management and `poetry` for virtual environment/ dependency management. To get started with these tools, you can refer to [Python dev](https://www.notion.so/facultyai/Tips-and-tricks-027fd336f3b34e3ba4f487899826bb12?pvs=4) in Notion.

```bash
#Clone the repository using your preferred method(SSH vs HTTPS)
git clone <repo_url>
cd <repo>
```
```bash
#Create the poetry virtual environment (if you don't have a compatible version of python on your system
#you might have to install it !!Danger platform user see pyenv in Notion above!!)
poetry install
```
```bash
#you can now run all packages installed such as pre-commit, ruff and pytest using
poetry run <package>
```

Note `poetry shell` has been deprecated in 2.0.0, use `eval $(poetry env activate)` to create a poetry shell.

## Local development
Relying on the remote CI pipeline to check your code leads to slow development iteration. Locally, you can trigger:

- linting & formatting checks : `poetry run pre-commit run --all-files`
- tests: `poetry run pytest tests/`

## Streaming Client

This project includes a Dedalus streaming client that connects to a WebSocket server.

### Running the Example

1.  **Start the server:** The included server in `src/Dedalus/src/server.ts` is configured to listen for WebSocket connections. To start it, navigate to the `src/Dedalus` directory and run:
    ```bash
    npm install
    npm run build
    npm start
    ```
2.  **Run the client:** In a separate terminal, navigate to `src/Dedalus` and run the example client:
    ```bash
    node dist/streaming-client-example.js
    ```

The client will connect to the server, send a dummy audio chunk, and close the connection.

## ElevenLabs Speech-to-Text Module

This project includes a standalone speech-to-text module using the ElevenLabs API, available in both TypeScript and Python implementations.

### Features

- **Multi-format Support**: MP3, WAV, FLAC, AAC, OGG, WebM audio + MP4, AVI, MKV video
- **Multiple Input Methods**: File paths or audio buffers
- **Flexible Output**: JSON, text, SRT, VTT, or verbose JSON responses
- **Timestamps**: Word-level and segment-level timing data
- **99 Languages**: Full ElevenLabs language support
- **Environment Configuration**: Secure API key management

### Python Setup

1. **Install Dependencies:**
   ```bash
   cd src/Dedalus
   pip install -r requirements.txt
   ```

2. **Configure API Key:**
   ```bash
   cp .env.example .env
   # Edit .env and add your ElevenLabs API key
   ```

3. **Run Example:**
   ```bash
   python src/speech_to_text_example.py
   ```

### TypeScript Setup

1. **Build the Module:**
   ```bash
   cd src/Dedalus
   npm install
   npm run build
   ```

2. **Configure API Key:**
   ```bash
   cp .env.example .env
   # Edit .env and add your ElevenLabs API key
   ```

3. **Run Example:**
   ```bash
   node dist/speech-to-text-example.js
   ```

### Usage Examples

**Python:**
```python
from speech_to_text_example import ElevenLabsSpeechToText

# From environment variable
stt = ElevenLabsSpeechToText.from_env()

# Transcribe file
result = stt.transcribe_file("audio.mp3", response_format="verbose_json")
print(result["text"])

# Transcribe buffer
with open("audio.mp3", "rb") as f:
    buffer_result = stt.transcribe_buffer(f.read(), "audio.mp3")
```

**TypeScript:**
```typescript
import { ElevenLabsSpeechToText } from './speech-to-text.js';

const stt = ElevenLabsSpeechToText.fromEnv();
const result = await stt.transcribeFile('audio.mp3');
console.log(result.text);
```

### API Key Setup

Get your ElevenLabs API key from [https://elevenlabs.io/docs/introduction](https://elevenlabs.io/docs/introduction) and add it to your `.env` file:

```
ELEVENLABS_API_KEY=your_api_key_here
```

## Real-time Speech-to-Text WebSocket Server

This project includes a real-time speech-to-text WebSocket server that streams audio to ElevenLabs for live transcription.

### Features

- **Real-time Audio Processing**: Processes audio streams every 1 second
- **WebSocket Integration**: Receives audio data via WebSocket connections
- **Live Transcription**: Uses ElevenLabs Speech-to-Text API for high-quality transcription
- **Automatic Logging**: Saves transcriptions to timestamped log files
- **Pause Detection**: Basic pause detection in audio streams
- **Microphone Support**: Includes client for live microphone streaming

### Quick Start

1. **Set up your ElevenLabs API key:**
   ```bash
   export ELEVENLABS_API_KEY="your_api_key_here"
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Start the WebSocket server:**
   ```bash
   uv run uvicorn src.websocket_server:app --host 0.0.0.0 --port 8000
   ```

4. **Run the microphone client (in a new terminal):**
   ```bash
   # Install audio dependencies first
   pip install pyaudio websockets

   # Run the microphone client
   uv run python src/microphone_client.py
   ```

### Usage Examples

#### Live Microphone Transcription

The `microphone_client.py` provides a complete example of streaming microphone audio for live transcription:

- **Real-time streaming**: Captures microphone audio and streams to WebSocket
- **Live transcription**: Displays transcriptions as you speak
- **File logging**: Saves all transcriptions to `live_transcription.txt`
- **Graceful shutdown**: Use Ctrl+C to stop

```bash
uv run python src/microphone_client.py
```

#### Custom WebSocket Client

You can also create your own WebSocket client. The protocol is:

1. Connect to `ws://localhost:8000/ws`
2. Send initial JSON message: `{"prompt": "session_name", "duration": 3600}`
3. Send audio data as binary messages
4. Receive JSON responses with transcription and pause detection

Example response format:
```json
{
    "is_there_a_pause": false,
    "transcription": "Hello, this is the transcribed text"
}
```

### Audio Requirements

- **Format**: 16-bit PCM audio
- **Sample Rate**: 16,000 Hz recommended
- **Channels**: Mono (1 channel) recommended
- **Chunk Size**: 1024 bytes recommended for real-time streaming

### Output Files

- **Server logs**: Console output with detailed WebSocket activity
- **Transcription logs**: `transcription_log_{session_name}.txt` with timestamped transcriptions
- **Client logs**: `live_transcription.txt` with real-time transcriptions

### Troubleshooting

**PyAudio Installation Issues:**
```bash
# macOS
brew install portaudio
pip install pyaudio

# Ubuntu/Debian
sudo apt-get install python3-pyaudio

# Windows
pip install pipwin
pipwin install pyaudio
```

**Connection Issues:**
- Ensure the WebSocket server is running on port 8000
- Check that your `ELEVENLABS_API_KEY` environment variable is set
- Verify your microphone permissions are granted

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. It also includes a custom license in [LICENSE.txt](LICENSE.txt).