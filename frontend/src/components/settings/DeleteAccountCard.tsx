import { useState } from "react";
import { SettingsCard } from "./SettingsCard";
import { FintechButton } from "./FintechButton";
import { FintechToggle } from "./FintechToggle";
import { AlertTriangle } from "lucide-react";

export function DeleteAccountCard() {
  const [confirmed, setConfirmed] = useState(false);

  return (
    <SettingsCard
      title={
        <span className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-destructive" />
          Delete Account
        </span>
      }
    >
      <div className="space-y-6">
        <p className="text-muted-foreground text-sm">
          Once you delete your account, there is no going back. Please be
          certain.
        </p>

        <div className="flex items-start justify-between gap-4 py-4 border-t border-border">
          <div className="space-y-1">
            <span className="text-foreground font-medium">Confirm</span>
            <p className="text-xs text-muted-foreground">
              I want to delete my account.
            </p>
          </div>
          <FintechToggle checked={confirmed} onChange={setConfirmed} />
        </div>

        <div className="flex flex-col sm:flex-row justify-end gap-3 pt-2 border-t border-border">
          <FintechButton variant="outline" className="px-5 py-2.5">
            DEACTIVATE
          </FintechButton>
          <FintechButton
            variant="destructive"
            disabled={!confirmed}
            className="px-5 py-2.5"
            title={!confirmed ? "Enable the confirmation toggle first" : "This action is irreversible"}
          >
            DELETE ACCOUNT
          </FintechButton>
        </div>
      </div>
    </SettingsCard>
  );
}
