import { AlertTriangle } from "lucide-react";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import type { AssetClass } from "./types";

interface DeleteAssetClassModalProps {
    assetClass: AssetClass | null;
    isOpen: boolean;
    onClose: () => void;
    onConfirm: (id: string) => void;
}

export function DeleteAssetClassModal({
    assetClass,
    isOpen,
    onClose,
    onConfirm,
}: DeleteAssetClassModalProps) {
    if (!assetClass) return null;

    const instrumentCount = assetClass.instruments.length;

    const handleConfirm = () => {
        onConfirm(assetClass.id);
        onClose();
    };

    return (
        <AlertDialog open={isOpen} onOpenChange={onClose}>
            <AlertDialogContent className="bg-card border-border max-w-md">
                <AlertDialogHeader>
                    <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-destructive/10">
                            <AlertTriangle className="h-5 w-5 text-destructive" />
                        </div>
                        <AlertDialogTitle className="text-foreground">
                            Supprimer l'Asset Class
                        </AlertDialogTitle>
                    </div>
                    <AlertDialogDescription asChild>
                        <div className="space-y-4 pt-2">
                            <p className="text-muted-foreground">
                                Vous êtes sur le point de supprimer l'Asset Class{" "}
                                <span className="font-semibold text-gold">
                                    "{assetClass.name}"
                                </span>
                                .
                            </p>

                            {instrumentCount > 0 && (
                                <div className="rounded-lg bg-amber-500/10 border border-amber-500/20 p-4 space-y-2">
                                    <p className="text-sm font-medium text-amber-500">
                                        ⚠️ {instrumentCount} instrument{instrumentCount > 1 ? "s" : ""} associé{instrumentCount > 1 ? "s" : ""}
                                    </p>
                                    <p className="text-sm text-muted-foreground">
                                        Les actifs contenus dans cette Asset Class ne seront pas
                                        supprimés. Ils seront automatiquement reclassés dans la
                                        catégorie <span className="font-semibold text-foreground">"Unknown"</span>.
                                    </p>
                                    <p className="text-sm text-muted-foreground">
                                        Vous devrez ensuite les reclasser manuellement dans une
                                        Asset Class valide.
                                    </p>
                                </div>
                            )}

                            {instrumentCount === 0 && (
                                <p className="text-sm text-muted-foreground">
                                    Cette Asset Class ne contient aucun instrument.
                                </p>
                            )}
                        </div>
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter className="gap-2">
                    <AlertDialogCancel className="border-border">
                        Annuler
                    </AlertDialogCancel>
                    <AlertDialogAction
                        onClick={handleConfirm}
                        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                    >
                        Confirmer la suppression
                    </AlertDialogAction>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    );
}
