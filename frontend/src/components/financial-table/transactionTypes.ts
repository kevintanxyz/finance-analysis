// Transaction Types for Financial Transactions Table

export type TransactionType = "Buy" | "Sell" | "Dividend" | "Transfer" | "Fee" | "Interest";

export interface Transaction {
    id: string;
    description: string;
    date: string;
    type: TransactionType;
    amount: number;        // Quantity or units
    price: number;         // Price per unit
    value: number;         // Total value (amount * price or absolute value)
    currency: string;
    investmentAccount: string;
}

// Investment account display names
export const INVESTMENT_ACCOUNTS: Record<string, string> = {
    "ubs": "UBS",
    "edmond-rothschild": "Edmond de Rothschild",
    "lombard-odier": "Lombard Odier",
    "julius-baer": "Julius Baer",
    "pictet": "Pictet",
};
