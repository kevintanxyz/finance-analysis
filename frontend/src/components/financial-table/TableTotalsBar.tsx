import { formatCurrency, formatNumber, formatPercent } from "@/utils/formatters";
import { cn } from "@/lib/utils";

interface TableTotalsBarProps {
    totalAmount: number;
    totalWeight: number;
    itemCount: number;
    filteredCount?: number;
    currency?: string;
}

export function TableTotalsBar({
    totalAmount,
    totalWeight,
    itemCount,
    filteredCount,
    currency = "EUR",
}: TableTotalsBarProps) {
    const isFiltered = filteredCount !== undefined && filteredCount !== itemCount;

    return (
        <div className="flex items-center justify-between px-4 py-3 bg-card border-t border-border">
            <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground uppercase tracking-wide">
                        Positions
                    </span>
                    <span className="text-sm font-medium text-foreground tabular-nums">
                        {isFiltered ? (
                            <>
                                <span className="text-gold">{filteredCount}</span>
                                <span className="text-muted-foreground"> / {itemCount}</span>
                            </>
                        ) : (
                            itemCount
                        )}
                    </span>
                </div>

                <div className="h-4 w-px bg-border" />

                <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground uppercase tracking-wide">
                        Montant Total
                    </span>
                    <span className="text-sm font-semibold text-gold tabular-nums">
                        {formatCurrency(totalAmount, currency)}
                    </span>
                </div>

                <div className="h-4 w-px bg-border" />

                <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground uppercase tracking-wide">
                        Poids Total
                    </span>
                    <span
                        className={cn(
                            "text-sm font-medium tabular-nums",
                            Math.abs(totalWeight - 100) < 0.5
                                ? "text-success"
                                : "text-amber-500"
                        )}
                    >
                        {totalWeight.toFixed(2)}%
                    </span>
                </div>
            </div>

            {isFiltered && (
                <div className="text-xs text-muted-foreground">
                    Filtres actifs — affichage partiel
                </div>
            )}
        </div>
    );
}
