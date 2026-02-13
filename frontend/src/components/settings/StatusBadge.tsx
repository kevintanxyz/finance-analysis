import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  status: "success" | "disabled";
  children: React.ReactNode;
}

export function StatusBadge({ status, children }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium",
        {
          "bg-success/20 text-success": status === "success",
          "bg-muted text-muted-foreground": status === "disabled",
        }
      )}
    >
      {children}
    </span>
  );
}
