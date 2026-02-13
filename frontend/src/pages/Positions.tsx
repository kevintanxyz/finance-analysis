import { useMemo } from "react";
import { FinancialDataTable } from "@/components/financial-table";
import type { FlattenedInstrument } from "@/components/financial-table";
import mockAssetClasses from "@/mocks/asset-classes.mock.json";
import positionsMock from "@/mocks/positions.mock.json";

export default function Positions() {
    // Flatten instruments for the positions table
    const flattenedInstruments: FlattenedInstrument[] = useMemo(() => {
        return mockAssetClasses.flatMap((assetClass, acIndex) =>
            assetClass.instruments.map((instrument, idx) => ({
                ...instrument,
                assetClassId: assetClass.id,
                assetClassName: assetClass.name,
                bank: positionsMock.banks[(acIndex + idx) % positionsMock.banks.length],
                ytdPerformance: positionsMock.ytdPerformances[(acIndex * 3 + idx) % positionsMock.ytdPerformances.length],
            }))
        );
    }, []);

    return (
        <div className="flex-1 p-6 space-y-6">
            {/* Page Title */}
            <div className="space-y-1">
                <h1 className="text-xl font-semibold text-foreground tracking-tight">
                    Positions
                </h1>
                <p className="text-sm text-muted-foreground">
                    Vue consolidée de toutes les positions du portefeuille avec recherche, filtres et regroupements.
                </p>
            </div>

            {/* Table Container */}
            <div className="h-[calc(100vh-200px)]">
                <FinancialDataTable data={flattenedInstruments} />
            </div>
        </div>
    );
}
