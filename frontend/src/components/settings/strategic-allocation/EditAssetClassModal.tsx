import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { editAssetClassSchema, type EditAssetClassFormData } from "./schemas";
import type { AssetClass } from "./types";

interface EditAssetClassModalProps {
    assetClass: AssetClass | null;
    isOpen: boolean;
    onClose: () => void;
    onConfirm: (id: string, minAllocation: number, maxAllocation: number) => void;
}

export function EditAssetClassModal({
    assetClass,
    isOpen,
    onClose,
    onConfirm,
}: EditAssetClassModalProps) {
    const {
        register,
        handleSubmit,
        formState: { errors, isValid },
        reset,
        watch,
    } = useForm<EditAssetClassFormData>({
        resolver: zodResolver(editAssetClassSchema),
        mode: "onChange",
        values: assetClass
            ? {
                  minAllocation: assetClass.minAllocation,
                  maxAllocation: assetClass.maxAllocation,
              }
            : undefined,
    });

    const minValue = watch("minAllocation");
    const maxValue = watch("maxAllocation");

    const handleClose = () => {
        reset();
        onClose();
    };

    const onSubmit = (data: EditAssetClassFormData) => {
        if (assetClass) {
            onConfirm(assetClass.id, data.minAllocation, data.maxAllocation);
            handleClose();
        }
    };

    if (!assetClass) return null;

    return (
        <Dialog open={isOpen} onOpenChange={handleClose}>
            <DialogContent className="sm:max-w-[425px] bg-card border-border">
                <DialogHeader>
                    <DialogTitle className="text-foreground">
                        Modifier les allocations
                    </DialogTitle>
                    <DialogDescription className="text-muted-foreground">
                        Définissez les bornes d'allocation pour{" "}
                        <span className="font-semibold text-gold">{assetClass.name}</span>
                    </DialogDescription>
                </DialogHeader>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 py-4">
                    {/* Min Allocation */}
                    <div className="space-y-2">
                        <Label htmlFor="minAllocation" className="text-sm text-foreground">
                            Allocation Minimum (%)
                        </Label>
                        <div className="relative">
                            <Input
                                id="minAllocation"
                                type="number"
                                min={0}
                                max={100}
                                step={1}
                                {...register("minAllocation", { valueAsNumber: true })}
                                className="pr-8 bg-secondary border-border text-foreground"
                            />
                            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">
                                %
                            </span>
                        </div>
                        {errors.minAllocation && (
                            <p className="text-xs text-destructive">
                                {errors.minAllocation.message}
                            </p>
                        )}
                    </div>

                    {/* Max Allocation */}
                    <div className="space-y-2">
                        <Label htmlFor="maxAllocation" className="text-sm text-foreground">
                            Allocation Maximum (%)
                        </Label>
                        <div className="relative">
                            <Input
                                id="maxAllocation"
                                type="number"
                                min={0}
                                max={100}
                                step={1}
                                {...register("maxAllocation", { valueAsNumber: true })}
                                className="pr-8 bg-secondary border-border text-foreground"
                            />
                            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">
                                %
                            </span>
                        </div>
                        {errors.maxAllocation && (
                            <p className="text-xs text-destructive">
                                {errors.maxAllocation.message}
                            </p>
                        )}
                    </div>

                    {/* Visual preview of allocation range */}
                    <div className="space-y-2">
                        <Label className="text-xs text-muted-foreground">
                            Aperçu de la plage d'allocation
                        </Label>
                        <div className="h-2 bg-secondary rounded-full overflow-hidden relative">
                            <div
                                className="absolute h-full bg-gold/30 transition-all duration-200"
                                style={{
                                    left: `${Math.min(minValue || 0, 100)}%`,
                                    width: `${Math.max(0, Math.min((maxValue || 0) - (minValue || 0), 100 - (minValue || 0)))}%`,
                                }}
                            />
                            <div
                                className="absolute h-full w-0.5 bg-gold transition-all duration-200"
                                style={{ left: `${Math.min(minValue || 0, 100)}%` }}
                            />
                            <div
                                className="absolute h-full w-0.5 bg-gold transition-all duration-200"
                                style={{ left: `${Math.min(maxValue || 0, 100)}%` }}
                            />
                        </div>
                        <div className="flex justify-between text-xs text-muted-foreground">
                            <span>0%</span>
                            <span>50%</span>
                            <span>100%</span>
                        </div>
                    </div>

                    <DialogFooter className="gap-2">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={handleClose}
                            className="border-border"
                        >
                            Annuler
                        </Button>
                        <Button
                            type="submit"
                            disabled={!isValid}
                            className="bg-gold text-primary-foreground hover:bg-gold/90"
                        >
                            Valider
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
