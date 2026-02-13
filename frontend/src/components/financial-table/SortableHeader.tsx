import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";
import { cn } from "@/lib/utils";
import type { SortDirection } from "./types";

interface SortableHeaderProps {
    label: string;
    column: string;
    currentColumn: string;
    currentDirection: SortDirection;
    onSort: (column: string) => void;
    align?: "left" | "center" | "right";
    className?: string;
}

export function SortableHeader({
    label,
    column,
    currentColumn,
    currentDirection,
    onSort,
    align = "left",
    className,
}: SortableHeaderProps) {
    const isActive = currentColumn === column;
    const direction = isActive ? currentDirection : null;

    const getIcon = () => {
        if (!isActive || direction === null) {
            return <ArrowUpDown className="h-3.5 w-3.5 text-muted-foreground" />;
        }
        if (direction === "asc") {
            return <ArrowUp className="h-3.5 w-3.5 text-gold" />;
        }
        return <ArrowDown className="h-3.5 w-3.5 text-gold" />;
    };

    return (
        <button
            onClick={() => onSort(column)}
            className={cn(
                "flex items-center gap-1.5 hover:text-foreground transition-colors group",
                align === "right" && "flex-row-reverse",
                align === "center" && "justify-center",
                isActive && direction ? "text-gold" : "text-muted-foreground",
                className
            )}
        >
            <span className="text-xs font-medium whitespace-nowrap">{label}</span>
            <span className="opacity-60 group-hover:opacity-100 transition-opacity">
                {getIcon()}
            </span>
        </button>
    );
}
