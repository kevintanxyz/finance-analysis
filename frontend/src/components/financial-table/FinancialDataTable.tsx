import { useState, Fragment } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatCurrency, formatNumber } from "@/utils/formatters";
import { useFinancialTable } from "./useFinancialTable";
import { TableSearchBar } from "./TableSearchBar";
import { TableFilters } from "./TableFilters";
import { TableGrouping } from "./TableGrouping";
import { TableColumnConfig } from "./TableColumnConfig";
import { TableViews } from "./TableViews";
import { TableTotalsBar } from "./TableTotalsBar";
import { SortableHeader } from "./SortableHeader";
import { YtdBadge } from "./FinancialBadge";
import type { FlattenedInstrument, GroupedData } from "./types";

interface FinancialDataTableProps {
    data: FlattenedInstrument[];
    title?: string;
    description?: string;
}

const COLUMN_DEFINITIONS = [
    { id: "name", label: "Instrument", required: true },
    { id: "isin", label: "ISIN" },
    { id: "quantity", label: "Quantité" },
    { id: "price", label: "Prix" },
    { id: "amount", label: "Montant" },
    { id: "weight", label: "Poids" },
    { id: "ytd", label: "YTD" },
    { id: "currency", label: "Devise" },
    { id: "bank", label: "Banque" },
];

// YtdBadge is now imported from FinancialBadge.tsx

