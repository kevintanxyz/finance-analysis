import { formatCurrency } from "@/utils/formatters";
import type { Transaction } from "./transactionTypes";

interface TransactionsTotalsBarProps {
    data: Transaction[];
    filteredData: Transaction[];
}

export function TransactionsTotalsBar({ data, filteredData }: TransactionsTotalsBarProps) {
    const totalValue = filteredData.reduce((sum, t) => sum + t.value, 0);
    const isFiltered = filteredData.length !== data.length;

    return (
        <div className="flex items-center justify-between px-4 py-3 mt-3 bg-muted/50 rounded-lg border border-border">
            <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">Transactions:</span>
                    <span className="text-sm font-medium text-foreground tabular-nums">
                        {isFiltered ? `${filteredData.length} / ${data.length}` : data.length}
                    </span>
                </div>
            </div>
            <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Valeur totale:</span>
                <span className="text-sm font-semibold text-foreground tabular-nums">
                    {formatCurrency(totalValue, "EUR")}
                </span>
            </div>
        </div>
    );
}
