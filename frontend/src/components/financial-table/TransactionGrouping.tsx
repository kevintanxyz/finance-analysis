import { Layers, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
    DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

export type TransactionGroupByOption = "account" | "type" | "month" | null;

interface TransactionGroupingProps {
    groupBy: TransactionGroupByOption;
    onGroupByChange: (groupBy: TransactionGroupByOption) => void;
}

const GROUPING_OPTIONS: { value: TransactionGroupByOption; label: string }[] = [
    { value: null, label: "Aucun regroupement" },
    { value: "account", label: "Par Compte" },
    { value: "type", label: "Par Type" },
    { value: "month", label: "Par Mois" },
];

export function TransactionGrouping({ groupBy, onGroupByChange }: TransactionGroupingProps) {
    const currentLabel = GROUPING_OPTIONS.find((opt) => opt.value === groupBy)?.label ?? "Regrouper";

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button
                    variant="outline"
                    size="sm"
                    className={`gap-2 border-border ${groupBy ? "border-gold text-gold" : ""}`}
                >
                    <Layers className="h-4 w-4" />
                    {currentLabel}
                    <ChevronDown className="h-3.5 w-3.5 ml-1" />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="bg-card border-border" align="start">
                {GROUPING_OPTIONS.map((option, index) => (
                    <div key={option.value ?? "none"}>
                        {index === 1 && <DropdownMenuSeparator />}
                        <DropdownMenuItem
                            onClick={() => onGroupByChange(option.value)}
                            className={groupBy === option.value ? "text-gold" : ""}
                        >
                            {option.label}
                        </DropdownMenuItem>
                    </div>
                ))}
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
