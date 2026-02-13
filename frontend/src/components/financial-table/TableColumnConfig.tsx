import { useState } from "react";
import { Columns, Eye, EyeOff, GripVertical } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";

interface ColumnConfig {
    id: string;
    label: string;
    required?: boolean;
}

interface TableColumnConfigProps {
    columns: ColumnConfig[];
    visibleColumns: string[];
    onToggleColumn: (columnId: string) => void;
}

const DEFAULT_COLUMNS: ColumnConfig[] = [
    { id: "name", label: "Nom", required: true },
    { id: "isin", label: "ISIN" },
    { id: "quantity", label: "Quantité" },
    { id: "price", label: "Prix" },
    { id: "amount", label: "Montant" },
    { id: "weight", label: "Poids" },
    { id: "assetClass", label: "Asset Class" },
    { id: "currency", label: "Devise" },
];

export function TableColumnConfig({
    columns = DEFAULT_COLUMNS,
    visibleColumns,
    onToggleColumn,
}: TableColumnConfigProps) {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <Popover open={isOpen} onOpenChange={setIsOpen}>
            <PopoverTrigger asChild>
                <Button variant="outline" size="sm" className="gap-2 border-border">
                    <Columns className="h-4 w-4" />
                    Colonnes
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-56 bg-card border-border p-0" align="end">
                <div className="p-3 border-b border-border">
                    <h4 className="font-medium text-sm text-foreground">Afficher les colonnes</h4>
                </div>
                <div className="p-2 space-y-1 max-h-[300px] overflow-y-auto">
                    {columns.map((column) => {
                        const isVisible = visibleColumns.includes(column.id);
                        const isDisabled = column.required;

                        return (
                            <div
                                key={column.id}
                                className="flex items-center justify-between p-2 rounded hover:bg-muted/50"
                            >
                                <div className="flex items-center gap-2">
                                    {isVisible ? (
                                        <Eye className="h-3.5 w-3.5 text-muted-foreground" />
                                    ) : (
                                        <EyeOff className="h-3.5 w-3.5 text-muted-foreground" />
                                    )}
                                    <span className="text-sm text-foreground">{column.label}</span>
                                </div>
                                <Switch
                                    checked={isVisible}
                                    onCheckedChange={() => onToggleColumn(column.id)}
                                    disabled={isDisabled}
                                    className="scale-75"
                                />
                            </div>
                        );
                    })}
                </div>
            </PopoverContent>
        </Popover>
    );
}
