import { useMemo, useState, useCallback } from "react";
import type {
    FlattenedInstrument,
    GroupedData,
    SortConfig,
    SortDirection,
    FilterConfig,
    TableState,
    SavedView,
    DEFAULT_TABLE_STATE,
} from "./types";
import { DEFAULT_FILTER_CONFIG } from "./types";

interface UseFinancialTableProps {
    data: FlattenedInstrument[];
    initialState?: Partial<TableState>;
}

interface UseFinancialTableReturn {
    // State
    state: TableState;
    
    // Data
    filteredData: FlattenedInstrument[];
    groupedData: GroupedData[];
    totals: { amount: number; weight: number; count: number };
    
    // Available filter options
    availableAssetClasses: string[];
    availableCurrencies: string[];
    
    // Actions
    setSearch: (search: string) => void;
    setSort: (column: string) => void;
    setFilters: (filters: Partial<FilterConfig>) => void;
    clearFilters: () => void;
    setGroupBy: (groupBy: string | null) => void;
    setVisibleColumns: (columns: string[]) => void;
    toggleColumnVisibility: (columnId: string) => void;
    
    // Views
    savedViews: SavedView[];
    saveView: (name: string) => void;
    loadView: (viewId: string) => void;
    deleteView: (viewId: string) => void;
    
    // State checks
    hasActiveFilters: boolean;
}

const STORAGE_KEY = "financial-table-views";

function loadSavedViews(): SavedView[] {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        return stored ? JSON.parse(stored) : [];
    } catch {
        return [];
    }
}

function saveSavedViews(views: SavedView[]): void {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(views));
    } catch {
        console.error("Failed to save views to localStorage");
    }
}

