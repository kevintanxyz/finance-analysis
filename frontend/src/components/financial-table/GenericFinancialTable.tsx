import { useState, Fragment, ReactNode } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { TableSearchBar } from "./TableSearchBar";
import { TableColumnConfig } from "./TableColumnConfig";
import { TableViews } from "./TableViews";
import { SortableHeader } from "./SortableHeader";
import type { SortDirection, SavedView } from "./types";

// ============= TYPES =============

export interface ColumnDefinition<T> {
    id: string;
    label: string;
    accessor: keyof T | ((row: T) => unknown);
    type: "text" | "number" | "currency" | "percent" | "date" | "custom";
    sortable?: boolean;
    align?: "left" | "right";
    required?: boolean;
    render?: (value: unknown, row: T) => ReactNode;
}

export interface GroupedTableData<T> {
    groupKey: string;
    groupLabel: string;
    items: T[];
    totals?: Record<string, number | string>;
}

interface GenericTableState {
    search: string;
    sort: { column: string; direction: SortDirection };
    visibleColumns: string[];
}

export interface GenericFinancialTableProps<T> {
    // Data
    data: T[];
    columns: ColumnDefinition<T>[];
    groupBy?: string | null;
    getGroupKey?: (item: T) => string;
    getGroupLabel?: (key: string) => string;
    calculateGroupTotals?: (items: T[]) => Record<string, number | string>;
    
    // Display columns for group totals
    groupTotalColumns?: string[];
    
    // Search config
    searchableFields?: (keyof T)[];
    
    // State & persistence
    storageKey?: string;
    
    // Empty state
    emptyMessage?: string;
    
    // Bottom bar
    renderTotalsBar?: (data: T[], filteredData: T[]) => ReactNode;
}

// ============= STORAGE =============

function loadSavedViews(key: string): SavedView[] {
    try {
        const stored = localStorage.getItem(key);
        return stored ? JSON.parse(stored) : [];
    } catch {
        return [];
    }
}

function saveSavedViewsToStorage(key: string, views: SavedView[]): void {
    try {
        localStorage.setItem(key, JSON.stringify(views));
    } catch {
        console.error("Failed to save views to localStorage");
    }
}

// ============= COMPONENT =============

