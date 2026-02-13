import { useState } from "react";
import { Filter, X, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from "@/components/ui/collapsible";
import type { TransactionType } from "./transactionTypes";

export interface TransactionFilterConfig {
    types: TransactionType[];
    accounts: string[];
    valueRange: { min: number | null; max: number | null };
}

export const DEFAULT_TRANSACTION_FILTERS: TransactionFilterConfig = {
    types: [],
    accounts: [],
    valueRange: { min: null, max: null },
};

interface TransactionFiltersProps {
    filters: TransactionFilterConfig;
    onFiltersChange: (filters: Partial<TransactionFilterConfig>) => void;
    onClear: () => void;
    availableTypes: TransactionType[];
    availableAccounts: string[];
    hasActiveFilters: boolean;
}

export function TransactionFilters({
    filters,
    onFiltersChange,
    onClear,
    availableTypes,
    availableAccounts,
    hasActiveFilters,
}: TransactionFiltersProps) {
    const [isOpen, setIsOpen] = useState(false);

    const activeFilterCount =
        filters.types.length +
        filters.accounts.length +
        (filters.valueRange.min !== null ? 1 : 0) +
        (filters.valueRange.max !== null ? 1 : 0);

    const toggleType = (type: TransactionType) => {
        const current = filters.types;
        const updated = current.includes(type)
            ? current.filter((t) => t !== type)
            : [...current, type];
        onFiltersChange({ types: updated });
    };

    const toggleAccount = (account: string) => {
        const current = filters.accounts;
        const updated = current.includes(account)
            ? current.filter((a) => a !== account)
            : [...current, account];
        onFiltersChange({ accounts: updated });
    };

    return (
        <Popover open={isOpen} onOpenChange={setIsOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="outline"
                    size="sm"
                    className={`gap-2 border-border ${hasActiveFilters ? "border-gold text-gold" : ""}`}
                >
                    <Filter className="h-4 w-4" />
                    Filtres
                    {activeFilterCount > 0 && (
                        <Badge variant="secondary" className="h-5 px-1.5 text-xs">
                            {activeFilterCount}
                        </Badge>
                    )}
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-80 bg-card border-border p-0" align="start">
                <div className="p-4 border-b border-border">
                    <div className="flex items-center justify-between">
                        <h4 className="font-medium text-sm text-foreground">Filtres</h4>
                        {hasActiveFilters && (
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={onClear}
                                className="h-7 text-xs text-muted-foreground hover:text-foreground"
                            >
                                <X className="h-3 w-3 mr-1" />
                                Effacer tout
                            </Button>
                        )}
                    </div>
                </div>

                <div className="max-h-[400px] overflow-y-auto">
                    {/* Transaction Type Filter */}
                    <Collapsible defaultOpen>
                        <CollapsibleTrigger className="flex items-center justify-between w-full p-4 hover:bg-muted/50 text-left">
                            <span className="text-sm font-medium text-foreground">Type</span>
                            <ChevronDown className="h-4 w-4 text-muted-foreground" />
                        </CollapsibleTrigger>
                        <CollapsibleContent className="px-4 pb-4 space-y-2">
                            {availableTypes.map((type) => (
                                <label
                                    key={type}
                                    className="flex items-center gap-2 cursor-pointer"
                                >
                                    <Checkbox
                                        checked={filters.types.includes(type)}
                                        onCheckedChange={() => toggleType(type)}
                                    />
                                    <span className="text-sm text-foreground">{type}</span>
                                </label>
                            ))}
                        </CollapsibleContent>
                    </Collapsible>

                    {/* Account Filter */}
                    <Collapsible defaultOpen>
                        <CollapsibleTrigger className="flex items-center justify-between w-full p-4 hover:bg-muted/50 text-left border-t border-border">
                            <span className="text-sm font-medium text-foreground">Compte</span>
                            <ChevronDown className="h-4 w-4 text-muted-foreground" />
                        </CollapsibleTrigger>
                        <CollapsibleContent className="px-4 pb-4 space-y-2">
                            {availableAccounts.map((account) => (
                                <label
                                    key={account}
                                    className="flex items-center gap-2 cursor-pointer"
                                >
                                    <Checkbox
                                        checked={filters.accounts.includes(account)}
                                        onCheckedChange={() => toggleAccount(account)}
                                    />
                                    <span className="text-sm text-foreground">{account}</span>
                                </label>
                            ))}
                        </CollapsibleContent>
                    </Collapsible>

                    {/* Value Range Filter */}
                    <Collapsible>
                        <CollapsibleTrigger className="flex items-center justify-between w-full p-4 hover:bg-muted/50 text-left border-t border-border">
                            <span className="text-sm font-medium text-foreground">Valeur</span>
                            <ChevronDown className="h-4 w-4 text-muted-foreground" />
                        </CollapsibleTrigger>
                        <CollapsibleContent className="px-4 pb-4 space-y-3">
                            <div className="grid grid-cols-2 gap-3">
                                <div className="space-y-1.5">
                                    <Label className="text-xs text-muted-foreground">Min</Label>
                                    <Input
                                        type="number"
                                        placeholder="0"
                                        value={filters.valueRange.min ?? ""}
                                        onChange={(e) =>
                                            onFiltersChange({
                                                valueRange: {
                                                    ...filters.valueRange,
                                                    min: e.target.value ? Number(e.target.value) : null,
                                                },
                                            })
                                        }
                                        className="h-8 text-sm bg-secondary border-border"
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <Label className="text-xs text-muted-foreground">Max</Label>
                                    <Input
                                        type="number"
                                        placeholder="∞"
                                        value={filters.valueRange.max ?? ""}
                                        onChange={(e) =>
                                            onFiltersChange({
                                                valueRange: {
                                                    ...filters.valueRange,
                                                    max: e.target.value ? Number(e.target.value) : null,
                                                },
                                            })
                                        }
                                        className="h-8 text-sm bg-secondary border-border"
                                    />
                                </div>
                            </div>
                        </CollapsibleContent>
                    </Collapsible>
                </div>
            </PopoverContent>
        </Popover>
    );
}
