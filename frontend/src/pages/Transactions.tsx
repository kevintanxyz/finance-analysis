import { useMemo, useState, useCallback } from "react";
import { formatCurrency, formatNumber } from "@/utils/formatters";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronRight } from "lucide-react";

import { TableSearchBar } from "@/components/financial-table/TableSearchBar";
import { TableColumnConfig } from "@/components/financial-table/TableColumnConfig";
import { TableViews } from "@/components/financial-table/TableViews";
import { SortableHeader } from "@/components/financial-table/SortableHeader";
import { TransactionFilters, DEFAULT_TRANSACTION_FILTERS, type TransactionFilterConfig } from "@/components/financial-table/TransactionFilters";
import { TransactionGrouping, type TransactionGroupByOption } from "@/components/financial-table/TransactionGrouping";
import { TransactionsTotalsBar } from "@/components/financial-table/TransactionsTotalsBar";
import { TransactionTypeBadge } from "@/components/financial-table/FinancialBadge";

import type { Transaction, TransactionType } from "@/components/financial-table/transactionTypes";
import { INVESTMENT_ACCOUNTS } from "@/components/financial-table/transactionTypes";
import type { SortDirection, SavedView } from "@/components/financial-table/types";
import mockTransactions from "@/mocks/transactions.mock.json";

// ============= COLUMN DEFINITIONS =============

const COLUMN_DEFINITIONS = [
    { id: "description", label: "Description", required: true },
    { id: "date", label: "Date" },
    { id: "type", label: "Type" },
    { id: "amount", label: "Amount" },
    { id: "price", label: "Price" },
    { id: "value", label: "Value" },
];

// ============= STORAGE =============

const STORAGE_KEY = "transactions-table-views";

function loadSavedViews(): SavedView[] {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        return stored ? JSON.parse(stored) : [];
    } catch {
        return [];
    }
}

function saveSavedViewsToStorage(views: SavedView[]): void {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(views));
    } catch {
        console.error("Failed to save views to localStorage");
    }
}

// ============= PAGE COMPONENT =============

