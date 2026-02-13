import { Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface TableSearchBarProps {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    resultCount?: number;
}

export function TableSearchBar({
    value,
    onChange,
    placeholder = "Rechercher par nom, ISIN, classe...",
    resultCount,
}: TableSearchBarProps) {
    return (
        <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder={placeholder}
                className="pl-10 pr-10 bg-secondary border-border h-9"
            />
            {value && (
                <Button
                    variant="ghost"
                    size="sm"
                    className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
                    onClick={() => onChange("")}
                >
                    <X className="h-3.5 w-3.5" />
                </Button>
            )}
            {value && resultCount !== undefined && (
                <span className="absolute right-10 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
                    {resultCount} résultat{resultCount !== 1 ? "s" : ""}
                </span>
            )}
        </div>
    );
}
