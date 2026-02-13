import { StrategicAllocationTable } from "./StrategicAllocationTable";

export function StrategicAllocationPage() {
    return (
        <div className="flex-1 space-y-6">
            {/* Page Title */}
            <div className="space-y-1">
                <h1 className="text-xl font-semibold text-foreground tracking-tight">
                    Strategic Asset Allocation
                </h1>
                <p className="text-sm text-muted-foreground">
                    Define your target allocation ranges and manage portfolio holdings by asset class.
                </p>
            </div>

            {/* Table Container */}
            <div className="w-full">
                <StrategicAllocationTable />
            </div>
        </div>
    );
}
