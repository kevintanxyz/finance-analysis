import { useState } from "react";
import { TableCell, TableRow } from "@/components/ui/table";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import type { Instrument, AssetClass } from "./types";

interface InstrumentRowProps {
    instrument: Instrument;
    currentAssetClassId: string;
    assetClasses: AssetClass[];
    onAssetClassChange: (targetAssetClassId: string) => void;
}

export function InstrumentRow({
    instrument,
    currentAssetClassId,
    assetClasses,
    onAssetClassChange,
}: InstrumentRowProps) {
    const [showChangeHighlight, setShowChangeHighlight] = useState(false);

    const formatCurrency = (amount: number, currency: string) => {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency,
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(amount);
    };

    const formatNumber = (num: number) => {
        return new Intl.NumberFormat("en-US").format(num);
    };

    const handleAssetClassChange = (newAssetClassId: string) => {
        if (newAssetClassId !== currentAssetClassId) {
            setShowChangeHighlight(true);
            setTimeout(() => {
                onAssetClassChange(newAssetClassId);
                setShowChangeHighlight(false);
            }, 300);
        }
    };

    return (
        <TableRow
            className={cn(
                "hover:bg-muted/50 transition-all duration-300 border-b border-border/30",
                showChangeHighlight && "bg-gold/10"
            )}
        >
            <TableCell colSpan={4} className="py-2.5 px-0">
                <div className="grid grid-cols-6 gap-4 pl-10 pr-4 items-center">
                    {/* Instrument Name + ISIN */}
                    <div className="flex flex-col gap-0.5">
                        <span className="text-sm text-foreground">
                            {instrument.name}
                        </span>
                        <span className="text-xs text-muted-foreground font-mono">
                            {instrument.isin}
                        </span>
                    </div>

                    {/* Quantity (informative) */}
                    <div className="text-right">
                        <span className="text-sm text-muted-foreground tabular-nums">
                            {formatNumber(instrument.quantity)}
                        </span>
                    </div>

                    {/* Price (informative) */}
                    <div className="text-right">
                        <span className="text-sm text-muted-foreground tabular-nums">
                            {formatCurrency(instrument.price, instrument.currency)}
                        </span>
                    </div>

                    {/* Amount (informative) */}
                    <div className="text-right">
                        <span className="text-sm text-foreground font-medium tabular-nums">
                            {formatCurrency(instrument.amount, instrument.currency)}
                        </span>
                    </div>

                    {/* Weight (calculated, read-only) */}
                    <div className="text-right">
                        <span className="text-sm text-muted-foreground tabular-nums">
                            {instrument.weight.toFixed(1)}%
                        </span>
                    </div>

                    {/* Asset Class Dropdown (requalification) */}
                    <div>
                        <Select
                            value={currentAssetClassId}
                            onValueChange={handleAssetClassChange}
                        >
                            <SelectTrigger className="w-[130px] h-8 text-xs bg-card border-border">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-card border-border z-50">
                                {assetClasses.map((ac) => (
                                    <SelectItem
                                        key={ac.id}
                                        value={ac.id}
                                        className="text-xs"
                                    >
                                        {ac.name}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                </div>
            </TableCell>
        </TableRow>
    );
}
