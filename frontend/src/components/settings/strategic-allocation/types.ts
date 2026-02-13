// Strategic Asset Allocation Types

export interface Instrument {
    id: string;
    name: string;
    isin: string;
    quantity: number;
    price: number;
    currency: string;
    amount: number;
    weight: number;
}

export interface AssetClass {
    id: string;
    name: string;
    minAllocation: number;
    maxAllocation: number;
    instruments: Instrument[];
    isExpanded?: boolean;
}