export function GenericFinancialTable<T>({
    data,
    columns,
    groupBy,
    getGroupKey,
    getGroupLabel,
    calculateGroupTotals,
    groupTotalColumns = [],
    searchableFields = [],
    storageKey = "generic-table-views",
    emptyMessage = "Aucun élément ne correspond à vos critères.",
    renderTotalsBar,
}: GenericFinancialTableProps<T>) {
    // State
    const defaultVisibleColumns = columns.map((c) => c.id);
    const [state, setState] = useState<GenericTableState>({
        search: "",
        sort: { column: "", direction: null },
        visibleColumns: defaultVisibleColumns,
    });
    const [savedViews, setSavedViews] = useState<SavedView[]>(() => loadSavedViews(storageKey));
    const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set(["all"]));

    // Column visibility
    const isColumnVisible = (columnId: string) => state.visibleColumns.includes(columnId);
    const toggleColumnVisibility = (columnId: string) => {
        setState((prev) => ({
            ...prev,
            visibleColumns: prev.visibleColumns.includes(columnId)
                ? prev.visibleColumns.filter((c) => c !== columnId)
                : [...prev.visibleColumns, columnId],
        }));
    };

    // Search filter
    const filteredData = (() => {
        let result = [...data];
        
        if (state.search && searchableFields.length > 0) {
            const searchLower = state.search.toLowerCase();
            result = result.filter((item) =>
                searchableFields.some((field) => {
                    const value = item[field];
                    return typeof value === "string" && value.toLowerCase().includes(searchLower);
                })
            );
        }

        // Sorting
        if (state.sort.column && state.sort.direction) {
            const column = columns.find((c) => c.id === state.sort.column);
            if (column) {
                result.sort((a, b) => {
                    const aValue = typeof column.accessor === "function"
                        ? column.accessor(a)
                        : a[column.accessor];
                    const bValue = typeof column.accessor === "function"
                        ? column.accessor(b)
                        : b[column.accessor];

                    if (typeof aValue === "number" && typeof bValue === "number") {
                        return state.sort.direction === "asc" ? aValue - bValue : bValue - aValue;
                    }

                    if (typeof aValue === "string" && typeof bValue === "string") {
                        const comparison = aValue.localeCompare(bValue);
                        return state.sort.direction === "asc" ? comparison : -comparison;
                    }

                    return 0;
                });
            }
        }

        return result;
    })();

    // Group data
    const groupedData: GroupedTableData<T>[] = (() => {
        if (!groupBy || !getGroupKey) {
            return [{
                groupKey: "all",
                groupLabel: "Tous les éléments",
                items: filteredData,
                totals: calculateGroupTotals ? calculateGroupTotals(filteredData) : undefined,
            }];
        }

        const groups = new Map<string, T[]>();
        
        filteredData.forEach((item) => {
            const key = getGroupKey(item);
            if (!groups.has(key)) {
                groups.set(key, []);
            }
            groups.get(key)!.push(item);
        });

        return Array.from(groups.entries()).map(([key, items]) => ({
            groupKey: key,
            groupLabel: getGroupLabel ? getGroupLabel(key) : key,
            items,
            totals: calculateGroupTotals ? calculateGroupTotals(items) : undefined,
        }));
    })();

    // Actions
    const setSearch = (search: string) => setState((prev) => ({ ...prev, search }));
    
    const setSort = (column: string) => {
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
    };

    // Group toggle
    const toggleGroup = (groupKey: string) => {
        setExpandedGroups((prev) => {
            const next = new Set(prev);
            if (next.has(groupKey)) {
                next.delete(groupKey);
            } else {
                next.add(groupKey);
            }
            return next;
        });
    };

    // Views management
    const saveView = (name: string) => {
        const newView: SavedView = {
            id: crypto.randomUUID(),
            name,
            state: {
                search: state.search,
                sort: state.sort,
                filters: { assetClasses: [], currencies: [], amountRange: { min: null, max: null }, weightRange: { min: null, max: null } },
                groupBy: groupBy || null,
                visibleColumns: state.visibleColumns,
            },
            createdAt: new Date().toISOString(),
        };
        const updated = [...savedViews, newView];
        setSavedViews(updated);
        saveSavedViewsToStorage(storageKey, updated);
    };

    const loadView = (viewId: string) => {
        const view = savedViews.find((v) => v.id === viewId);
        if (view) {
            setState({
                search: view.state.search,
                sort: view.state.sort,
                visibleColumns: view.state.visibleColumns,
            });
        }
    };

    const deleteView = (viewId: string) => {
        const updated = savedViews.filter((v) => v.id !== viewId);
        setSavedViews(updated);
        saveSavedViewsToStorage(storageKey, updated);
    };

    const hasActiveFilters = state.search !== "";

    // Calculate visible column counts for colspan
    const visibleColumns = columns.filter((c) => isColumnVisible(c.id));
    const leftCols = visibleColumns.filter((c) => c.align !== "right").length;

    return (
        <div className="flex flex-col h-full">
            {/* Toolbar */}
            <div className="flex items-center gap-3 flex-wrap pb-4">
                <TableSearchBar
                    value={state.search}
                    onChange={setSearch}
                    resultCount={hasActiveFilters ? filteredData.length : undefined}
                />

                <div className="flex items-center gap-2 ml-auto">
                    <TableColumnConfig
                        columns={columns.map((c) => ({ id: c.id, label: c.label, required: c.required }))}
                        visibleColumns={state.visibleColumns}
                        onToggleColumn={toggleColumnVisibility}
                    />
                    <TableViews
                        savedViews={savedViews}
                        onSaveView={saveView}
                        onLoadView={loadView}
                        onDeleteView={deleteView}
                    />
                </div>
            </div>

            {/* Table */}
            <div className="flex-1 border border-border rounded-lg overflow-auto">
                <table className="w-full border-collapse">
                    {/* Header */}
                    <thead className="sticky top-0 z-10 bg-muted/80 backdrop-blur-sm">
                        <tr className="border-b border-border">
                            {columns.map((col) =>
                                isColumnVisible(col.id) ? (
                                    <th
                                        key={col.id}
                                        className={cn(
                                            "px-4 py-3 whitespace-nowrap",
                                            col.align === "right" ? "text-right" : "text-left"
                                        )}
                                    >
                                        <SortableHeader
                                            label={col.label}
                                            column={col.id}
                                            currentColumn={state.sort.column}
                                            currentDirection={state.sort.direction}
                                            onSort={col.sortable !== false ? setSort : undefined}
                                            align={col.align}
                                        />
                                    </th>
                                ) : null
                            )}
                        </tr>
                    </thead>

                    {/* Body */}
                    <tbody>
                        {groupedData.map((group) => (
                            <GroupSection
                                key={group.groupKey}
                                group={group}
                                columns={columns}
                                visibleColumns={state.visibleColumns}
                                isExpanded={expandedGroups.has(group.groupKey)}
                                onToggle={() => toggleGroup(group.groupKey)}
                                showGroupHeader={!!groupBy}
                                groupTotalColumns={groupTotalColumns}
                                leftCols={leftCols}
                            />
                        ))}
                    </tbody>
                </table>

                {/* Empty state */}
                {filteredData.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-16 text-center">
                        <p className="text-muted-foreground text-sm">{emptyMessage}</p>
                        {hasActiveFilters && (
                            <button
                                onClick={() => setSearch("")}
                                className="mt-2 text-sm text-gold hover:underline"
                            >
                                Effacer la recherche
                            </button>
                        )}
                    </div>
                )}
            </div>

            {/* Totals bar */}
            {renderTotalsBar && renderTotalsBar(data, filteredData)}
        </div>
    );
}

