import { useState } from "react";
import { FintechButton } from "../FintechButton";
import { EU_COUNTRIES, BANKS_BY_COUNTRY } from "./types";
import mockBankAccounts from "@/mocks/bank-accounts.mock.json";
import { Search, ChevronRight, Loader2, CheckCircle2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";

interface AddBankModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: () => void;
}

type Step = "country" | "bank" | "redirect" | "accounts" | "confirmation";

export function AddBankModal({ isOpen, onClose, onComplete }: AddBankModalProps) {
  const [step, setStep] = useState<Step>("country");
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);
  const [selectedBank, setSelectedBank] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedAccounts, setSelectedAccounts] = useState<string[]>([]);

  const resetState = () => {
    setStep("country");
    setSelectedCountry(null);
    setSelectedBank(null);
    setSearchQuery("");
    setSelectedAccounts([]);
  };

  const handleClose = () => {
    resetState();
    onClose();
  };

  const handleComplete = () => {
    resetState();
    onComplete();
  };

  const filteredCountries = EU_COUNTRIES.filter((c) =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const banks = selectedCountry ? BANKS_BY_COUNTRY[selectedCountry] || [] : [];
  const filteredBanks = banks.filter((b) =>
    b.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const mockAccounts: { id: string; name: string }[] = mockBankAccounts;

  const toggleAccount = (accountId: string) => {
    setSelectedAccounts((prev) =>
      prev.includes(accountId)
        ? prev.filter((id) => id !== accountId)
        : [...prev, accountId]
    );
  };

  const inputClasses = "w-full bg-input border border-border rounded-lg px-4 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all";

  const renderStep = () => {
    switch (step) {
      case "country":
        return (
          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search country..."
                className={cn(inputClasses, "pl-10")}
              />
            </div>
            <div className="max-h-[300px] overflow-y-auto space-y-1">
              {filteredCountries.map((country) => (
                <button
                  key={country.code}
                  onClick={() => {
                    setSelectedCountry(country.code);
                    setSearchQuery("");
                    setStep("bank");
                  }}
                  className="w-full flex items-center justify-between p-3 rounded-lg hover:bg-secondary transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{country.flag}</span>
                    <span className="text-foreground">{country.name}</span>
                  </div>
                  <ChevronRight className="w-4 h-4 text-muted-foreground" />
                </button>
              ))}
            </div>
          </div>
        );

      case "bank":
        return (
          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search bank..."
                className={cn(inputClasses, "pl-10")}
              />
            </div>
            <div className="max-h-[300px] overflow-y-auto space-y-1">
              {filteredBanks.length > 0 ? (
                filteredBanks.map((bank) => (
                  <button
                    key={bank.id}
                    onClick={() => {
                      setSelectedBank(bank.id);
                      setSearchQuery("");
                      setStep("redirect");
                    }}
                    className="w-full flex items-center justify-between p-3 rounded-lg hover:bg-secondary transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center overflow-hidden">
                        <img
                          src={bank.logo}
                          alt={bank.name}
                          className="w-6 h-6 object-contain"
                          onError={(e) => {
                            e.currentTarget.style.display = "none";
                          }}
                        />
                      </div>
                      <span className="text-foreground">{bank.name}</span>
                    </div>
                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                  </button>
                ))
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  No banks available for this country yet.
                </p>
              )}
            </div>
            <button
              onClick={() => {
                setStep("country");
                setSearchQuery("");
              }}
              className="text-sm text-primary hover:underline"
            >
              ← Back to countries
            </button>
          </div>
        );

      case "redirect":
        return (
          <div className="py-8 space-y-6 text-center">
            <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center mx-auto">
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-medium text-foreground">
                Redirecting to your bank
              </h3>
              <p className="text-sm text-muted-foreground">
                You'll be securely redirected to your bank for authentication...
              </p>
            </div>
            <FintechButton
              variant="primary"
              onClick={() => setStep("accounts")}
              className="px-8 py-3"
            >
              Continue
            </FintechButton>
          </div>
        );

      case "accounts":
        return (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Select the accounts you want to connect:
            </p>
            <div className="space-y-2">
              {mockAccounts.map((account) => (
                <label
                  key={account.id}
                  className="flex items-center gap-3 p-4 rounded-lg bg-secondary/50 cursor-pointer hover:bg-secondary transition-colors"
                >
                  <Checkbox
                    checked={selectedAccounts.includes(account.id)}
                    onCheckedChange={() => toggleAccount(account.id)}
                    className="border-border data-[state=checked]:bg-primary data-[state=checked]:border-primary"
                  />
                  <span className="text-foreground">{account.name}</span>
                </label>
              ))}
            </div>
            <div className="flex justify-end pt-4">
              <FintechButton
                variant="primary"
                onClick={() => setStep("confirmation")}
                disabled={selectedAccounts.length === 0}
                className="px-6 py-2.5"
              >
                Connect accounts
              </FintechButton>
            </div>
          </div>
        );

      case "confirmation":
        return (
          <div className="py-8 space-y-6 text-center">
            <div className="w-16 h-16 rounded-full bg-success/20 flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-8 h-8 text-success" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-medium text-foreground">
                Bank connected successfully!
              </h3>
              <p className="text-sm text-muted-foreground">
                Your bank account has been successfully connected.
                {selectedAccounts.length} account(s) will now sync automatically.
              </p>
            </div>
            <FintechButton
              variant="primary"
              onClick={handleComplete}
              className="px-8 py-3"
            >
              Finish
            </FintechButton>
          </div>
        );
    }
  };

  const stepTitles: Record<Step, string> = {
    country: "Select country",
    bank: "Select bank",
    redirect: "Bank authentication",
    accounts: "Select accounts",
    confirmation: "Success",
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="bg-card border-border rounded-2xl max-w-md">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold text-foreground">
            {stepTitles[step]}
          </DialogTitle>
        </DialogHeader>
        {renderStep()}
      </DialogContent>
    </Dialog>
  );
}
