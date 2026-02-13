import { TableCell, TableRow } from "@/components/ui/table";

export function InstrumentHeader() {
    return (
        <TableRow className="bg-muted/30 hover:bg-muted/30 border-b border-border/50">
            <TableCell colSpan={4} className="py-1.5 px-0">
                <div className="grid grid-cols-6 gap-4 pl-10 pr-4">
                    <div className="text-gold font-medium text-xs">
                        Instrument
                    </div>
                    <div className="text-gold font-medium text-xs text-right">
                        Quantity
                    </div>
                    <div className="text-gold font-medium text-xs text-right">
                        Price
                    </div>
                    <div className="text-gold font-medium text-xs text-right">
                        Amount
                    </div>
                    <div className="text-gold font-medium text-xs text-right">
                        Weight
                    </div>
                    <div className="text-gold font-medium text-xs">
                        Asset Class
                    </div>
                </div>
            </TableCell>
        </TableRow>
    );
}
