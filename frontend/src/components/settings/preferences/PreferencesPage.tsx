import { useState } from "react";
import { SettingsCard } from "../SettingsCard";
import { FintechButton } from "../FintechButton";
import { FintechToggle } from "../FintechToggle";
import { toast } from "@/hooks/use-toast";
import { useTheme, ThemeMode } from "@/contexts/ThemeContext";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { Sparkles, Moon, Sun, Download, FileText, Unlink, RotateCcw } from "lucide-react";

interface Preferences {
  // Appearance
  theme: "light" | "dark" | "system";
  // Display
  defaultCurrency: string;
  multiCurrencyAggregation: boolean;
  referenceCurrency: string;
  dateFormat: string;
  numberFormat: string;
  decimalPrecision: "2" | "3" | "4";
  defaultLandingPage: string;
  rowsPerPage: "10" | "25" | "50";
  defaultSorting: string;
  showBalances: boolean;
}

const initialPreferences: Preferences = {
  theme: "system",
  defaultCurrency: "EUR",
  multiCurrencyAggregation: false,
  referenceCurrency: "EUR",
  dateFormat: "DD/MM/YYYY",
  numberFormat: "1,234.56",
  decimalPrecision: "2",
  defaultLandingPage: "dashboard",
  rowsPerPage: "25",
  defaultSorting: "date-desc",
  showBalances: true,
};

const CURRENCIES = ["EUR", "USD", "GBP", "CHF", "SEK", "NOK", "DKK"];
const DATE_FORMATS = ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"];
const NUMBER_FORMATS = ["1,234.56", "1.234,56", "1 234,56"];
const LANDING_PAGES = [
  { value: "dashboard", label: "Dashboard" },
  { value: "accounts", label: "Accounts" },
  { value: "portfolio", label: "Portfolio" },
  { value: "reports", label: "Reports" },
];
const SORTING_OPTIONS = [
  { value: "date-desc", label: "Date (newest first)" },
  { value: "date-asc", label: "Date (oldest first)" },
  { value: "amount-desc", label: "Amount (high to low)" },
  { value: "amount-asc", label: "Amount (low to high)" },
];

