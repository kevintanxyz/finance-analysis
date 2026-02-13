import { FintechButton } from "../FintechButton";
import { AlertTriangle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

interface DisconnectModalProps {
  bankName: string;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export function DisconnectModal({ bankName, isOpen, onClose, onConfirm }: DisconnectModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-card border-border rounded-2xl max-w-md">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold text-foreground flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-destructive" />
            Disconnect bank?
          </DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Are you sure you want to disconnect <strong className="text-foreground">{bankName}</strong>?
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <div className="p-4 rounded-lg border border-destructive/30 bg-destructive/5 space-y-2">
            <p className="text-sm text-destructive font-medium">This will:</p>
            <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
              <li>Stop syncing all accounts from this bank</li>
              <li>Remove the bank connection from your profile</li>
              <li>Historical data will be retained</li>
            </ul>
          </div>
        </div>

        <DialogFooter className="flex flex-col-reverse sm:flex-row gap-3">
          <FintechButton
            variant="outline"
            onClick={onClose}
            className="px-5 py-2.5 flex-1 sm:flex-none"
          >
            Cancel
          </FintechButton>
          <FintechButton
            variant="destructive"
            onClick={onConfirm}
            className="px-5 py-2.5 flex-1 sm:flex-none"
          >
            Disconnect
          </FintechButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