export function useFinancialTable({
    data,
    initialState,
}: UseFinancialTableProps): UseFinancialTableReturn {
    const defaultState: TableState = {
        search: "",
        sort: { column: "", direction: null },
        filters: DEFAULT_FILTER_CONFIG,
        groupBy: null,
        visibleColumns: ["name", "isin", "quantity", "price", "amount", "weight", "ytd", "currency", "bank"],
        ...initialState,
    };

    const [state, setState] = useState<TableState>(defaultState);
    const [savedViews, setSavedViews] = useState<SavedView[]>(loadSavedViews);

    // Extract available filter options from data
    const availableAssetClasses = useMemo(() => {
        const classes = new Set(data.map((d) => d.assetClassName));
        return Array.from(classes).sort();
    }, [data]);

    const availableCurrencies = useMemo(() => {
        const currencies = new Set(data.map((d) => d.currency));
        return Array.from(currencies).sort();
    }, [data]);

    // Filter data
    const filteredData = useMemo(() => {
        let result = [...data];

        // Search filter
        if (state.search) {
            const searchLower = state.search.toLowerCase();
            result = result.filter(
                (item) =>
                    item.name.toLowerCase().includes(searchLower) ||
                    item.isin.toLowerCase().includes(searchLower) ||
                    item.assetClassName.toLowerCase().includes(searchLower) ||
                    item.currency.toLowerCase().includes(searchLower)
            );
        }

        // Asset class filter
        if (state.filters.assetClasses.length > 0) {
            result = result.filter((item) =>
                state.filters.assetClasses.includes(item.assetClassName)
            );
        }

        // Currency filter
        if (state.filters.currencies.length > 0) {
            result = result.filter((item) =>
                state.filters.currencies.includes(item.currency)
            );
        }

        // Amount range filter
        if (state.filters.amountRange.min !== null) {
            result = result.filter((item) => item.amount >= state.filters.amountRange.min!);
        }
        if (state.filters.amountRange.max !== null) {
            result = result.filter((item) => item.amount <= state.filters.amountRange.max!);
        }

        // Weight range filter
        if (state.filters.weightRange.min !== null) {
            result = result.filter((item) => item.weight >= state.filters.weightRange.min!);
        }
        if (state.filters.weightRange.max !== null) {
            result = result.filter((item) => item.weight <= state.filters.weightRange.max!);
        }

        // Sorting
        if (state.sort.column && state.sort.direction) {
            const { column, direction } = state.sort;
            result.sort((a, b) => {
                const aValue = a[column as keyof FlattenedInstrument];
                const bValue = b[column as keyof FlattenedInstrument];

                if (typeof aValue === "number" && typeof bValue === "number") {
                    return direction === "asc" ? aValue - bValue : bValue - aValue;
                }

                if (typeof aValue === "string" && typeof bValue === "string") {
                    const comparison = aValue.localeCompare(bValue);
                    return direction === "asc" ? comparison : -comparison;
                }

                return 0;
            });
        }

        return result;
    }, [data, state.search, state.filters, state.sort]);

    // Calculate totals
    const totals = useMemo(() => ({
        amount: filteredData.reduce((sum, item) => sum + item.amount, 0),
        weight: filteredData.reduce((sum, item) => sum + item.weight, 0),
        count: filteredData.length,
    }), [filteredData]);

    // Group data
    const groupedData = useMemo((): GroupedData[] => {
        if (!state.groupBy) {
            return [{
                groupKey: "all",
                groupLabel: "Tous les instruments",
                items: filteredData,
                totals,
            }];
        }

        const groups = new Map<string, FlattenedInstrument[]>();
        
        filteredData.forEach((item) => {
            let groupKey: string;
            switch (state.groupBy) {
                case "assetClass":
                    groupKey = item.assetClassName;
                    break;
                case "currency":
                    groupKey = item.currency;
                    break;
                case "bank":
                    groupKey = item.bank || "Non assigné";
                    break;
                default:
                    groupKey = "other";
            }

            if (!groups.has(groupKey)) {
                groups.set(groupKey, []);
            }
            groups.get(groupKey)!.push(item);
        });

        return Array.from(groups.entries()).map(([key, items]) => ({
            groupKey: key,
            groupLabel: key,
            items,
            totals: {
                amount: items.reduce((sum, item) => sum + item.amount, 0),
                weight: items.reduce((sum, item) => sum + item.weight, 0),
                count: items.length,
            },
        }));
    }, [filteredData, state.groupBy, totals]);

    // Actions
    const setSearch = useCallback((search: string) => {
        setState((prev) => ({ ...prev, search }));
    }, []);

    const setSort = useCallback((column: string) => {
        setState((prev) => {
            let newDirection: SortDirection;
            if (prev.sort.column !== column) {
                newDirection = "asc";
            } else if (prev.sort.direction === "asc") {
                newDirection = "desc";
            } else if (prev.sort.direction === "desc") {
                newDirection = null;
            } else {
                newDirection = "asc";
            }

            return {
                ...prev,
                sort: { column: newDirection ? column : "", direction: newDirection },
            };
        });
    }, []);

    const setFilters = useCallback((filters: Partial<FilterConfig>) => {
        setState((prev) => ({
            ...prev,
            filters: { ...prev.filters, ...filters },
        }));
    }, []);

    const clearFilters = useCallback(() => {
        setState((prev) => ({
            ...prev,
            search: "",
            filters: DEFAULT_FILTER_CONFIG,
        }));
    }, []);

    const setGroupBy = useCallback((groupBy: string | null) => {
        setState((prev) => ({ ...prev, groupBy }));
    }, []);

    const setVisibleColumns = useCallback((columns: string[]) => {
        setState((prev) => ({ ...prev, visibleColumns: columns }));
    }, []);

    const toggleColumnVisibility = useCallback((columnId: string) => {
        setState((prev) => {
            const isVisible = prev.visibleColumns.includes(columnId);
            return {
                ...prev,
                visibleColumns: isVisible
                    ? prev.visibleColumns.filter((c) => c !== columnId)
                    : [...prev.visibleColumns, columnId],
            };
        });
    }, []);

    // Views management
    const saveView = useCallback((name: string) => {
        const newView: SavedView = {
            id: crypto.randomUUID(),
            name,
            state,
            createdAt: new Date().toISOString(),
        };
        const updated = [...savedViews, newView];
        setSavedViews(updated);
        saveSavedViews(updated);
    }, [state, savedViews]);

    const loadView = useCallback((viewId: string) => {
        const view = savedViews.find((v) => v.id === viewId);
        if (view) {
            setState(view.state);
        }
    }, [savedViews]);

    const deleteView = useCallback((viewId: string) => {
        const updated = savedViews.filter((v) => v.id !== viewId);
        setSavedViews(updated);
        saveSavedViews(updated);
    }, [savedViews]);

    // Check if any filters are active
    const hasActiveFilters = useMemo(() => {
        return (
            state.search !== "" ||
            state.filters.assetClasses.length > 0 ||
            state.filters.currencies.length > 0 ||
            state.filters.amountRange.min !== null ||
            state.filters.amountRange.max !== null ||
            state.filters.weightRange.min !== null ||
            state.filters.weightRange.max !== null
        );
    }, [state.search, state.filters]);

    return {
        state,
        filteredData,
        groupedData,
        totals,
        availableAssetClasses,
        availableCurrencies,
        setSearch,
        setSort,
        setFilters,
        clearFilters,
        setGroupBy,
        setVisibleColumns,
        toggleColumnVisibility,
        savedViews,
        saveView,
        loadView,
        deleteView,
        hasActiveFilters,
    };
}
