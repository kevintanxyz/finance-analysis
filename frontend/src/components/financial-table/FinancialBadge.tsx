import { cn } from "@/lib/utils";

export type BadgeVariant = "positive" | "negative" | "buy" | "sell" | "dividend" | "transfer" | "fee" | "interest" | "neutral";

interface FinancialBadgeProps {
    children: React.ReactNode;
    variant: BadgeVariant;
    className?: string;
}

const VARIANT_STYLES: Record<BadgeVariant, string> = {
    positive: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
    negative: "bg-rose-500/15 text-rose-400 border-rose-500/20",
    buy: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
    sell: "bg-rose-500/15 text-rose-400 border-rose-500/20",
    dividend: "bg-zinc-800/80 text-zinc-300 border-zinc-700/50",
    transfer: "bg-teal-600/20 text-teal-400 border-teal-500/25",
    fee: "bg-slate-500/15 text-slate-400 border-slate-500/20",
    interest: "bg-violet-500/15 text-violet-400 border-violet-500/20",
    neutral: "bg-muted text-muted-foreground border-border",
};

/**
 * Unified financial badge component with consistent width across all pages.
 * Used for YTD Performance (Positions) and Transaction Types (Transactions).
 */
export function FinancialBadge({ children, variant, className }: FinancialBadgeProps) {
    return (
        <span
            className={cn(
                // Fixed width for visual consistency across all badges
                "inline-flex items-center justify-center w-[72px] px-2 py-0.5 rounded text-xs font-medium border tabular-nums",
                VARIANT_STYLES[variant],
                className
            )}
        >
            {children}
        </span>
    );
}

// ============= SPECIALIZED BADGE COMPONENTS =============

interface YtdBadgeProps {
    value: number | undefined | null;
}

export function YtdBadge({ value }: YtdBadgeProps) {
    if (value === undefined || value === null) {
        return <span className="inline-flex items-center justify-center w-[72px] text-sm text-muted-foreground">—</span>;
    }

    const isPositive = value >= 0;
    const formatted = `${isPositive ? "+" : ""}${value.toFixed(1)}%`;

    return (
        <FinancialBadge variant={isPositive ? "positive" : "negative"}>
            {formatted}
        </FinancialBadge>
    );
}

type TransactionType = "Buy" | "Sell" | "Dividend" | "Transfer" | "Fee" | "Interest";

interface TransactionTypeBadgeProps {
    type: TransactionType;
}

const TYPE_TO_VARIANT: Record<TransactionType, BadgeVariant> = {
    Buy: "buy",
    Sell: "sell",
    Dividend: "dividend",
    Transfer: "transfer",
    Fee: "fee",
    Interest: "interest",
};

export function TransactionTypeBadge({ type }: TransactionTypeBadgeProps) {
    return (
        <FinancialBadge variant={TYPE_TO_VARIANT[type]}>
            {type}
        </FinancialBadge>
    );
}
