import { cn } from "@/lib/utils";
import type { ConnectionStatus } from "./types";

interface BankStatusBadgeProps {
  status: ConnectionStatus;
}

const STATUS_CONFIG: Record<ConnectionStatus, { label: string; className: string }> = {
  connected: {
    label: "Connected",
    className: "bg-success/20 text-success",
  },
  syncing: {
    label: "Syncing",
    className: "bg-blue-500/20 text-blue-400",
  },
  expired: {
    label: "Expired",
    className: "bg-orange-500/20 text-orange-400",
  },
  error: {
    label: "Error",
    className: "bg-destructive/20 text-destructive",
  },
};

export function BankStatusBadge({ status }: BankStatusBadgeProps) {
  const config = STATUS_CONFIG[status];

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        config.className
      )}
    >
      {status === "syncing" && (
        <span className="mr-1.5 h-2 w-2 animate-pulse rounded-full bg-blue-400" />
      )}
      {config.label}
    </span>
  );
}
