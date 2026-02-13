import { useState } from "react";
import { FintechButton } from "../FintechButton";
import { FintechToggle } from "../FintechToggle";
import type { BankConnection, BankAccount } from "./types";
import { RefreshCw, Pencil, Trash2, Eye } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

interface ManageAccountsModalProps {
  bank: BankConnection;
  isOpen: boolean;
  onClose: () => void;
  onNavigateToSharing?: () => void;
}

// Mock sharing data
const SHARED_ACCOUNTS: Record<string, number> = {
  a1: 2,
  a2: 1,
  b1: 0,
  c1: 1,
  c2: 0,
  d1: 0,
};

const ACCOUNT_TYPE_LABELS: Record<BankAccount["type"], string> = {
  current: "Current",
  savings: "Savings",
  securities: "Securities",
  loan: "Loan",
};

function maskIban(iban: string): string {
  const cleaned = iban.replace(/\s/g, "");
  if (cleaned.length <= 8) return iban;
  const first4 = cleaned.slice(0, 4);
  const last4 = cleaned.slice(-4);
  return `${first4} **** **** ${last4}`;
}

export function ManageAccountsModal({ bank, isOpen, onClose, onNavigateToSharing }: ManageAccountsModalProps) {
  const [accounts, setAccounts] = useState(bank.accounts);

  const toggleIncluded = (accountId: string) => {
    setAccounts((prev) =>
      prev.map((acc) =>
        acc.id === accountId ? { ...acc, included: !acc.included } : acc
      )
    );
  };

  const formatBalance = (balance?: number, currency?: string) => {
    if (balance === undefined) return "—";
    return new Intl.NumberFormat("en-CH", {
      style: "currency",
      currency: currency || "CHF",
    }).format(balance);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-card border-border rounded-2xl max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="text-xl font-semibold text-foreground">
            Manage accounts – {bank.name}
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto py-4 space-y-4">
          {accounts.map((account, index) => (
            <div
              key={account.id}
              className={cn(
                "p-4 rounded-lg bg-secondary/50",
                index !== accounts.length - 1 && "border-b border-border"
              )}
            >
              {/* Desktop Layout */}
              <div className="hidden sm:flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-foreground truncate">
                      {account.name}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
                      {ACCOUNT_TYPE_LABELS[account.type]}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-primary/20 text-primary">
                      {account.currency}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground font-mono">
                    {maskIban(account.iban)}
                  </p>
                </div>

                  <div className="flex items-center gap-6">
                    {/* Sharing indicator */}
                    {SHARED_ACCOUNTS[account.id] > 0 && (
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              onClick={onNavigateToSharing}
                              className="flex items-center gap-1.5 text-xs text-primary hover:underline"
                            >
                              <Eye className="w-3.5 h-3.5" />
                              Shared
                            </button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>This account is shared with {SHARED_ACCOUNTS[account.id]} people</p>
                            <button
                              onClick={onNavigateToSharing}
                              className="text-primary hover:underline mt-1 block"
                            >
                              Manage sharing
                            </button>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    )}

                    <div className="text-right">
                      <p className="text-sm font-medium text-foreground">
                        {formatBalance(account.balance, account.currency)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {account.lastSync}
                      </p>
                    </div>

                  <div className="flex items-center gap-3">
                    <div className="flex flex-col items-center gap-1">
                      <FintechToggle
                        checked={account.included}
                        onChange={() => toggleIncluded(account.id)}
                      />
                      <span className="text-[10px] text-muted-foreground">
                        {account.included ? "Included" : "Excluded"}
                      </span>
                    </div>

                    <div className="flex items-center gap-1">
                      <button
                        className="p-2 rounded-lg hover:bg-muted transition-colors"
                        title="Rename"
                      >
                        <Pencil className="w-4 h-4 text-muted-foreground" />
                      </button>
                      <button
                        className="p-2 rounded-lg hover:bg-muted transition-colors"
                        title="Resync"
                      >
                        <RefreshCw className="w-4 h-4 text-muted-foreground" />
                      </button>
                      <button
                        className="p-2 rounded-lg hover:bg-destructive/10 transition-colors"
                        title="Remove"
                      >
                        <Trash2 className="w-4 h-4 text-destructive" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Mobile Layout */}
              <div className="sm:hidden space-y-3">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-foreground">
                        {account.name}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
                        {ACCOUNT_TYPE_LABELS[account.type]}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground font-mono">
                      {maskIban(account.iban)}
                    </p>
                  </div>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-primary/20 text-primary">
                    {account.currency}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {formatBalance(account.balance, account.currency)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {account.lastSync}
                    </p>
                  </div>
                  <FintechToggle
                    checked={account.included}
                    onChange={() => toggleIncluded(account.id)}
                  />
                </div>

                <div className="flex items-center gap-2 pt-2 border-t border-border">
                  <button className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg bg-muted text-muted-foreground text-xs hover:bg-muted/80 transition-colors">
                    <Pencil className="w-3.5 h-3.5" />
                    Rename
                  </button>
                  <button className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg bg-muted text-muted-foreground text-xs hover:bg-muted/80 transition-colors">
                    <RefreshCw className="w-3.5 h-3.5" />
                    Resync
                  </button>
                  <button className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg bg-destructive/10 text-destructive text-xs hover:bg-destructive/20 transition-colors">
                    <Trash2 className="w-3.5 h-3.5" />
                    Remove
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="flex-shrink-0 pt-4 border-t border-border space-y-4">
          <div className="p-3 rounded-lg bg-muted/50">
            <p className="text-xs text-muted-foreground">
              Your bank connections are secured using European PSD2 Open Banking standards.
              You can revoke access at any time.
            </p>
          </div>
          <div className="flex justify-end">
            <FintechButton variant="outline" onClick={onClose} className="px-6 py-2.5">
              Close
            </FintechButton>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
