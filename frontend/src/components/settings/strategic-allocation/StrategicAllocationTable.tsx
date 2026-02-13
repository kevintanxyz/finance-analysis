import { useState, Fragment, useMemo } from "react";
import { Info } from "lucide-react";
import {
    Table,
    TableBody,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { AssetClassRow } from "./AssetClassRow";
import { InstrumentRow } from "./InstrumentRow";
import { InstrumentHeader } from "./InstrumentHeader";
import { EditAssetClassModal } from "./EditAssetClassModal";
import { DeleteAssetClassModal } from "./DeleteAssetClassModal";
import { mockAssetClasses, UNKNOWN_ASSET_CLASS } from "./mockData";
import { useToast } from "@/hooks/use-toast";
import type { AssetClass, Instrument } from "./types";

export function StrategicAllocationTable() {
    const { toast } = useToast();
    const [assetClasses, setAssetClasses] = useState<AssetClass[]>(mockAssetClasses);
    
    // Modal states
    const [editingAssetClass, setEditingAssetClass] = useState<AssetClass | null>(null);
    const [deletingAssetClass, setDeletingAssetClass] = useState<AssetClass | null>(null);

    // Ensure "Unknown" category exists when needed
    const assetClassesWithUnknown = useMemo(() => {
        const hasUnknown = assetClasses.some((ac) => ac.id === "unknown");
        const unknownClass = assetClasses.find((ac) => ac.id === "unknown");
        
        // Only show Unknown if it has instruments
        if (hasUnknown && unknownClass?.instruments.length === 0) {
            return assetClasses.filter((ac) => ac.id !== "unknown");
        }
        
        return assetClasses;
    }, [assetClasses]);

    const handleToggle = (id: string) => {
        setAssetClasses((prev) =>
            prev.map((ac) =>
                ac.id === id ? { ...ac, isExpanded: !ac.isExpanded } : ac
            )
        );
    };

    const handleEdit = (assetClass: AssetClass) => {
        setEditingAssetClass(assetClass);
    };

    const handleEditConfirm = (id: string, minAllocation: number, maxAllocation: number) => {
        setAssetClasses((prev) =>
            prev.map((ac) =>
                ac.id === id
                    ? { ...ac, minAllocation, maxAllocation }
                    : ac
            )
        );
        toast({
            title: "Allocations mises à jour",
            description: `Les bornes d'allocation ont été modifiées avec succès.`,
        });
    };

    const handleRemove = (assetClass: AssetClass) => {
        // Prevent deleting "Unknown" category
        if (assetClass.id === "unknown") {
            toast({
                title: "Action non autorisée",
                description: "La catégorie 'Unknown' ne peut pas être supprimée.",
                variant: "destructive",
            });
            return;
        }
        setDeletingAssetClass(assetClass);
    };

    const handleDeleteConfirm = (id: string) => {
        setAssetClasses((prev) => {
            const assetClassToDelete = prev.find((ac) => ac.id === id);
            if (!assetClassToDelete) return prev;

            const instrumentsToMove = assetClassToDelete.instruments;
            
            // If no instruments to move, just remove the asset class
            if (instrumentsToMove.length === 0) {
                return prev.filter((ac) => ac.id !== id);
            }

            // Check if "Unknown" category exists
            const hasUnknown = prev.some((ac) => ac.id === "unknown");

            if (hasUnknown) {
                // Move instruments to existing "Unknown" category
                return prev
                    .filter((ac) => ac.id !== id)
                    .map((ac) =>
                        ac.id === "unknown"
                            ? { ...ac, instruments: [...ac.instruments, ...instrumentsToMove] }
                            : ac
                    );
            } else {
                // Create "Unknown" category with the instruments
                const unknownCategory: AssetClass = {
                    ...UNKNOWN_ASSET_CLASS,
                    instruments: instrumentsToMove,
                    isExpanded: true,
                };
                return [...prev.filter((ac) => ac.id !== id), unknownCategory];
            }
        });

        const deletedClass = assetClasses.find((ac) => ac.id === id);
        if (deletedClass && deletedClass.instruments.length > 0) {
            toast({
                title: "Asset Class supprimée",
                description: `${deletedClass.instruments.length} instrument(s) ont été déplacés vers "Unknown". Veuillez les reclasser.`,
            });
        } else {
            toast({
                title: "Asset Class supprimée",
                description: "L'Asset Class a été supprimée avec succès.",
            });
        }
    };

    const handleAssetClassChange = (
        sourceAssetClassId: string,
        instrumentId: string,
        targetAssetClassId: string
    ) => {
        if (sourceAssetClassId === targetAssetClassId) return;

        setAssetClasses((prev) => {
            // Find the instrument to move
            const sourceAssetClass = prev.find((ac) => ac.id === sourceAssetClassId);
            const instrumentToMove = sourceAssetClass?.instruments.find(
                (inst) => inst.id === instrumentId
            );

            if (!instrumentToMove) return prev;

            // Remove from source and add to target
            return prev.map((ac) => {
                if (ac.id === sourceAssetClassId) {
                    return {
                        ...ac,
                        instruments: ac.instruments.filter((inst) => inst.id !== instrumentId),
                    };
                }
                if (ac.id === targetAssetClassId) {
                    return {
                        ...ac,
                        instruments: [...ac.instruments, instrumentToMove],
                    };
                }
                return ac;
            });
        });
    };

    // Calculate total weight for each asset class
    const calculateAssetClassWeight = (instruments: Instrument[]) => {
        return instruments.reduce((sum, inst) => sum + inst.weight, 0);
    };

    // Check if there are instruments in "Unknown" that need reclassification
    const unknownClass = assetClassesWithUnknown.find((ac) => ac.id === "unknown");
    const hasUnclassifiedInstruments = unknownClass && unknownClass.instruments.length > 0;

    return (
        <div className="space-y-4">
            {/* Warning banner for unclassified instruments */}
            {hasUnclassifiedInstruments && (
                <div className="flex items-start gap-3 rounded-lg bg-amber-500/10 border border-amber-500/20 p-4">
                    <Info className="h-5 w-5 text-amber-500 mt-0.5 shrink-0" />
                    <div>
                        <p className="text-sm font-medium text-amber-500">
                            Instruments non classifiés
                        </p>
                        <p className="text-sm text-muted-foreground mt-1">
                            {unknownClass.instruments.length} instrument(s) se trouve(nt) dans
                            la catégorie "Unknown". Utilisez le dropdown pour les reclasser
                            dans une Asset Class appropriée.
                        </p>
                    </div>
                </div>
            )}

            <div className="rounded border border-border overflow-hidden">
                <Table>
                    {/* Level 1 Header - Asset Class (Governance) */}
                    <TableHeader>
                        <TableRow className="bg-card hover:bg-card border-b border-border">
                            <TableHead className="text-gold font-semibold text-sm">
                                Asset Class
                            </TableHead>
                            <TableHead className="text-gold font-semibold text-sm text-right">
                                Min Allocation
                            </TableHead>
                            <TableHead className="text-gold font-semibold text-sm text-right">
                                Max Allocation
                            </TableHead>
                            <TableHead className="text-gold font-semibold text-sm text-right w-24">
                                Actions
                            </TableHead>
                        </TableRow>
                    </TableHeader>

                    <TableBody>
                        {assetClassesWithUnknown.map((assetClass) => (
                            <Fragment key={assetClass.id}>
                                {/* Level 1: Asset Class Header (Governance) */}
                                <AssetClassRow
                                    assetClass={assetClass}
                                    currentWeight={calculateAssetClassWeight(assetClass.instruments)}
                                    isExpanded={assetClass.isExpanded ?? true}
                                    onToggle={() => handleToggle(assetClass.id)}
                                    onEdit={() => handleEdit(assetClass)}
                                    onRemove={() => handleRemove(assetClass)}
                                    isUnknownCategory={assetClass.id === "unknown"}
                                />

                                {/* Level 2: Instruments Sub-header when expanded */}
                                {(assetClass.isExpanded ?? true) && assetClass.instruments.length > 0 && (
                                    <>
                                        <InstrumentHeader />
                                        {assetClass.instruments.map((instrument) => (
                                            <InstrumentRow
                                                key={instrument.id}
                                                instrument={instrument}
                                                currentAssetClassId={assetClass.id}
                                                assetClasses={assetClassesWithUnknown.filter(
                                                    (ac) => ac.id !== "unknown"
                                                )}
                                                onAssetClassChange={(targetId) =>
                                                    handleAssetClassChange(
                                                        assetClass.id,
                                                        instrument.id,
                                                        targetId
                                                    )
                                                }
                                            />
                                        ))}
                                    </>
                                )}
                            </Fragment>
                        ))}
                    </TableBody>
                </Table>
            </div>

            {/* Modals */}
            <EditAssetClassModal
                assetClass={editingAssetClass}
                isOpen={!!editingAssetClass}
                onClose={() => setEditingAssetClass(null)}
                onConfirm={handleEditConfirm}
            />

            <DeleteAssetClassModal
                assetClass={deletingAssetClass}
                isOpen={!!deletingAssetClass}
                onClose={() => setDeletingAssetClass(null)}
                onConfirm={handleDeleteConfirm}
            />
        </div>
    );
}
