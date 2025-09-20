import cn from "clsx";
import { ConversationStatus } from "./AudioDashboard";

interface StatusIndicatorProps {
  status: ConversationStatus;
  audioLevel: number;
  isRecording: boolean;
}

export const StatusIndicator = ({ status, audioLevel, isRecording }: StatusIndicatorProps) => {
  const getIndicatorClasses = () => {
    const baseClasses = "w-32 h-32 rounded-full flex items-center justify-center text-2xl font-bold transition-all duration-300 border-2";

    switch (status) {
      case "paused":
        return cn(baseClasses, "bg-success text-success-foreground animate-status-pulse");
      case "speaking":
      case "listening":
        return cn(baseClasses, "bg-error text-error-foreground");
      default:
        return cn(baseClasses, "bg-muted text-muted-foreground");
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case "paused":
        return "✓";
      case "speaking":
      case "listening":
        return "●";
      default:
        return "○";
    }
  };

  const getAudioLevelIndicator = () => {
    // Audio level removed as backend might not support it
    return null;
  };

  return (
    <div className="flex flex-col items-center">
      <div className={getIndicatorClasses()}>
        {getStatusIcon()}
      </div>
      {getAudioLevelIndicator()}
    </div>
  );
};
