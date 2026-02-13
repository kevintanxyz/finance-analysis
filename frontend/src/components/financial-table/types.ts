// Financial Data Table Types

export type SortDirection = "asc" | "desc" | null;

export interface SortConfig {
    column: string;
    direction: SortDirection;
}

export interface ColumnDefinition<T> {
    id: string;
    label: string;
    accessor: keyof T | ((row: T) => unknown);
    type: "text" | "number" | "currency" | "percent" | "date";
    sortable?: boolean;
    align?: "left" | "center" | "right";
    width?: string;
    visible?: boolean;
    sticky?: boolean;
    format?: (value: unknown, row: T) => string;
}

export interface FilterConfig {
    assetClasses: string[];
    currencies: string[];
    amountRange: { min: number | null; max: number | null };
    weightRange: { min: number | null; max: number | null };
}

export interface TableState {
    search: string;
    sort: SortConfig;
    filters: FilterConfig;
    groupBy: string | null;
    visibleColumns: string[];
}

export interface SavedView {
    id: string;
    name: string;
    state: TableState;
    isDefault?: boolean;
    createdAt: string;
}

export interface FlattenedInstrument {
    id: string;
    name: string;
    isin: string;
    quantity: number;
    price: number;
    currency: string;
    amount: number;
    weight: number;
    assetClassId: string;
    assetClassName: string;
    bank?: string;
    ytdPerformance?: number; // Year-to-date performance in percentage
}

export interface GroupedData {
    groupKey: string;
    groupLabel: string;
    items: FlattenedInstrument[];
    totals: {
        amount: number;
        weight: number;
        count: number;
    };
}

export const DEFAULT_FILTER_CONFIG: FilterConfig = {
    assetClasses: [],
    currencies: [],
    amountRange: { min: null, max: null },
    weightRange: { min: null, max: null },
};

export const DEFAULT_TABLE_STATE: TableState = {
    search: "",
    sort: { column: "", direction: null },
    filters: DEFAULT_FILTER_CONFIG,
    groupBy: null,
    visibleColumns: ["name", "isin", "quantity", "price", "amount", "weight", "ytd", "currency", "bank"],
};
