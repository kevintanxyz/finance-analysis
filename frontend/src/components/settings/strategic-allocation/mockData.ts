import type { AssetClass } from "./types";
import mockAssetClassesJson from "@/mocks/asset-classes.mock.json";

// Default "Unknown" category for unclassified instruments
export const UNKNOWN_ASSET_CLASS: AssetClass = {
    id: "unknown",
    name: "Unknown",
    minAllocation: 0,
    maxAllocation: 100,
    isExpanded: true,
    instruments: [],
};

export const mockAssetClasses: AssetClass[] = mockAssetClassesJson as AssetClass[];
