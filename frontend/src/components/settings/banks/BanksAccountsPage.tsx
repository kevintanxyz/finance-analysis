import { useState } from "react";
import { FintechButton } from "../FintechButton";
import { SettingsCard } from "../SettingsCard";
import { BankConnectionCard } from "./BankConnectionCard";
import { AddBankModal } from "./AddBankModal";
import { MOCK_BANKS } from "./types";
import type { BankConnection } from "./types";
import { Plus, RefreshCw, Building2 } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

export function BanksAccountsPage() {
  const [banks, setBanks] = useState<BankConnection[]>(MOCK_BANKS);
  const [isAddBankOpen, setIsAddBankOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefreshAll = () => {
    setIsRefreshing(true);
    toast({
      title: "Syncing all banks",
      description: "Your accounts are being synchronized...",
    });
    setTimeout(() => {
      setIsRefreshing(false);
      toast({
        title: "Sync complete",
        description: "All bank accounts have been synchronized.",
      });
    }, 2000);
  };

  const handleResync = (bankId: string) => {
    toast({
      title: "Syncing bank",
      description: "Account data is being refreshed...",
    });
  };

  const handleDisconnect = (bankId: string) => {
    setBanks((prev) => prev.filter((b) => b.id !== bankId));
    toast({
      title: "Bank disconnected",
      description: "The bank has been removed from your account.",
    });
  };

  const handleReconnect = (bankId: string) => {
    setIsAddBankOpen(true);
  };

  const handleAddBankComplete = () => {
    setIsAddBankOpen(false);
    toast({
      title: "Bank connected",
      description: "Your new bank account is now syncing.",
    });
  };

  return (
    <div className="flex-1 space-y-6 max-w-[1100px]">
      {/* Top Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h2 className="text-2xl font-semibold text-foreground">Connected banks</h2>
        <div className="flex items-center gap-3">
          <FintechButton
            variant="outline"
            onClick={handleRefreshAll}
            disabled={isRefreshing}
            className="px-4 py-2.5"
          >
            <RefreshCw className={cn("w-4 h-4 mr-2", isRefreshing && "animate-spin")} />
            Refresh all
          </FintechButton>
          <FintechButton
            variant="primary"
            onClick={() => setIsAddBankOpen(true)}
            className="px-4 py-2.5"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add bank
          </FintechButton>
        </div>
      </div>

      {/* Bank Connection Cards */}
      {banks.length > 0 ? (
        <div className="space-y-4">
          {banks.map((bank) => (
            <BankConnectionCard
              key={bank.id}
              bank={bank}
              onResync={handleResync}
              onDisconnect={handleDisconnect}
              onReconnect={handleReconnect}
            />
          ))}
        </div>
      ) : (
        <SettingsCard>
          <div className="py-12 text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto">
              <Building2 className="w-8 h-8 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-medium text-foreground">No banks connected</h3>
              <p className="text-sm text-muted-foreground max-w-md mx-auto">
                Connect your bank accounts to get a complete view of your finances.
                Your data is secured using PSD2 Open Banking standards.
              </p>
            </div>
            <FintechButton
              variant="primary"
              onClick={() => setIsAddBankOpen(true)}
              className="px-6 py-2.5"
            >
              <Plus className="w-4 h-4 mr-2" />
              Connect your first bank
            </FintechButton>
          </div>
        </SettingsCard>
      )}

      {/* Add New Bank Card */}
      {banks.length > 0 && (
        <button
          onClick={() => setIsAddBankOpen(true)}
          className="w-full p-6 rounded-2xl border-2 border-dashed border-border hover:border-primary/50 hover:bg-card/50 transition-all flex items-center justify-center gap-3 text-muted-foreground hover:text-foreground"
        >
          <Plus className="w-5 h-5" />
          <span className="font-medium">Connect a new bank account</span>
        </button>
      )}

      <AddBankModal
        isOpen={isAddBankOpen}
        onClose={() => setIsAddBankOpen(false)}
        onComplete={handleAddBankComplete}
      />
    </div>
  );
}
