import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface SettingsCardProps {
  title?: ReactNode;
  description?: string;
  rightElement?: ReactNode;
  children?: ReactNode;
  className?: string;
}

export function SettingsCard({
  title,
  description,
  rightElement,
  children,
  className,
}: SettingsCardProps) {
  const hasHeader = title || description || rightElement;

  return (
    <div
      className={cn(
        "bg-card border border-border rounded-[16px] p-6 shadow-lg shadow-black/20",
        className
      )}
    >
      {hasHeader && (
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            {title && <h3 className="text-foreground font-semibold text-base">{title}</h3>}
            {description && (
              <p className="text-muted-foreground text-sm">{description}</p>
            )}
          </div>
          {rightElement && <div className="flex-shrink-0">{rightElement}</div>}
        </div>
      )}
      {children && <div className={cn(hasHeader && "mt-4")}>{children}</div>}
    </div>
  );
}
