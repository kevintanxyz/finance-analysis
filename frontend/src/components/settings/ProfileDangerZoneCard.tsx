import { useState } from "react";
import { SettingsCard } from "./SettingsCard";
import { FintechButton } from "./FintechButton";
import { AlertTriangle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";

export function ProfileDangerZoneCard() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [password, setPassword] = useState("");
  const [confirmed, setConfirmed] = useState(false);

  const canDelete = password.length > 0 && confirmed;

  const handleClose = () => {
    setIsModalOpen(false);
    setPassword("");
    setConfirmed(false);
  };

  const handleDelete = () => {
    // Frontend only - no actual deletion
    handleClose();
  };

  const inputClasses = "w-full bg-input border border-border rounded-lg px-4 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all";

  return (
    <>
      <SettingsCard
        title={
          <span className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-destructive" />
            Delete account
          </span>
        }
      >
        <div className="space-y-4">
          <p className="text-muted-foreground text-sm">
            Once you delete your account, there is no going back. Please be certain.
          </p>
          <div className="flex justify-end">
            <FintechButton
              variant="destructive"
              onClick={() => setIsModalOpen(true)}
              className="px-5 py-2.5"
            >
              Delete my account
            </FintechButton>
          </div>
        </div>
      </SettingsCard>

      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="bg-card border-border rounded-2xl max-w-md">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold text-foreground flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-destructive" />
              Delete your account?
            </DialogTitle>
            <DialogDescription className="text-muted-foreground">
              This action cannot be undone. Please confirm your decision.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* Step 1: Password */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-foreground">
                Confirm your password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className={inputClasses}
              />
            </div>

            {/* Step 2: Checkbox */}
            <div className="flex items-start gap-3">
              <Checkbox
                id="confirm-delete"
                checked={confirmed}
                onCheckedChange={(checked) => setConfirmed(checked === true)}
                className="mt-0.5 border-border data-[state=checked]:bg-destructive data-[state=checked]:border-destructive"
              />
              <label
                htmlFor="confirm-delete"
                className="text-sm text-foreground cursor-pointer"
              >
                I understand that this action is irreversible
              </label>
            </div>

            {/* Step 3: Warning box */}
            <div className="p-4 rounded-lg border border-destructive/30 bg-destructive/5 space-y-2">
              <p className="text-sm text-destructive font-medium">Warning:</p>
              <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                <li>All bank connections will be revoked</li>
                <li>Your personal data will be deleted</li>
                <li>Invoices may be retained for legal purposes</li>
              </ul>
            </div>
          </div>

          <DialogFooter className="flex flex-col-reverse sm:flex-row gap-3">
            <FintechButton
              variant="outline"
              onClick={handleClose}
              className="px-5 py-2.5 flex-1 sm:flex-none"
            >
              Cancel
            </FintechButton>
            <FintechButton
              variant="destructive"
              onClick={handleDelete}
              disabled={!canDelete}
              className="px-5 py-2.5 flex-1 sm:flex-none"
            >
              Confirm deletion
            </FintechButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
