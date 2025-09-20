import { useState, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatusIndicator } from "./StatusIndicator";
import { AgentConfig } from "./AgentConfig";
import { ConversationHistory, ConversationMessage } from "./ConversationHistory";
import { useAudioCapture } from "@/hooks/useAudioCapture";
import { useWebSocket } from "@/hooks/useWebSocket";
import { Mic, MicOff, Settings } from "lucide-react";

export interface AgentSettings {
  scenario: string;
  pauseDuration: number;
}

export type ConversationStatus = "idle" | "listening" | "speaking" | "paused";

const WEBSOCKET_URL = "ws://localhost:8000/audio-stream";

export const AudioDashboard = () => {
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [agentSettings, setAgentSettings] = useState<AgentSettings>({
    scenario: "Negotiate career progression with my manager",
    pauseDuration: 2.0
  });
  const [conversationStatus, setConversationStatus] = useState<ConversationStatus>("idle");
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [conversationMessages, setConversationMessages] = useState<ConversationMessage[]>([]);

  const { isRecording, startRecording, stopRecording, audioLevel } = useAudioCapture({
    onAudioData: useCallback((audioData: ArrayBuffer) => {
      sendAudioData(audioData);
    }, [])
  });

  const { isConnected, connect, disconnect, sendAudioData } = useWebSocket({
    url: WEBSOCKET_URL,
    onStatusUpdate: useCallback((status: ConversationStatus) => {
      setConversationStatus(status);
    }, []),
    onRecommendations: useCallback((recs: string[]) => {
      setRecommendations(recs);
      // Add recommendations as agent messages
      if (recs.length > 0) {
        const newMessages: ConversationMessage[] = recs.map((rec, index) => ({
          id: `agent-${Date.now()}-${index}`,
          type: 'agent',
          content: rec,
          timestamp: new Date()
        }));
        setConversationMessages(prev => [...prev, ...newMessages]);
      }
    }, [])
  });

  const handleStartSession = async () => {
    try {
      await connect();
      await startRecording();

      // Add system message for session start
      const startMessage: ConversationMessage = {
        id: `system-${Date.now()}`,
        type: 'system',
        content: `Session started - Scenario: ${agentSettings.scenario}`,
        timestamp: new Date()
      };
      setConversationMessages(prev => [...prev, startMessage]);
    } catch (error) {
      console.error("Failed to start session:", error);
    }
  };

  const handleStopSession = () => {
    stopRecording();
    disconnect();
    setConversationStatus("idle");
    setRecommendations([]);

    // Add system message for session end
    const endMessage: ConversationMessage = {
      id: `system-${Date.now()}`,
      type: 'system',
      content: 'Session ended',
      timestamp: new Date()
    };
    setConversationMessages(prev => [...prev, endMessage]);
  };

  const handleClearHistory = () => {
    setConversationMessages([]);
    setRecommendations([]);
  };

  const getStatusText = () => {
    switch (conversationStatus) {
      case "listening":
        return "Listening to conversation...";
      case "speaking":
        return "Speaker is talking";
      case "paused":
        return "Conversation paused - Agent ready";
      default:
        return "Ready to start";
    }
  };

  return (
    <div className="h-screen bg-background p-6 overflow-hidden">
      <div className="mx-auto max-w-6xl h-full flex flex-col space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Audio Stream Dashboard</h1>
            <p className="text-muted-foreground">Real-time conversation analysis and agent recommendations</p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsConfigOpen(!isConfigOpen)}
            >
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </Button>
          </div>
        </div>

        {/* Configuration Panel */}
        {isConfigOpen && (
          <Card className="p-6 animate-fade-in border-2">
            <AgentConfig
              settings={agentSettings}
              onSettingsChange={setAgentSettings}
              onClose={() => setIsConfigOpen(false)}
            />
          </Card>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
          {/* Status and Controls */}
          <div className="lg:col-span-1">
            <Card className="p-6 text-center h-full border-2">
              <StatusIndicator
                status={conversationStatus}
                audioLevel={audioLevel}
                isRecording={isRecording}
              />
              <div className="mt-6 space-y-4">
                <p className="text-lg font-medium">{getStatusText()}</p>
                <div className="flex justify-center gap-4">
                  {!isRecording ? (
                    <Button
                      onClick={handleStartSession}
                      size="lg"
                      className="gap-2"
                    >
                      <Mic className="h-4 w-4" />
                      Start Session
                    </Button>
                  ) : (
                    <Button
                      onClick={handleStopSession}
                      variant="destructive"
                      size="lg"
                      className="gap-2"
                    >
                      <MicOff className="h-4 w-4" />
                      Stop Session
                    </Button>
                  )}
                </div>

                {/* Scenario and Pause Configuration */}
                <div className="mt-6 p-4 bg-muted/50 rounded-lg space-y-3 border">
                  <div className="text-center">
                    <h3 className="font-medium text-sm text-muted-foreground mb-2">Current Scenario</h3>
                    <p className="text-sm">{agentSettings.scenario}</p>
                  </div>
                  <div className="text-center">
                    <span className="font-medium text-muted-foreground">Pause Duration:</span>
                    <span className="ml-1 font-bold text-primary">{agentSettings.pauseDuration}s</span>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Agent Recommendations - Main Focus */}
          <div className="lg:col-span-2 h-full">
            <ConversationHistory
              messages={conversationMessages}
              status={conversationStatus}
              onClearHistory={handleClearHistory}
            />
          </div>
        </div>

        {/* Session Info */}
        <Card className="p-4 border-2">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-xl font-bold text-primary">{agentSettings.pauseDuration}s</div>
              <div className="text-xs text-muted-foreground">Pause Duration</div>
            </div>
            <div>
              <div className={`text-xl font-bold ${isRecording ? "text-success" : "text-muted-foreground"}`}>
                {isRecording ? "LIVE" : "IDLE"}
              </div>
              <div className="text-xs text-muted-foreground">Recording Status</div>
            </div>
            <div>
              <div className="text-xl font-bold text-warning">{conversationMessages.filter(msg => msg.type === 'agent').length}</div>
              <div className="text-xs text-muted-foreground">Recommendations</div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
