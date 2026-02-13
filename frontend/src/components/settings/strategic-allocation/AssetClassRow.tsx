import { useState } from "react";
import { Pencil, Trash2, ChevronDown, ChevronRight, AlertCircle } from "lucide-react";
import { TableCell, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";
import type { AssetClass } from "./types";

interface AssetClassRowProps {
    assetClass: AssetClass;
    currentWeight: number;
    isExpanded: boolean;
    onToggle: () => void;
    onEdit: () => void;
    onRemove: () => void;
    isUnknownCategory?: boolean;
}

export function AssetClassRow({
    assetClass,
    currentWeight,
    isExpanded,
    onToggle,
    onEdit,
    onRemove,
    isUnknownCategory = false,
}: AssetClassRowProps) {
    const [isHovered, setIsHovered] = useState(false);

    // Check if current weight is within bounds
    const isUnderAllocated = currentWeight < assetClass.minAllocation;
    const isOverAllocated = currentWeight > assetClass.maxAllocation;

    return (
        <TableRow
            className={cn(
                "cursor-pointer bg-card hover:bg-muted/50 transition-colors border-b border-border",
                isUnknownCategory && "bg-amber-500/5"
            )}
            onClick={onToggle}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            {/* Asset Class Name */}
            <TableCell className="py-3">
                <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">
                        {isExpanded ? (
                            <ChevronDown className="h-4 w-4" />
                        ) : (
                            <ChevronRight className="h-4 w-4" />
                        )}
                    </span>
                    {isUnknownCategory && (
                        <AlertCircle className="h-4 w-4 text-amber-500" />
                    )}
                    <span
                        className={cn(
                            "font-bold text-sm",
                            isUnknownCategory ? "text-amber-500" : "text-gold"
                        )}
                    >
                        {assetClass.name}
                    </span>
                    {/* Current weight indicator */}
                    <span
                        className={cn(
                            "text-xs px-1.5 py-0.5 rounded-sm ml-2",
                            isUnderAllocated && "bg-amber-500/10 text-amber-500",
                            isOverAllocated && "bg-destructive/10 text-destructive",
                            !isUnderAllocated && !isOverAllocated && "bg-muted text-muted-foreground"
                        )}
                    >
                        {currentWeight.toFixed(1)}%
                    </span>
                </div>
            </TableCell>

            {/* Min Allocation */}
            <TableCell className="text-right py-3">
                <span className="text-sm font-medium text-foreground tabular-nums">
                    {assetClass.minAllocation}%
                </span>
            </TableCell>

            {/* Max Allocation */}
            <TableCell className="text-right py-3">
                <span className="text-sm font-medium text-foreground tabular-nums">
                    {assetClass.maxAllocation}%
                </span>
            </TableCell>

            {/* Actions */}
            <TableCell className="text-right py-3">
                {!isUnknownCategory && (
                    <div
                        className={cn(
                            "flex items-center justify-end gap-1 transition-opacity",
                            isHovered ? "opacity-100" : "opacity-0"
                        )}
                    >
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                onEdit();
                            }}
                            className="p-1.5 rounded text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
                            title="Modifier les allocations Min/Max"
                        >
                            <Pencil className="h-3.5 w-3.5" />
                        </button>
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                onRemove();
                            }}
                            className="p-1.5 rounded text-muted-foreground hover:text-destructive hover:bg-secondary transition-colors"
                            title="Supprimer l'Asset Class"
                        >
                            <Trash2 className="h-3.5 w-3.5" />
                        </button>
                    </div>
                )}
            </TableCell>
        </TableRow>
    );
}