export function FinancialDataTable({
    data,
    title = "Positions",
    description,
}: FinancialDataTableProps) {
    const {
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
        toggleColumnVisibility,
        savedViews,
        saveView,
        loadView,
        deleteView,
        hasActiveFilters,
    } = useFinancialTable({ data });

    const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set(["all"]));

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

    const isColumnVisible = (columnId: string) => state.visibleColumns.includes(columnId);

    // Count visible columns for group header colspan
    const visibleLeftCols = (isColumnVisible("name") ? 1 : 0) + (isColumnVisible("isin") ? 1 : 0);
    const visibleRightCols = 
        (isColumnVisible("quantity") ? 1 : 0) +
        (isColumnVisible("price") ? 1 : 0) +
        (isColumnVisible("amount") ? 1 : 0) +
        (isColumnVisible("weight") ? 1 : 0) +
        (isColumnVisible("currency") ? 1 : 0) +
        (isColumnVisible("bank") ? 1 : 0);

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
                    <TableFilters
                        filters={state.filters}
                        onFiltersChange={setFilters}
                        onClear={clearFilters}
                        availableAssetClasses={availableAssetClasses}
                        availableCurrencies={availableCurrencies}
                        hasActiveFilters={hasActiveFilters}
                    />
                    <TableGrouping
                        groupBy={state.groupBy}
                        onGroupByChange={setGroupBy}
                    />
                    <TableColumnConfig
                        columns={COLUMN_DEFINITIONS}
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
                            {isColumnVisible("name") && (
                                <th className="text-left px-4 py-3 whitespace-nowrap">
                                    <SortableHeader
                                        label="Instrument"
                                        column="name"
                                        currentColumn={state.sort.column}
                                        currentDirection={state.sort.direction}
                                        onSort={setSort}
                                    />
                                </th>
                            )}
                            {isColumnVisible("isin") && (
                                <th className="text-left px-4 py-3 whitespace-nowrap">
                                    <SortableHeader
                                        label="ISIN"
                                        column="isin"
                                        currentColumn={state.sort.column}
                                        currentDirection={state.sort.direction}
                                        onSort={setSort}
                                    />
                                </th>
                            )}
                            {isColumnVisible("quantity") && (
                                <th className="text-right px-4 py-3 whitespace-nowrap">
                                    <SortableHeader
                                        label="Quantité"
                                        column="quantity"
                                        currentColumn={state.sort.column}
                                        currentDirection={state.sort.direction}
                                        onSort={setSort}
                                        align="right"
                                    />
                                </th>
                            )}
                            {isColumnVisible("price") && (
                                <th className="text-right px-4 py-3 whitespace-nowrap">
                                    <SortableHeader
                                        label="Prix"
                                        column="price"
                                        currentColumn={state.sort.column}
                                        currentDirection={state.sort.direction}
                                        onSort={setSort}
                                        align="right"
                                    />
                                </th>
                            )}
                            {isColumnVisible("amount") && (
                                <th className="text-right px-4 py-3 whitespace-nowrap">
                                    <SortableHeader
                                        label="Montant"
                                        column="amount"
                                        currentColumn={state.sort.column}
                                        currentDirection={state.sort.direction}
                                        onSort={setSort}
                                        align="right"
                                    />
                                </th>
                            )}
                            {isColumnVisible("weight") && (
                                <th className="text-right px-4 py-3 whitespace-nowrap">
                                    <SortableHeader
                                        label="Poids"
                                        column="weight"
                                        currentColumn={state.sort.column}
                                        currentDirection={state.sort.direction}
                                        onSort={setSort}
                                        align="right"
                                    />
                                </th>
                            )}
                            {isColumnVisible("ytd") && (
                                <th className="text-right px-4 py-3 whitespace-nowrap">
                                    <SortableHeader
                                        label="YTD"
                                        column="ytdPerformance"
                                        currentColumn={state.sort.column}
                                        currentDirection={state.sort.direction}
                                        onSort={setSort}
                                        align="right"
                                    />
                                </th>
                            )}
                            {isColumnVisible("currency") && (
                                <th className="text-right px-4 py-3 whitespace-nowrap">
                                    <SortableHeader
                                        label="Devise"
                                        column="currency"
                                        currentColumn={state.sort.column}
                                        currentDirection={state.sort.direction}
                                        onSort={setSort}
                                        align="right"
                                    />
                                </th>
                            )}
                            {isColumnVisible("bank") && (
                                <th className="text-right px-4 py-3 whitespace-nowrap">
                                    <SortableHeader
                                        label="Banque"
                                        column="bank"
                                        currentColumn={state.sort.column}
                                        currentDirection={state.sort.direction}
                                        onSort={setSort}
                                        align="right"
                                    />
                                </th>
                            )}
                        </tr>
                    </thead>

                    {/* Body */}
                    <tbody>
                        {groupedData.map((group) => (
                            <GroupSection
                                key={group.groupKey}
                                group={group}
                                isExpanded={expandedGroups.has(group.groupKey)}
                                onToggle={() => toggleGroup(group.groupKey)}
                                showGroupHeader={state.groupBy !== null}
                                visibleColumns={state.visibleColumns}
                            />
                        ))}
                    </tbody>
                </table>

                {/* Empty state */}
                {filteredData.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-16 text-center">
                        <p className="text-muted-foreground text-sm">
                            Aucun instrument ne correspond à vos critères.
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
            <TableTotalsBar
                totalAmount={totals.amount}
                totalWeight={totals.weight}
                itemCount={data.length}
                filteredCount={hasActiveFilters ? filteredData.length : undefined}
            />
        </div>
    );
}

// Group section component
interface GroupSectionProps {
    group: GroupedData;
    isExpanded: boolean;
    onToggle: () => void;
    showGroupHeader: boolean;
    visibleColumns: string[];
}