// ============= GROUP SECTION =============

interface GroupSectionProps<T> {
    group: GroupedTableData<T>;
    columns: ColumnDefinition<T>[];
    visibleColumns: string[];
    isExpanded: boolean;
    onToggle: () => void;
    showGroupHeader: boolean;
    groupTotalColumns: string[];
    leftCols: number;
}

function GroupSection<T>({
    group,
    columns,
    visibleColumns,
    isExpanded,
    onToggle,
    showGroupHeader,
    groupTotalColumns,
    leftCols,
}: GroupSectionProps<T>) {
    const isColumnVisible = (columnId: string) => visibleColumns.includes(columnId);
    const visibleCols = columns.filter((c) => isColumnVisible(c.id));

    // Calculate positions for totals - find first total column position
    const firstTotalColIndex = visibleCols.findIndex((c) => groupTotalColumns.includes(c.id));
    const colsBeforeTotals = firstTotalColIndex >= 0 ? firstTotalColIndex : leftCols;
    const colsAfterTotals = visibleCols.length - colsBeforeTotals - groupTotalColumns.filter((c) => isColumnVisible(c)).length;

    if (!showGroupHeader) {
        return (
            <>
                {group.items.map((item, idx) => (
                    <DataRow
                        key={`${group.groupKey}-${idx}`}
                        item={item}
                        columns={columns}
                        visibleColumns={visibleColumns}
                    />
                ))}
            </>
        );
    }

    return (
        <>
            {/* Group header row */}
            <tr
                onClick={onToggle}
                className="bg-muted/50 hover:bg-muted transition-colors cursor-pointer border-b border-border"
            >
                {/* Group name - spans left columns */}
                <td colSpan={colsBeforeTotals > 0 ? colsBeforeTotals : 1} className="px-4 py-2.5">
                    <div className="flex items-center gap-2">
                        {isExpanded ? (
                            <ChevronDown className="h-4 w-4 text-gold" />
                        ) : (
                            <ChevronRight className="h-4 w-4 text-gold" />
                        )}
                        <span className="font-semibold text-gold text-sm">{group.groupLabel}</span>
                        <span className="text-xs text-gold">
                            ({group.items.length} transaction{group.items.length > 1 ? "s" : ""})
                        </span>
                    </div>
                </td>
                
                {/* Total columns */}
                {groupTotalColumns.map((colId) =>
                    isColumnVisible(colId) ? (
                        <td key={colId} className="text-right px-4 py-2.5">
                            <span className="text-sm font-medium text-gold tabular-nums">
                                {group.totals?.[colId] ?? "—"}
                            </span>
                        </td>
                    ) : null
                )}
                
                {/* Empty cells for remaining columns */}
                {colsAfterTotals > 0 && <td colSpan={colsAfterTotals} />}
            </tr>

            {/* Group items */}
            {isExpanded && group.items.map((item, idx) => (
                <DataRow
                    key={`${group.groupKey}-${idx}`}
                    item={item}
                    columns={columns}
                    visibleColumns={visibleColumns}
                    indented
                />
            ))}
        </>
    );
}

// ============= DATA ROW =============

interface DataRowProps<T> {
    item: T;
    columns: ColumnDefinition<T>[];
    visibleColumns: string[];
    indented?: boolean;
}

function DataRow<T>({
    item,
    columns,
    visibleColumns,
    indented,
}: DataRowProps<T>) {
    const isColumnVisible = (columnId: string) => visibleColumns.includes(columnId);

    return (
        <tr className="hover:bg-muted/30 transition-colors border-b border-border">
            {columns.map((col, colIndex) =>
                isColumnVisible(col.id) ? (
                    <td
                        key={col.id}
                        className={cn(
                            "px-4 py-2.5",
                            col.align === "right" ? "text-right" : "text-left",
                            colIndex === 0 && indented && "pl-10"
                        )}
                    >
                        {col.render ? (
                            col.render(
                                typeof col.accessor === "function"
                                    ? col.accessor(item)
                                    : item[col.accessor],
                                item
                            )
                        ) : (
                            <span
                                className={cn(
                                    "text-sm tabular-nums",
                                    col.type === "text" && colIndex === 0
                                        ? "text-foreground"
                                        : "text-muted-foreground"
                                )}
                            >
                                {String(
                                    typeof col.accessor === "function"
                                        ? col.accessor(item)
                                        : item[col.accessor] ?? "—"
                                )}
                            </span>
                        )}
                    </td>
                ) : null
            )}
        </tr>
    );
}
