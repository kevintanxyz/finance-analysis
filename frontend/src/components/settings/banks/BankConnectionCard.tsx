import { useState } from "react";
import { SettingsCard } from "../SettingsCard";
import { FintechButton } from "../FintechButton";
import { BankStatusBadge } from "./StatusBadge";
import { ManageAccountsModal } from "./ManageAccountsModal";
import { DisconnectModal } from "./DisconnectModal";
import type { BankConnection } from "./types";
import { RefreshCw, Settings2, Unlink, MoreVertical, AlertTriangle } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

interface BankConnectionCardProps {
  bank: BankConnection;
  onResync: (bankId: string) => void;
  onDisconnect: (bankId: string) => void;
  onReconnect: (bankId: string) => void;
}

const FLAG_MAP: Record<string, string> = {
  CH: "🇨🇭",
  FR: "🇫🇷",
  DE: "🇩🇪",
  NL: "🇳🇱",
  AT: "🇦🇹",
  BE: "🇧🇪",
  ES: "🇪🇸",
  IT: "🇮🇹",
  PT: "🇵🇹",
  SE: "🇸🇪",
};

export function BankConnectionCard({ bank, onResync, onDisconnect, onReconnect }: BankConnectionCardProps) {
  const [isManageOpen, setIsManageOpen] = useState(false);
  const [isDisconnectOpen, setIsDisconnectOpen] = useState(false);
  const [isSyncing, setIsSyncing] = useState(bank.status === "syncing");

  const handleResync = () => {
    setIsSyncing(true);
    onResync(bank.id);
    setTimeout(() => setIsSyncing(false), 2000);
  };

  const isError = bank.status === "error" || bank.status === "expired";

  return (
    <>
      <SettingsCard className={cn(isError && "border-destructive/30")}>
        <div className="space-y-4">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-secondary flex items-center justify-center overflow-hidden">
                <img
                  src={bank.logo}
                  alt={bank.name}
                  className="w-8 h-8 object-contain"
                  onError={(e) => {
                    e.currentTarget.style.display = "none";
                  }}
                />
              </div>
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-foreground font-semibold">{bank.name}</span>
                  <span className="text-lg" title={bank.country}>
                    {FLAG_MAP[bank.countryCode] || "🌍"}
                  </span>
                  <BankStatusBadge status={isSyncing ? "syncing" : bank.status} />
                </div>
                <span className="text-xs text-muted-foreground">
                  Last synchronized: {bank.lastSync}
                </span>
              </div>
            </div>

            {/* Desktop Actions */}
            <div className="hidden sm:flex items-center gap-2">
              <FintechButton
                variant="outline"
                onClick={handleResync}
                disabled={isSyncing}
                className="px-3 py-2 text-xs"
              >
                <RefreshCw className={cn("w-3.5 h-3.5 mr-1.5", isSyncing && "animate-spin")} />
                Resync
              </FintechButton>
              <FintechButton
                variant="outline"
                onClick={() => setIsManageOpen(true)}
                className="px-3 py-2 text-xs"
              >
                <Settings2 className="w-3.5 h-3.5 mr-1.5" />
                Manage accounts
              </FintechButton>
              <FintechButton
                variant="outline"
                onClick={() => setIsDisconnectOpen(true)}
                className="px-3 py-2 text-xs text-destructive border-destructive/50 hover:bg-destructive/10"
              >
                <Unlink className="w-3.5 h-3.5" />
              </FintechButton>
            </div>

            {/* Mobile Actions Dropdown */}
            <div className="sm:hidden">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="p-2 rounded-lg hover:bg-secondary transition-colors">
                    <MoreVertical className="w-5 h-5 text-muted-foreground" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="bg-popover border-border">
                  <DropdownMenuItem onClick={handleResync}>
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Resync
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setIsManageOpen(true)}>
                    <Settings2 className="w-4 h-4 mr-2" />
                    Manage accounts
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => setIsDisconnectOpen(true)}
                    className="text-destructive focus:text-destructive"
                  >
                    <Unlink className="w-4 h-4 mr-2" />
                    Disconnect
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          {/* Error State */}
          {isError && (
            <div className="flex items-center gap-3 p-3 rounded-lg bg-destructive/10 border border-destructive/20">
              <AlertTriangle className="w-5 h-5 text-destructive flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm text-foreground">
                  {bank.status === "expired"
                    ? "Connection expired. Please reconnect to continue syncing."
                    : "Connection error. Please try reconnecting."}
                </p>
              </div>
              <FintechButton
                variant="destructive"
                onClick={() => onReconnect(bank.id)}
                className="px-4 py-2 text-xs"
              >
                Reconnect
              </FintechButton>
            </div>
          )}
        </div>
      </SettingsCard>

      <ManageAccountsModal
        bank={bank}
        isOpen={isManageOpen}
        onClose={() => setIsManageOpen(false)}
      />

      <DisconnectModal
        bankName={bank.name}
        isOpen={isDisconnectOpen}
        onClose={() => setIsDisconnectOpen(false)}
        onConfirm={() => {
          onDisconnect(bank.id);
          setIsDisconnectOpen(false);
        }}
      />
    </>
  );
}
