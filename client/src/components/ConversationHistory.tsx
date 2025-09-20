import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MessageSquare, Bot, User, Clock, Trash2 } from "lucide-react";
import { ConversationStatus } from "./AudioDashboard";
import { useEffect, useRef } from "react";

export interface ConversationMessage {
  id: string;
  type: 'user' | 'agent' | 'system';
  content: string;
  timestamp: Date;
  status?: ConversationStatus;
}

interface ConversationHistoryProps {
  messages: ConversationMessage[];
  status: ConversationStatus;
  onClearHistory: () => void;
}

export const ConversationHistory = ({ messages, status, onClearHistory }: ConversationHistoryProps) => {
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    if (scrollAreaRef.current) {
      setTimeout(() => {
        scrollAreaRef.current!.scrollTop = scrollAreaRef.current!.scrollHeight;
      }, 100);
    }
  }, [messages]);

  const getMessageIcon = (type: ConversationMessage['type']) => {
    switch (type) {
      case 'user':
        return <User className="h-4 w-4" />;
      case 'agent':
        return <Bot className="h-4 w-4" />;
      case 'system':
        return <Clock className="h-4 w-4" />;
    }
  };

  const getMessageColor = (type: ConversationMessage['type']) => {
    switch (type) {
      case 'user':
        return 'bg-primary text-primary-foreground';
      case 'agent':
        return 'bg-success text-success-foreground';
      case 'system':
        return 'bg-muted text-muted-foreground';
    }
  };

  const formatTime = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <Card className="h-full flex flex-col border-2">
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Agent Recommendations</h3>
          <div className="flex items-center gap-2">
            {status !== 'idle' && (
              <Badge variant={status === 'paused' ? 'default' : 'secondary'}>
                <MessageSquare className="h-3 w-3 mr-1" />
                {status === 'listening' ? 'Listening to conversation' :
                 status === 'paused' ? 'Ready' :
                 status === 'speaking' ? 'Speaking detected' : ''}
              </Badge>
            )}
            {messages.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={onClearHistory}
                className="gap-2"
              >
                <Trash2 className="h-3 w-3" />
                Clear
              </Button>
            )}
          </div>
        </div>
      </div>

      <div
        ref={scrollAreaRef}
        className="flex-1 p-4 overflow-y-auto"
        style={{ maxHeight: 'calc(100vh - 200px)' }}
      >
        <div className="space-y-3">
          {messages.length === 0 ? (
            <div className="text-center py-8">
              <div className="w-16 h-16 mx-auto mb-3 bg-muted rounded-full flex items-center justify-center">
                <MessageSquare className="h-6 w-6 text-muted-foreground" />
              </div>
              <p className="text-sm text-muted-foreground">
                Start a session to begin the conversation
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex items-start gap-3 p-3 rounded-lg border ${
                  message.type === 'user' ? 'bg-primary/5 border-primary/20' :
                  message.type === 'agent' ? 'bg-success/5 border-success/20' :
                  'bg-muted/5 border-muted/20'
                }`}
              >
                <div className={`p-2 rounded-full ${getMessageColor(message.type)}`}>
                  {getMessageIcon(message.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium">
                      {message.type === 'user' ? 'You' :
                       message.type === 'agent' ? 'AI Assistant' : 'System'}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {formatTime(message.timestamp)}
                    </span>
                  </div>
                  <p className="text-sm">{message.content}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </Card>
  );
};
