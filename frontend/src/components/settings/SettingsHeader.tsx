import { Settings as SettingsIcon } from "lucide-react";

export function SettingsHeader() {
  return (
    <div className="flex items-center gap-4">
      {/* Settings icon */}
      <div className="flex items-center gap-2 bg-card border border-border rounded-full px-4 py-2">
        <SettingsIcon className="h-5 w-5 text-muted-foreground" />
        <span className="text-sm font-medium text-foreground">Settings</span>
      </div>
    </div>
  );
}
