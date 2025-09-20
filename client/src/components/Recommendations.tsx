import { Badge } from "@/components/ui/badge";
import { ConversationStatus } from "./AudioDashboard";
import { MessageSquare, Clock, Target } from "lucide-react";

interface RecommendationsProps {
  recommendations: string[];
  status: ConversationStatus;
  scenario: string;
}

export const Recommendations = ({ recommendations, status, scenario }: RecommendationsProps) => {
  const getStatusMessage = () => {
    switch (status) {
      case "listening":
        return {
          icon: <MessageSquare className="h-4 w-4" />,
          text: "Listening to conversation...",
          color: "bg-primary text-primary-foreground"
        };
      case "speaking":
        return {
          icon: <MessageSquare className="h-4 w-4" />,
          text: "Someone is speaking",
          color: "bg-error text-error-foreground"
        };
      case "paused":
        return {
          icon: <Target className="h-4 w-4" />,
          text: "Ready to help!",
          color: "bg-success text-success-foreground"
        };
      default:
        return {
          icon: <Clock className="h-4 w-4" />,
          text: "Waiting for audio...",
          color: "bg-muted text-muted-foreground"
        };
    }
  };

  const statusInfo = getStatusMessage();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Agent Recommendations</h3>
        <Badge className={statusInfo.color}>
          {statusInfo.icon}
          <span className="ml-2">{statusInfo.text}</span>
        </Badge>
      </div>

      <div className="p-3 bg-muted rounded-lg">
        <h4 className="font-medium text-sm mb-1">Current Scenario</h4>
        <p className="text-sm text-muted-foreground">{scenario}</p>
      </div>

      <div className="space-y-3">
        {recommendations.length > 0 ? (
          <>
            <h4 className="font-medium text-sm">Suggestions:</h4>
            {recommendations.map((rec, index) => (
              <div
                key={index}
                className="p-3 bg-card border rounded-lg animate-fade-in"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <p className="text-sm">{rec}</p>
              </div>
            ))}
          </>
        ) : (
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-3 bg-muted rounded-full flex items-center justify-center">
              <MessageSquare className="h-6 w-6 text-muted-foreground" />
            </div>
            <p className="text-sm text-muted-foreground">
              {status === "paused"
                ? "No recommendations at the moment"
                : "Start the session to receive AI recommendations"}
            </p>
          </div>
        )}
      </div>

      {status === "paused" && recommendations.length === 0 && (
        <div className="p-3 bg-success/10 border border-success/20 rounded-lg">
          <p className="text-sm text-success-foreground">
            Great! The conversation is flowing well. No immediate suggestions needed.
          </p>
        </div>
      )}
    </div>
  );
};
