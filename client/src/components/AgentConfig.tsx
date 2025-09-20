import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { AgentSettings } from "./AudioDashboard";
import { Save, X } from "lucide-react";

interface AgentConfigProps {
  settings: AgentSettings;
  onSettingsChange: (settings: AgentSettings) => void;
  onClose: () => void;
}

export const AgentConfig = ({ settings, onSettingsChange, onClose }: AgentConfigProps) => {
  const [localSettings, setLocalSettings] = useState(settings);

  const handleSave = () => {
    onSettingsChange(localSettings);
    onClose();
  };

  const handleReset = () => {
    setLocalSettings({
      scenario: "Negotiate career progression with my manager",
      pauseDuration: 2.0
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Agent Configuration</h3>
        <Button variant="ghost" size="sm" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div>
            <Label htmlFor="scenario">Conversation Scenario</Label>
            <Textarea
              id="scenario"
              value={localSettings.scenario}
              onChange={(e) => setLocalSettings({ ...localSettings, scenario: e.target.value })}
              placeholder="Describe the conversation context..."
              className="mt-1"
              rows={3}
            />
            <p className="text-sm text-muted-foreground mt-1">
              Describe what kind of conversation the agent should help with.
            </p>
          </div>

          <div>
            <Label htmlFor="pauseDuration">Pause Duration (seconds)</Label>
            <Input
              id="pauseDuration"
              type="number"
              min="0.5"
              max="10"
              step="0.1"
              value={localSettings.pauseDuration}
              onChange={(e) => setLocalSettings({ ...localSettings, pauseDuration: parseFloat(e.target.value) })}
              className="mt-1"
            />
            <p className="text-sm text-muted-foreground mt-1">
              How long a pause should be before agent provides recommendations.
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="p-4 bg-muted rounded-lg border">
            <h4 className="font-medium mb-2">Quick Scenarios</h4>
            <div className="space-y-2">
              {[
                "Negotiate career progression with my manager",
                "Customer service conversation",
                "Team meeting discussion",
                "Sales call with potential client"
              ].map((scenario) => (
                <Button
                  key={scenario}
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-left"
                  onClick={() => setLocalSettings({ ...localSettings, scenario })}
                >
                  {scenario}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-between">
        <Button variant="outline" onClick={handleReset}>
          Reset to Defaults
        </Button>
        <div className="flex gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave} className="gap-2">
            <Save className="h-4 w-4" />
            Save Settings
          </Button>
        </div>
      </div>
    </div>
  );
};
