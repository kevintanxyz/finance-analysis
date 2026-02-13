import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes, forwardRef } from "react";

interface FintechButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "outline" | "destructive";
}

export const FintechButton = forwardRef<HTMLButtonElement, FintechButtonProps>(
  ({ className, variant = "primary", children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center rounded-[4px] px-5 py-2.5 text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-background disabled:pointer-events-none disabled:opacity-50",
          {
            "bg-primary text-white hover:bg-primary/90":
              variant === "primary",
            "bg-white/10 border border-white/20 text-white hover:bg-white/20":
              variant === "outline",
            "bg-destructive text-white hover:bg-destructive/90":
              variant === "destructive",
          },
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);

FintechButton.displayName = "FintechButton";
