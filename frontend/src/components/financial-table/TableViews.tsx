import { useState } from "react";
import { Bookmark, Plus, Trash2, Check, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
    DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import type { SavedView } from "./types";
import { formatDate } from "@/utils/formatters";

interface TableViewsProps {
    savedViews: SavedView[];
    onSaveView: (name: string) => void;
    onLoadView: (viewId: string) => void;
    onDeleteView: (viewId: string) => void;
}

export function TableViews({
    savedViews,
    onSaveView,
    onLoadView,
    onDeleteView,
}: TableViewsProps) {
    const [showSaveDialog, setShowSaveDialog] = useState(false);
    const [viewName, setViewName] = useState("");

    const handleSave = () => {
        if (viewName.trim()) {
            onSaveView(viewName.trim());
            setViewName("");
            setShowSaveDialog(false);
        }
    };

    return (
        <>
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm" className="gap-2 border-border">
                        <Bookmark className="h-4 w-4" />
                        Vues
                        {savedViews.length > 0 && (
                            <span className="text-xs text-muted-foreground">
                                ({savedViews.length})
                            </span>
                        )}
                        <ChevronDown className="h-3.5 w-3.5 ml-1" />
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-64 bg-card border-border" align="end">
                    {savedViews.length > 0 ? (
                        <>
                            {savedViews.map((view) => (
                                <DropdownMenuItem
                                    key={view.id}
                                    className="flex items-center justify-between group"
                                    onClick={() => onLoadView(view.id)}
                                >
                                    <div className="flex flex-col">
                                        <span className="text-sm">{view.name}</span>
                                        <span className="text-xs text-muted-foreground">
                                            {formatDate(view.createdAt)}
                                        </span>
                                    </div>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onDeleteView(view.id);
                                        }}
                                    >
                                        <Trash2 className="h-3.5 w-3.5 text-destructive" />
                                    </Button>
                                </DropdownMenuItem>
                            ))}
                            <DropdownMenuSeparator />
                        </>
                    ) : (
                        <div className="px-2 py-3 text-center text-sm text-muted-foreground">
                            Aucune vue sauvegardée
                        </div>
                    )}
                    <DropdownMenuItem onClick={() => setShowSaveDialog(true)}>
                        <Plus className="h-4 w-4 mr-2" />
                        Sauvegarder la vue actuelle
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>

            <Dialog open={showSaveDialog} onOpenChange={setShowSaveDialog}>
                <DialogContent className="sm:max-w-[400px] bg-card border-border">
                    <DialogHeader>
                        <DialogTitle className="text-foreground">Sauvegarder la vue</DialogTitle>
                        <DialogDescription className="text-muted-foreground">
                            Donnez un nom à cette configuration de tableau pour la retrouver facilement.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="py-4">
                        <Input
                            value={viewName}
                            onChange={(e) => setViewName(e.target.value)}
                            placeholder="Nom de la vue..."
                            className="bg-secondary border-border"
                            autoFocus
                            onKeyDown={(e) => {
                                if (e.key === "Enter") handleSave();
                            }}
                        />
                    </div>
                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setShowSaveDialog(false)}
                            className="border-border"
                        >
                            Annuler
                        </Button>
                        <Button
                            onClick={handleSave}
                            disabled={!viewName.trim()}
                            className="bg-gold text-primary-foreground hover:bg-gold/90"
                        >
                            <Check className="h-4 w-4 mr-2" />
                            Sauvegarder
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </>
    );
}
