# AI Tinkerers Hackathon - Audio Conversation Assistant

A real-time audio conversation assistant that provides AI-powered recommendations during conversations. The application captures audio input, analyzes conversation patterns, and offers helpful suggestions to improve communication.

## Features

- **Real-time Audio Capture**: Continuous audio recording with visual level indicators
- **AI-Powered Recommendations**: Smart suggestions based on conversation context
- **Conversation History**: Track and review conversation messages and recommendations
- **WebSocket Integration**: Real-time communication with backend analysis engine
- **Responsive UI**: Modern, clean interface built with React and Tailwind CSS

## Quick Start

### Prerequisites

- Node.js (v18 or higher)
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-tinkerers-hackathon/client
```

2. Install dependencies:
```bash
npm install
```

3. Start the mock WebSocket server (in one terminal):
```bash
npm run mock-server
```

4. Start the development server (in another terminal):
```bash
npm run dev
```

5. Open your browser and navigate to `http://localhost:5173`

## Usage

1. **Configure Scenario**: Set your conversation context (e.g., "Negotiate career progression with my manager")
2. **Start Session**: Click "Start Session" to begin audio capture
3. **View Recommendations**: AI suggestions will appear in the conversation history
4. **Monitor Status**: Track conversation status (listening, speaking, paused)

## Project Structure

```
src/
├── components/
│   ├── AudioDashboard.tsx    # Main dashboard component
│   ├── ConversationHistory.tsx # Conversation message history
│   ├── Recommendations.tsx   # AI recommendation display
│   └── ui/                   # Reusable UI components
├── hooks/
│   ├── useAudioCapture.ts    # Audio recording functionality
│   └── useWebSocket.ts       # WebSocket communication
└── pages/
    └── Index.tsx             # Main application page
```

## Technologies Used

- **Frontend**: React 18, TypeScript, Vite
- **UI**: shadcn/ui, Tailwind CSS, Lucide React
- **Audio**: Web Audio API
- **Communication**: WebSocket
- **Backend**: Node.js mock server

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run mock-server` - Start mock WebSocket server
- `npm run lint` - Run ESLint

### Mock Server

The included mock server simulates the backend behavior:
- Random pause intervals (5-20 seconds)
- Discussion tips and recommendations
- WebSocket message handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is part of the AI Tinkerers Hackathon.
