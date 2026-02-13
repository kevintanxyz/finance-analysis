import { cn } from "@/lib/utils";
import type { ShareStatus } from "./types";

interface ShareStatusBadgeProps {
  status: ShareStatus;
}

const STATUS_CONFIG: Record<ShareStatus, { label: string; className: string }> = {
  active: {
    label: "Active",
    className: "bg-success/20 text-success",
  },
  pending: {
    label: "Pending",
    className: "bg-orange-500/20 text-orange-400",
  },
  revoked: {
    label: "Revoked",
    className: "bg-muted text-muted-foreground",
  },
};

export function ShareStatusBadge({ status }: ShareStatusBadgeProps) {
  const config = STATUS_CONFIG[status];

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        config.className
      )}
    >
      {config.label}
    </span>
  );
}