export default function Transactions() {
    const transactions = mockTransactions as Transaction[];
    
    // State
    const [search, setSearch] = useState("");
    const [sort, setSort] = useState<{ column: string; direction: SortDirection }>({ column: "", direction: null });
    const [visibleColumns, setVisibleColumns] = useState<string[]>(COLUMN_DEFINITIONS.map((c) => c.id));
    const [filters, setFilters] = useState<TransactionFilterConfig>(DEFAULT_TRANSACTION_FILTERS);
    const [groupBy, setGroupBy] = useState<TransactionGroupByOption>("account");
    const [savedViews, setSavedViews] = useState<SavedView[]>(loadSavedViews);
    const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

    // Available filter options
    const availableTypes = useMemo(() => {
        const types = new Set(transactions.map((t) => t.type));
        return Array.from(types) as TransactionType[];
    }, [transactions]);

    const availableAccounts = useMemo(() => {
        const accounts = new Set(transactions.map((t) => INVESTMENT_ACCOUNTS[t.investmentAccount] || t.investmentAccount));
        return Array.from(accounts).sort();
    }, [transactions]);

    // Filter data
    const filteredData = useMemo(() => {
        let result = [...transactions];

        // Search
        if (search) {
            const searchLower = search.toLowerCase();
            result = result.filter(
                (t) =>
                    t.description.toLowerCase().includes(searchLower) ||
                    t.type.toLowerCase().includes(searchLower) ||
                    (INVESTMENT_ACCOUNTS[t.investmentAccount] || t.investmentAccount).toLowerCase().includes(searchLower)
            );
        }

        // Type filter
        if (filters.types.length > 0) {
            result = result.filter((t) => filters.types.includes(t.type));
        }

        // Account filter
        if (filters.accounts.length > 0) {
            result = result.filter((t) =>
                filters.accounts.includes(INVESTMENT_ACCOUNTS[t.investmentAccount] || t.investmentAccount)
            );
        }

        // Value range filter
        if (filters.valueRange.min !== null) {
            result = result.filter((t) => t.value >= filters.valueRange.min!);
        }
        if (filters.valueRange.max !== null) {
            result = result.filter((t) => t.value <= filters.valueRange.max!);
        }

        // Sorting
        if (sort.column && sort.direction) {
            result.sort((a, b) => {
                const aValue = a[sort.column as keyof Transaction];
                const bValue = b[sort.column as keyof Transaction];

                if (typeof aValue === "number" && typeof bValue === "number") {
                    return sort.direction === "asc" ? aValue - bValue : bValue - aValue;
                }

                if (typeof aValue === "string" && typeof bValue === "string") {
                    const comparison = aValue.localeCompare(bValue);
                    return sort.direction === "asc" ? comparison : -comparison;
                }

                return 0;
            });
        }

        return result;
    }, [transactions, search, filters, sort]);

    // Group data
    const groupedData = useMemo(() => {
        if (!groupBy) {
            return [{
                groupKey: "all",
                groupLabel: "Toutes les transactions",
                items: filteredData,
                totalValue: filteredData.reduce((sum, t) => sum + t.value, 0),
            }];
        }

        const groups = new Map<string, Transaction[]>();

        filteredData.forEach((item) => {
            let key: string;
            switch (groupBy) {
                case "account":
                    key = item.investmentAccount;
                    break;
                case "type":
                    key = item.type;
                    break;
                case "month":
                    key = format(new Date(item.date), "yyyy-MM");
                    break;
                default:
                    key = "other";
            }

            if (!groups.has(key)) {
                groups.set(key, []);
            }
            groups.get(key)!.push(item);
        });

        return Array.from(groups.entries()).map(([key, items]) => {
            let label: string;
            switch (groupBy) {
                case "account":
                    label = INVESTMENT_ACCOUNTS[key] || key;
                    break;
                case "type":
                    label = key;
                    break;
                case "month":
                    label = format(new Date(key + "-01"), "MMMM yyyy", { locale: fr });
                    break;
                default:
                    label = key;
            }

            return {
                groupKey: key,
                groupLabel: label,
                items,
                totalValue: items.reduce((sum, t) => sum + t.value, 0),
            };
        });
    }, [filteredData, groupBy]);

    // Actions
    const handleSort = useCallback((column: string) => {
        setSort((prev) => {
            let newDirection: SortDirection;
            if (prev.column !== column) {
                newDirection = "asc";
            } else if (prev.direction === "asc") {
                newDirection = "desc";
            } else if (prev.direction === "desc") {
                newDirection = null;
            } else {
                newDirection = "asc";
            }
            return { column: newDirection ? column : "", direction: newDirection };
        });
    }, []);

    const toggleColumnVisibility = useCallback((columnId: string) => {
        setVisibleColumns((prev) =>
            prev.includes(columnId) ? prev.filter((c) => c !== columnId) : [...prev, columnId]
        );
    }, []);

    const handleFiltersChange = useCallback((partial: Partial<TransactionFilterConfig>) => {
        setFilters((prev) => ({ ...prev, ...partial }));
    }, []);

    const clearFilters = useCallback(() => {
        setSearch("");
        setFilters(DEFAULT_TRANSACTION_FILTERS);
    }, []);

    const toggleGroup = useCallback((groupKey: string) => {
        setExpandedGroups((prev) => {
            const next = new Set(prev);
            if (next.has(groupKey)) {
                next.delete(groupKey);
            } else {
                next.add(groupKey);
            }
            return next;
        });
    }, []);

    // Views management
    const saveView = useCallback((name: string) => {
        const newView: SavedView = {
            id: crypto.randomUUID(),
            name,
            state: {
                search,
                sort,
                filters: { assetClasses: [], currencies: [], amountRange: { min: null, max: null }, weightRange: { min: null, max: null } },
                groupBy: groupBy || null,
                visibleColumns,
            },
            createdAt: new Date().toISOString(),
        };
        const updated = [...savedViews, newView];
        setSavedViews(updated);
        saveSavedViewsToStorage(updated);
    }, [search, sort, groupBy, visibleColumns, savedViews]);

    const loadView = useCallback((viewId: string) => {
        const view = savedViews.find((v) => v.id === viewId);
        if (view) {
            setSearch(view.state.search);
            setSort(view.state.sort);
            setVisibleColumns(view.state.visibleColumns);
            if (view.state.groupBy === "account" || view.state.groupBy === "type" || view.state.groupBy === "month") {
                setGroupBy(view.state.groupBy);
            } else {
                setGroupBy(null);
            }
        }
    }, [savedViews]);

    const deleteView = useCallback((viewId: string) => {
        const updated = savedViews.filter((v) => v.id !== viewId);
        setSavedViews(updated);
        saveSavedViewsToStorage(updated);
    }, [savedViews]);

    const hasActiveFilters =
        search !== "" ||
        filters.types.length > 0 ||
        filters.accounts.length > 0 ||
        filters.valueRange.min !== null ||
        filters.valueRange.max !== null;

    const isColumnVisible = (columnId: string) => visibleColumns.includes(columnId);

    // Calculate colspan for group headers
    const visibleLeftCols =
        (isColumnVisible("description") ? 1 : 0) +
        (isColumnVisible("date") ? 1 : 0) +
        (isColumnVisible("type") ? 1 : 0) +
        (isColumnVisible("amount") ? 1 : 0) +
        (isColumnVisible("price") ? 1 : 0);

    const visibleRightCols = 0; // No columns after value

    return (
        <div className="flex-1 p-6 space-y-6">
            {/* Page Title */}
            <div className="space-y-1">
                <h1 className="text-xl font-semibold text-foreground tracking-tight">
                    Transactions
                </h1>
                <p className="text-sm text-muted-foreground">
                    Historique des transactions par compte d'investissement avec recherche, filtres et regroupements.
                </p>
            </div>

            {/* Table Container */}
            <div className="h-[calc(100vh-200px)] flex flex-col">
                {/* Toolbar */}
                <div className="flex items-center gap-3 flex-wrap pb-4">
                    <TableSearchBar
                        value={search}
                        onChange={setSearch}
                        resultCount={hasActiveFilters ? filteredData.length : undefined}
                    />

                    <div className="flex items-center gap-2 ml-auto">
                        <TransactionFilters
                            filters={filters}
                            onFiltersChange={handleFiltersChange}
                            onClear={clearFilters}
                            availableTypes={availableTypes}
                            availableAccounts={availableAccounts}
                            hasActiveFilters={hasActiveFilters}
                        />
                        <TransactionGrouping
                            groupBy={groupBy}
                            onGroupByChange={setGroupBy}
                        />
                        <TableColumnConfig
                            columns={COLUMN_DEFINITIONS}
                            visibleColumns={visibleColumns}
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
                        <thead className="sticky top-0 z-10 bg-muted/80 backdrop-blur-sm">
                            <tr className="border-b border-border">
                                {isColumnVisible("description") && (
                                    <th className="text-left px-4 py-3 whitespace-nowrap">
                                        <SortableHeader
                                            label="Description"
                                            column="description"
                                            currentColumn={sort.column}
                                            currentDirection={sort.direction}
                                            onSort={handleSort}
                                        />
                                    </th>
                                )}
                                {isColumnVisible("date") && (
                                    <th className="text-left px-4 py-3 whitespace-nowrap">
                                        <SortableHeader
                                            label="Date"
                                            column="date"
                                            currentColumn={sort.column}
                                            currentDirection={sort.direction}
                                            onSort={handleSort}
                                        />
                                    </th>
                                )}
                                {isColumnVisible("type") && (
                                    <th className="text-left px-4 py-3 whitespace-nowrap">
                                        <SortableHeader
                                            label="Type"
                                            column="type"
                                            currentColumn={sort.column}
                                            currentDirection={sort.direction}
                                            onSort={handleSort}
                                        />
                                    </th>
                                )}
                                {isColumnVisible("amount") && (
                                    <th className="text-right px-4 py-3 whitespace-nowrap">
                                        <SortableHeader
                                            label="Amount"
                                            column="amount"
                                            currentColumn={sort.column}
                                            currentDirection={sort.direction}
                                            onSort={handleSort}
                                            align="right"
                                        />
                                    </th>
                                )}
                                {isColumnVisible("price") && (
                                    <th className="text-right px-4 py-3 whitespace-nowrap">
                                        <SortableHeader
                                            label="Price"
                                            column="price"
                                            currentColumn={sort.column}
                                            currentDirection={sort.direction}
                                            onSort={handleSort}
                                            align="right"
                                        />
                                    </th>
                                )}
                                {isColumnVisible("value") && (
                                    <th className="text-right px-4 py-3 whitespace-nowrap">
                                        <SortableHeader
                                            label="Value"
                                            column="value"
                                            currentColumn={sort.column}
                                            currentDirection={sort.direction}
                                            onSort={handleSort}
                                            align="right"
                                        />
                                    </th>
                                )}
                            </tr>
                        </thead>

                        <tbody>
                            {groupedData.map((group) => (
                                <GroupSection
                                    key={group.groupKey}
                                    group={group}
                                    isExpanded={expandedGroups.has(group.groupKey)}
                                    onToggle={() => toggleGroup(group.groupKey)}
                                    showGroupHeader={groupBy !== null}
                                    visibleColumns={visibleColumns}
                                    visibleLeftCols={visibleLeftCols}
                                    visibleRightCols={visibleRightCols}
                                />
                            ))}
                        </tbody>
                    </table>

                    {/* Empty state */}
                    {filteredData.length === 0 && (
                        <div className="flex flex-col items-center justify-center py-16 text-center">
                            <p className="text-muted-foreground text-sm">
                                Aucune transaction ne correspond à vos critères.
                            </p>
                            {hasActiveFilters && (
                                <button
                                    onClick={clearFilters}
                                    className="mt-2 text-sm text-gold hover:underline"
                                >
                                    Effacer les filtres
                                </button>
                            )}
                        </div>
                    )}
                </div>

                {/* Totals bar */}
                <TransactionsTotalsBar data={transactions} filteredData={filteredData} />
            </div>
        </div>
    );
}