export function PreferencesPage() {
  const { theme: currentTheme, setTheme } = useTheme();
  const [prefs, setPrefs] = useState<Preferences>(initialPreferences);
  const [hasChanges, setHasChanges] = useState(false);

  const updatePref = <K extends keyof Preferences>(key: K, value: Preferences[K]) => {
    setPrefs((prev) => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const handleThemeChange = (newTheme: ThemeMode) => {
    setTheme(newTheme);
    toast({
      title: "Theme updated",
      description: `Switched to ${newTheme === "classic" ? "Classic (Blue/Gold)" : newTheme === "premium" ? "Premium (Dark/Blue)" : "Light"} theme.`,
    });
  };

  const handleSave = () => {
    setHasChanges(false);
    toast({
      title: "Preferences saved",
      description: "Your preferences have been updated successfully.",
    });
  };

  const handleReset = () => {
    setPrefs(initialPreferences);
    setHasChanges(true);
    toast({
      title: "Preferences reset",
      description: "All preferences have been reset to defaults.",
    });
  };

  const inputClasses = "w-full bg-input border border-border rounded-lg px-4 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all";
  const labelClasses = "block text-sm font-medium text-foreground mb-2";
  const descriptionClasses = "text-xs text-muted-foreground mt-1";
  const sectionClasses = "space-y-4 pt-4 border-t border-border first:pt-0 first:border-t-0";

  const themeOptions: { value: ThemeMode; icon: typeof Moon; label: string; description: string }[] = [
    { value: "classic", icon: Moon, label: "Classic", description: "Blue background with gold accents" },
    { value: "premium", icon: Sparkles, label: "Premium", description: "Dark grey with deep blue accents" },
    { value: "light", icon: Sun, label: "Light", description: "Cream white with blue accents" },
  ];

  return (
    <div className="flex-1 space-y-6 max-w-[1000px]">
      {/* CARD 1: Appearance */}
      <SettingsCard
        title="Appearance"
        description="Customize how the application looks and feels."
      >
        <div className="space-y-6">
          {/* Theme */}
          <div>
            <label className={labelClasses}>Theme</label>
            <p className={cn(descriptionClasses, "mb-4")}>Choose your preferred color scheme</p>
            <div className="flex flex-wrap gap-3">
              {themeOptions.map((option) => {
                const Icon = option.icon;
                const isActive = currentTheme === option.value;
                return (
                  <button
                    key={option.value}
                    onClick={() => handleThemeChange(option.value)}
                    className={cn(
                      "flex items-center gap-3 px-5 py-3 rounded-lg border transition-all min-w-[160px]",
                      isActive
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-transparent border-border text-muted-foreground hover:text-foreground hover:border-primary/50"
                    )}
                  >
                    <Icon className="w-5 h-5" />
                    <div className="text-left">
                      <div className="font-medium">{option.label}</div>
                      <div className={cn("text-xs", isActive ? "text-primary-foreground/70" : "text-muted-foreground")}>{option.description}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </SettingsCard>

      {/* CARD 2: Display */}
      <SettingsCard
        title="Display"
        description="Control how financial data is displayed."
      >
        <div className="space-y-6">
          {/* Financial Section */}
          <div className={sectionClasses}>
            <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Financial</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className={labelClasses}>Default currency</label>
                <Select value={prefs.defaultCurrency} onValueChange={(v) => updatePref("defaultCurrency", v)}>
                  <SelectTrigger className={cn(inputClasses, "h-auto")}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-popover border-border">
                    {CURRENCIES.map((c) => (
                      <SelectItem key={c} value={c}>{c}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm text-foreground">Multi-currency aggregation</span>
                <p className={descriptionClasses}>Combine balances across currencies</p>
              </div>
              <FintechToggle checked={prefs.multiCurrencyAggregation} onChange={(v) => updatePref("multiCurrencyAggregation", v)} />
            </div>
            {prefs.multiCurrencyAggregation && (
              <div>
                <label className={labelClasses}>Reference currency</label>
                <Select value={prefs.referenceCurrency} onValueChange={(v) => updatePref("referenceCurrency", v)}>
                  <SelectTrigger className={cn(inputClasses, "h-auto max-w-[200px]")}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-popover border-border">
                    {CURRENCIES.map((c) => (
                      <SelectItem key={c} value={c}>{c}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          {/* Formats Section */}
          <div className={sectionClasses}>
            <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Formats</h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className={labelClasses}>Date format</label>
                <Select value={prefs.dateFormat} onValueChange={(v) => updatePref("dateFormat", v)}>
                  <SelectTrigger className={cn(inputClasses, "h-auto")}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-popover border-border">
                    {DATE_FORMATS.map((f) => (
                      <SelectItem key={f} value={f}>{f}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className={labelClasses}>Number format</label>
                <Select value={prefs.numberFormat} onValueChange={(v) => updatePref("numberFormat", v)}>
                  <SelectTrigger className={cn(inputClasses, "h-auto")}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-popover border-border">
                    {NUMBER_FORMATS.map((f) => (
                      <SelectItem key={f} value={f}>{f}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className={labelClasses}>Decimal precision</label>
                <div className="flex gap-1">
                  {["2", "3", "4"].map((p) => (
                    <button
                      key={p}
                      onClick={() => updatePref("decimalPrecision", p as Preferences["decimalPrecision"])}
                      className={cn(
                        "flex-1 py-2.5 rounded-lg border text-sm font-medium transition-all",
                        prefs.decimalPrecision === p
                          ? "bg-primary text-primary-foreground border-primary"
                          : "bg-transparent border-border text-muted-foreground hover:text-foreground"
                      )}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Dashboard Section */}
          <div className={sectionClasses}>
            <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Dashboard</h4>
            <div>
              <label className={labelClasses}>Default landing page</label>
              <Select value={prefs.defaultLandingPage} onValueChange={(v) => updatePref("defaultLandingPage", v)}>
                <SelectTrigger className={cn(inputClasses, "h-auto max-w-[250px]")}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-popover border-border">
                  {LANDING_PAGES.map((p) => (
                    <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Tables Section */}
          <div className={sectionClasses}>
            <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Tables</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className={labelClasses}>Rows per page</label>
                <div className="flex gap-1">
                  {["10", "25", "50"].map((r) => (
                    <button
                      key={r}
                      onClick={() => updatePref("rowsPerPage", r as Preferences["rowsPerPage"])}
                      className={cn(
                        "flex-1 py-2.5 rounded-lg border text-sm font-medium transition-all",
                        prefs.rowsPerPage === r
                          ? "bg-primary text-primary-foreground border-primary"
                          : "bg-transparent border-border text-muted-foreground hover:text-foreground"
                      )}
                    >
                      {r}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className={labelClasses}>Default sorting</label>
                <Select value={prefs.defaultSorting} onValueChange={(v) => updatePref("defaultSorting", v)}>
                  <SelectTrigger className={cn(inputClasses, "h-auto")}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-popover border-border">
                    {SORTING_OPTIONS.map((s) => (
                      <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm text-foreground">Show balances by default</span>
                <p className={descriptionClasses}>Display account balances in tables</p>
              </div>
              <FintechToggle checked={prefs.showBalances} onChange={(v) => updatePref("showBalances", v)} />
            </div>
          </div>
        </div>
      </SettingsCard>


      {/* CARD 4: Data & Privacy */}
      <SettingsCard
        title="Data & privacy"
        description="Manage your personal data and connected services."
      >
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-3">
            <div className="flex-1">
              <span className="text-sm text-foreground font-medium">Export my data</span>
              <p className={descriptionClasses}>Download a copy of your personal and financial data</p>
            </div>
            <button className="px-4 py-2.5 w-full sm:w-[180px] rounded-[4px] bg-primary/85 text-primary-foreground text-sm font-medium flex items-center justify-center gap-2 hover:bg-primary transition-colors">
              <Download className="w-4 h-4" />
              Export data
            </button>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-3 border-t border-border">
            <div className="flex-1">
              <span className="text-sm text-foreground font-medium">Download account report</span>
              <p className={descriptionClasses}>Includes profile information and connected banks</p>
            </div>
            <button className="px-4 py-2.5 w-full sm:w-[180px] rounded-[4px] bg-primary/85 text-primary-foreground text-sm font-medium flex items-center justify-center gap-2 hover:bg-primary transition-colors">
              <FileText className="w-4 h-4" />
              Download report
            </button>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-3 border-t border-border">
            <div className="flex-1">
              <span className="text-sm text-foreground font-medium">Revoke all bank connections</span>
              <p className={descriptionClasses}>Immediately disconnect all connected banks</p>
            </div>
            <button className="px-4 py-2.5 w-full sm:w-[180px] rounded-[4px] bg-primary/85 text-primary-foreground text-sm font-medium flex items-center justify-center gap-2 hover:bg-primary transition-colors">
              <Unlink className="w-4 h-4" />
              Revoke all
            </button>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-3 border-t border-border">
            <div className="flex-1">
              <span className="text-sm text-foreground font-medium">Reset preferences</span>
              <p className={descriptionClasses}>Restore all settings to default values</p>
            </div>
            <button onClick={handleReset} className="px-4 py-2.5 w-full sm:w-[180px] rounded-[4px] bg-primary/85 text-primary-foreground text-sm font-medium flex items-center justify-center gap-2 hover:bg-primary transition-colors">
              <RotateCcw className="w-4 h-4" />
              Reset
            </button>
          </div>
        </div>
      </SettingsCard>

      {/* Save Button */}
      <div className="flex items-center justify-between pt-2">
        <div>
          {hasChanges && (
            <span className="text-sm text-accent animate-pulse">You have unsaved changes</span>
          )}
        </div>
        <FintechButton
          variant="primary"
          onClick={handleSave}
          disabled={!hasChanges}
          className="px-6 py-2.5"
        >
          Save preferences
        </FintechButton>
      </div>
    </div>
  );
}
