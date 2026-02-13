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
import type { FilterConfig } from "./types";
import { formatCurrency } from "@/utils/formatters";

interface TableFiltersProps {
    filters: FilterConfig;
    onFiltersChange: (filters: Partial<FilterConfig>) => void;
    onClear: () => void;
    availableAssetClasses: string[];
    availableCurrencies: string[];
    hasActiveFilters: boolean;
}

export function TableFilters({
    filters,
    onFiltersChange,
    onClear,
    availableAssetClasses,
    availableCurrencies,
    hasActiveFilters,
}: TableFiltersProps) {
    const [isOpen, setIsOpen] = useState(false);

    const activeFilterCount =
        filters.assetClasses.length +
        filters.currencies.length +
        (filters.amountRange.min !== null ? 1 : 0) +
        (filters.amountRange.max !== null ? 1 : 0) +
        (filters.weightRange.min !== null ? 1 : 0) +
        (filters.weightRange.max !== null ? 1 : 0);

    const toggleAssetClass = (assetClass: string) => {
        const current = filters.assetClasses;
        const updated = current.includes(assetClass)
            ? current.filter((c) => c !== assetClass)
            : [...current, assetClass];
        onFiltersChange({ assetClasses: updated });
    };

    const toggleCurrency = (currency: string) => {
        const current = filters.currencies;
        const updated = current.includes(currency)
            ? current.filter((c) => c !== currency)
            : [...current, currency];
        onFiltersChange({ currencies: updated });
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
                    {/* Asset Class Filter */}
                    <Collapsible defaultOpen>
                        <CollapsibleTrigger className="flex items-center justify-between w-full p-4 hover:bg-muted/50 text-left">
                            <span className="text-sm font-medium text-foreground">Asset Class</span>
                            <ChevronDown className="h-4 w-4 text-muted-foreground" />
                        </CollapsibleTrigger>
                        <CollapsibleContent className="px-4 pb-4 space-y-2">
                            {availableAssetClasses.map((assetClass) => (
                                <label
                                    key={assetClass}
                                    className="flex items-center gap-2 cursor-pointer"
                                >
                                    <Checkbox
                                        checked={filters.assetClasses.includes(assetClass)}
                                        onCheckedChange={() => toggleAssetClass(assetClass)}
                                    />
                                    <span className="text-sm text-foreground">{assetClass}</span>
                                </label>
                            ))}
                        </CollapsibleContent>
                    </Collapsible>

                    {/* Currency Filter */}
                    <Collapsible defaultOpen>
                        <CollapsibleTrigger className="flex items-center justify-between w-full p-4 hover:bg-muted/50 text-left border-t border-border">
                            <span className="text-sm font-medium text-foreground">Devise</span>
                            <ChevronDown className="h-4 w-4 text-muted-foreground" />
                        </CollapsibleTrigger>
                        <CollapsibleContent className="px-4 pb-4 space-y-2">
                            {availableCurrencies.map((currency) => (
                                <label
                                    key={currency}
                                    className="flex items-center gap-2 cursor-pointer"
                                >
                                    <Checkbox
                                        checked={filters.currencies.includes(currency)}
                                        onCheckedChange={() => toggleCurrency(currency)}
                                    />
                                    <span className="text-sm text-foreground">{currency}</span>
                                </label>
                            ))}
                        </CollapsibleContent>
                    </Collapsible>

                    {/* Amount Range Filter */}
                    <Collapsible>
                        <CollapsibleTrigger className="flex items-center justify-between w-full p-4 hover:bg-muted/50 text-left border-t border-border">
                            <span className="text-sm font-medium text-foreground">Montant</span>
                            <ChevronDown className="h-4 w-4 text-muted-foreground" />
                        </CollapsibleTrigger>
                        <CollapsibleContent className="px-4 pb-4 space-y-3">
                            <div className="grid grid-cols-2 gap-3">
                                <div className="space-y-1.5">
                                    <Label className="text-xs text-muted-foreground">Min</Label>
                                    <Input
                                        type="number"
                                        placeholder="0"
                                        value={filters.amountRange.min ?? ""}
                                        onChange={(e) =>
                                            onFiltersChange({
                                                amountRange: {
                                                    ...filters.amountRange,
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
                                        value={filters.amountRange.max ?? ""}
                                        onChange={(e) =>
                                            onFiltersChange({
                                                amountRange: {
                                                    ...filters.amountRange,
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

                    {/* Weight Range Filter */}
                    <Collapsible>
                        <CollapsibleTrigger className="flex items-center justify-between w-full p-4 hover:bg-muted/50 text-left border-t border-border">
                            <span className="text-sm font-medium text-foreground">Poids (%)</span>
                            <ChevronDown className="h-4 w-4 text-muted-foreground" />
                        </CollapsibleTrigger>
                        <CollapsibleContent className="px-4 pb-4 space-y-3">
                            <div className="grid grid-cols-2 gap-3">
                                <div className="space-y-1.5">
                                    <Label className="text-xs text-muted-foreground">Min %</Label>
                                    <Input
                                        type="number"
                                        placeholder="0"
                                        min={0}
                                        max={100}
                                        value={filters.weightRange.min ?? ""}
                                        onChange={(e) =>
                                            onFiltersChange({
                                                weightRange: {
                                                    ...filters.weightRange,
                                                    min: e.target.value ? Number(e.target.value) : null,
                                                },
                                            })
                                        }
                                        className="h-8 text-sm bg-secondary border-border"
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <Label className="text-xs text-muted-foreground">Max %</Label>
                                    <Input
                                        type="number"
                                        placeholder="100"
                                        min={0}
                                        max={100}
                                        value={filters.weightRange.max ?? ""}
                                        onChange={(e) =>
                                            onFiltersChange({
                                                weightRange: {
                                                    ...filters.weightRange,
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