// ============= GROUP SECTION =============

interface GroupData {
    groupKey: string;
    groupLabel: string;
    items: Transaction[];
    totalValue: number;
}

interface GroupSectionProps {
    group: GroupData;
    isExpanded: boolean;
    onToggle: () => void;
    showGroupHeader: boolean;
    visibleColumns: string[];
    visibleLeftCols: number;
    visibleRightCols: number;
}

function GroupSection({
    group,
    isExpanded,
    onToggle,
    showGroupHeader,
    visibleColumns,
    visibleLeftCols,
}: GroupSectionProps) {
    const isColumnVisible = (columnId: string) => visibleColumns.includes(columnId);

    if (!showGroupHeader) {
        return (
            <>
                {group.items.map((item) => (
                    <TransactionRow key={item.id} item={item} visibleColumns={visibleColumns} />
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
                <td colSpan={visibleLeftCols > 0 ? visibleLeftCols : 1} className="px-4 py-2.5">
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

                {isColumnVisible("value") && (
                    <td className="text-right px-4 py-2.5">
                        <span className="text-sm font-medium text-gold tabular-nums">
                            {formatCurrency(group.totalValue, "EUR")}
                        </span>
                    </td>
                )}
            </tr>

            {/* Group items */}
            {isExpanded &&
                group.items.map((item) => (
                    <TransactionRow key={item.id} item={item} visibleColumns={visibleColumns} indented />
                ))}
        </>
    );
}

// ============= TRANSACTION ROW =============

interface TransactionRowProps {
    item: Transaction;
    visibleColumns: string[];
    indented?: boolean;
}

function TransactionRow({ item, visibleColumns, indented }: TransactionRowProps) {
    const isColumnVisible = (columnId: string) => visibleColumns.includes(columnId);

    return (
        <tr className="hover:bg-muted/30 transition-colors border-b border-border">
            {isColumnVisible("description") && (
                <td className={cn("px-4 py-2.5", indented && "pl-10")}>
                    <span className="text-sm text-foreground">{item.description}</span>
                </td>
            )}
            {isColumnVisible("date") && (
                <td className="px-4 py-2.5">
                    <span className="text-sm text-muted-foreground">
                        {format(new Date(item.date), "dd MMM yyyy", { locale: fr })}
                    </span>
                </td>
            )}
            {isColumnVisible("type") && (
                <td className="px-4 py-2.5">
                    <TransactionTypeBadge type={item.type} />
                </td>
            )}
            {isColumnVisible("amount") && (
                <td className="text-right px-4 py-2.5">
                    <span className="text-sm text-muted-foreground tabular-nums">
                        {formatNumber(item.amount)}
                    </span>
                </td>
            )}
            {isColumnVisible("price") && (
                <td className="text-right px-4 py-2.5">
                    <span className="text-sm text-muted-foreground tabular-nums">
                        {item.price > 0 ? formatCurrency(item.price, item.currency) : "—"}
                    </span>
                </td>
            )}
            {isColumnVisible("value") && (
                <td className="text-right px-4 py-2.5">
                    <span
                        className={cn(
                            "text-sm font-medium tabular-nums",
                            item.value >= 0 ? "text-foreground" : "text-rose-400"
                        )}
                    >
                        {formatCurrency(item.value, item.currency)}
                    </span>
                </td>
            )}
        </tr>
    );
}