function GroupSection({
    group,
    isExpanded,
    onToggle,
    showGroupHeader,
    visibleColumns,
}: GroupSectionProps) {
    const isColumnVisible = (columnId: string) => visibleColumns.includes(columnId);

    // Calculate column positions for totals alignment
    const colsBefore = (isColumnVisible("name") ? 1 : 0) + 
                       (isColumnVisible("isin") ? 1 : 0) +
                       (isColumnVisible("quantity") ? 1 : 0) +
                       (isColumnVisible("price") ? 1 : 0);
    
    const colsAfter = (isColumnVisible("ytd") ? 1 : 0) +
                      (isColumnVisible("currency") ? 1 : 0) +
                      (isColumnVisible("bank") ? 1 : 0);

    if (!showGroupHeader) {
        return (
            <>
                {group.items.map((item) => (
                    <InstrumentRow
                        key={item.id}
                        item={item}
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
                <td colSpan={colsBefore > 0 ? colsBefore : 1} className="px-4 py-2.5">
                    <div className="flex items-center gap-2">
                        {isExpanded ? (
                            <ChevronDown className="h-4 w-4 text-gold" />
                        ) : (
                            <ChevronRight className="h-4 w-4 text-gold" />
                        )}
                        <span className="font-semibold text-gold text-sm">{group.groupLabel}</span>
                        <span className="text-xs text-gold">
                            ({group.totals.count} position{group.totals.count > 1 ? "s" : ""})
                        </span>
                    </div>
                </td>
                
                {/* Montant - aligned with amount column */}
                {isColumnVisible("amount") && (
                    <td className="text-right px-4 py-2.5">
                        <span className="text-sm font-medium text-gold tabular-nums">
                            {formatCurrency(group.totals.amount, "EUR")}
                        </span>
                    </td>
                )}
                
                {/* Poids - aligned with weight column */}
                {isColumnVisible("weight") && (
                    <td className="text-right px-4 py-2.5">
                        <span className="text-sm font-medium text-gold tabular-nums">
                            {group.totals.weight.toFixed(1)}%
                        </span>
                    </td>
                )}
                
                {/* Empty cells for remaining columns */}
                {colsAfter > 0 && <td colSpan={colsAfter} />}
            </tr>

            {/* Group items */}
            {isExpanded && group.items.map((item) => (
                <InstrumentRow
                    key={item.id}
                    item={item}
                    visibleColumns={visibleColumns}
                    indented
                />
            ))}
        </>
    );
}

// Instrument row component
interface InstrumentRowProps {
    item: FlattenedInstrument;
    visibleColumns: string[];
    indented?: boolean;
}

function InstrumentRow({ item, visibleColumns, indented }: InstrumentRowProps) {
    const isColumnVisible = (columnId: string) => visibleColumns.includes(columnId);

    return (
        <tr className="hover:bg-muted/30 transition-colors border-b border-border">
            {isColumnVisible("name") && (
                <td className={cn("px-4 py-2.5", indented && "pl-10")}>
                    <span className="text-sm text-foreground">{item.name}</span>
                </td>
            )}
            {isColumnVisible("isin") && (
                <td className="px-4 py-2.5">
                    <span className="text-sm text-muted-foreground font-mono">{item.isin}</span>
                </td>
            )}
            {isColumnVisible("quantity") && (
                <td className="text-right px-4 py-2.5">
                    <span className="text-sm text-muted-foreground tabular-nums">
                        {formatNumber(item.quantity)}
                    </span>
                </td>
            )}
            {isColumnVisible("price") && (
                <td className="text-right px-4 py-2.5">
                    <span className="text-sm text-muted-foreground tabular-nums">
                        {formatCurrency(item.price, item.currency)}
                    </span>
                </td>
            )}
            {isColumnVisible("amount") && (
                <td className="text-right px-4 py-2.5">
                    <span className="text-sm font-medium text-foreground tabular-nums">
                        {formatCurrency(item.amount, item.currency)}
                    </span>
                </td>
            )}
            {isColumnVisible("weight") && (
                <td className="text-right px-4 py-2.5">
                    <span className="text-sm text-muted-foreground tabular-nums">
                        {item.weight.toFixed(1)}%
                    </span>
                </td>
            )}
            {isColumnVisible("ytd") && (
                <td className="text-right px-4 py-2.5">
                    <YtdBadge value={item.ytdPerformance} />
                </td>
            )}
            {isColumnVisible("currency") && (
                <td className="text-right px-4 py-2.5">
                    <span className="text-sm text-muted-foreground">{item.currency}</span>
                </td>
            )}
            {isColumnVisible("bank") && (
                <td className="text-right px-4 py-2.5">
                    <span className="text-sm text-muted-foreground">{item.bank || "—"}</span>
                </td>
            )}
        </tr>
    );
}
