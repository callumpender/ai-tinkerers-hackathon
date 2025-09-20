# Ultimate Agents Hackathon

This project is our submission for the Ultimate Agents Hackathon, the biggest hackathon yet in London. We are building with cutting-edge AI agent tools to compete for fun, and to learn.

## The Team

- Hans
- Claude
- Spyros
- Callum

## FRONTEND setup
npm install

npm run dev


## Getting started
This project makes use of `pyenv` for python version management and `uv` for virtual environment/ dependency management. To get started with these tools, you can refer to [Python dev](https://www.notion.so/facultyai/Tips-and-tricks-027fd336f3b34e3ba4f487899826bb12?pvs=4) in Notion.

### Prerequisites
Make sure you have `uv` and `ffmpeg` installed:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install ffmpeg (required for audio format conversion)
brew install ffmpeg
```

### Installation
```bash
#Clone the repository using your preferred method(SSH vs HTTPS)
git clone <repo_url>
cd <repo>

# Install PortAudio (required for audio capture)
brew install portaudio

```
```bash
#Install the project and its dependencies (if you don't have a compatible version of python on your system
#uv will automatically install it for you)
uv sync
```
To activate the virtual environment in your shell, use:
```bash
source .venv/bin/activate
```


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

- **Real-time Audio Processing**: Captures audio in 2-second batches for transcription
- **WebM to WAV Conversion**: Automatically converts WebM audio to WAV format using ffmpeg
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
   uv pip install -r requirements.txt
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
   uv run uvicorn src.websocket_server:app --host 0.0.0.0 --port 8001
   ```

4. **Run the frontend client (in a new terminal):**
   ```bash
   cd client
   npm install
   npm run dev
   ```

   Then open your browser to `http://localhost:8080` and click "Start Session" to begin audio capture and transcription.

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
