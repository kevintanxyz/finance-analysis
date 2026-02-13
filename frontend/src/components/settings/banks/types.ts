export type ConnectionStatus = "connected" | "syncing" | "expired" | "error";

export interface BankAccount {
  id: string;
  name: string;
  iban: string;
  type: "current" | "savings" | "securities" | "loan";
  currency: string;
  balance?: number;
  lastSync: string;
  included: boolean;
}

export interface BankConnection {
  id: string;
  name: string;
  logo: string;
  country: string;
  countryCode: string;
  status: ConnectionStatus;
  lastSync: string;
  accounts: BankAccount[];
}

import mockBanksJson from "@/mocks/banks.mock.json";

export const MOCK_BANKS: BankConnection[] = mockBanksJson as BankConnection[];

export const EU_COUNTRIES = [
  { code: "AT", name: "Austria", flag: "🇦🇹" },
  { code: "BE", name: "Belgium", flag: "🇧🇪" },
  { code: "CH", name: "Switzerland", flag: "🇨🇭" },
  { code: "DE", name: "Germany", flag: "🇩🇪" },
  { code: "ES", name: "Spain", flag: "🇪🇸" },
  { code: "FR", name: "France", flag: "🇫🇷" },
  { code: "IT", name: "Italy", flag: "🇮🇹" },
  { code: "NL", name: "Netherlands", flag: "🇳🇱" },
  { code: "PT", name: "Portugal", flag: "🇵🇹" },
  { code: "SE", name: "Sweden", flag: "🇸🇪" },
];

export const BANKS_BY_COUNTRY: Record<string, { id: string; name: string; logo: string }[]> = {
  CH: [
    { id: "cs", name: "Credit Suisse", logo: "https://logo.clearbit.com/credit-suisse.com" },
    { id: "ubs", name: "UBS", logo: "https://logo.clearbit.com/ubs.com" },
    { id: "zkb", name: "Zürcher Kantonalbank", logo: "https://logo.clearbit.com/zkb.ch" },
  ],
  DE: [
    { id: "db", name: "Deutsche Bank", logo: "https://logo.clearbit.com/db.com" },
    { id: "com", name: "Commerzbank", logo: "https://logo.clearbit.com/commerzbank.de" },
    { id: "n26", name: "N26", logo: "https://logo.clearbit.com/n26.com" },
  ],
  FR: [
    { id: "bnp", name: "BNP Paribas", logo: "https://logo.clearbit.com/bnpparibas.com" },
    { id: "sg", name: "Société Générale", logo: "https://logo.clearbit.com/societegenerale.com" },
    { id: "ca", name: "Crédit Agricole", logo: "https://logo.clearbit.com/credit-agricole.fr" },
  ],
  NL: [
    { id: "ing", name: "ING", logo: "https://logo.clearbit.com/ing.com" },
    { id: "abn", name: "ABN AMRO", logo: "https://logo.clearbit.com/abnamro.nl" },
    { id: "rabo", name: "Rabobank", logo: "https://logo.clearbit.com/rabobank.nl" },
  ],
};
