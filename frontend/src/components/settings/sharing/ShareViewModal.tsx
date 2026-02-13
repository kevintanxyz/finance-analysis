import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { FintechButton } from "../FintechButton";
import { FintechToggle } from "../FintechToggle";
import { cn } from "@/lib/utils";
import { Check, Search, CheckCircle, Mail } from "lucide-react";
import type {
  ShareConfig,
  ViewType,
  AccessDuration,
  AccountGroup,
} from "./types";
import { VIEW_TYPE_LABELS, MOCK_ACCOUNT_GROUPS } from "./types";

interface ShareViewModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const INITIAL_CONFIG: ShareConfig = {
  recipient: { name: "", email: "", message: "" },
  viewType: "portfolio",
  selectedAccounts: [],
  permissions: {
    viewBalances: true,
    viewTransactions: true,
    viewPerformance: true,
    downloadData: false,
    hideAccountNames: false,
  },
  duration: "unlimited",
  requireVerification: true,
};

export function ShareViewModal({ isOpen, onClose }: ShareViewModalProps) {
  const [step, setStep] = useState(1);
  const [config, setConfig] = useState<ShareConfig>(INITIAL_CONFIG);
  const [searchQuery, setSearchQuery] = useState("");
  const [showSuccess, setShowSuccess] = useState(false);

  const totalSteps = 5;

  const handleClose = () => {
    setStep(1);
    setConfig(INITIAL_CONFIG);
    setSearchQuery("");
    setShowSuccess(false);
    onClose();
  };

  const handleNext = () => {
    if (step < totalSteps) {
      setStep(step + 1);
    } else {
      // Submit
      setShowSuccess(true);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const isStepValid = () => {
    switch (step) {
      case 1:
        return config.recipient.name.trim() !== "" && config.recipient.email.trim() !== "";
      case 2:
        return true;
      case 3:
        return config.selectedAccounts.length > 0;
      case 4:
        return true;
      case 5:
        return true;
      default:
        return true;
    }
  };

  const toggleAccount = (accountId: string) => {
    setConfig((prev) => ({
      ...prev,
      selectedAccounts: prev.selectedAccounts.includes(accountId)
        ? prev.selectedAccounts.filter((id) => id !== accountId)
        : [...prev.selectedAccounts, accountId],
    }));
  };

  const selectAllAccounts = () => {
    const allIds = MOCK_ACCOUNT_GROUPS.flatMap((g) => g.accounts.map((a) => a.id));
    setConfig((prev) => ({
      ...prev,
      selectedAccounts: allIds,
    }));
  };

  const filteredGroups = MOCK_ACCOUNT_GROUPS.map((group) => ({
    ...group,
    accounts: group.accounts.filter((acc) =>
      acc.name.toLowerCase().includes(searchQuery.toLowerCase())
    ),
  })).filter((g) => g.accounts.length > 0);

  if (showSuccess) {
    return (
      <Dialog open={isOpen} onOpenChange={handleClose}>
        <DialogContent className="bg-card border-border rounded-2xl max-w-[600px]">
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="w-16 h-16 rounded-full bg-success/20 flex items-center justify-center mb-6">
              <CheckCircle className="w-8 h-8 text-success" />
            </div>
            <h2 className="text-2xl font-semibold text-foreground mb-2">
              Invitation sent
            </h2>
            <p className="text-muted-foreground mb-8">
              An email has been sent to {config.recipient.email}
            </p>
            <FintechButton variant="primary" onClick={handleClose} className="px-8">
              Done
            </FintechButton>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="bg-card border-border rounded-2xl max-w-[600px] max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <div className="flex items-center justify-between">
            <DialogTitle className="text-xl font-semibold text-foreground">
              Share a view
            </DialogTitle>
            <span className="text-sm text-muted-foreground">
              {step}/{totalSteps}
            </span>
          </div>
          {/* Progress bar */}
          <div className="flex gap-1.5 mt-4">
            {Array.from({ length: totalSteps }).map((_, i) => (
              <div
                key={i}
                className={cn(
                  "h-1 flex-1 rounded-full transition-colors",
                  i < step ? "bg-primary" : "bg-muted"
                )}
              />
            ))}
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto py-6">
          {/* Step 1: Recipient */}
          {step === 1 && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-foreground">
                Who do you want to share with?
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-2">
                    Full name
                  </label>
                  <input
                    type="text"
                    value={config.recipient.name}
                    onChange={(e) =>
                      setConfig((prev) => ({
                        ...prev,
                        recipient: { ...prev.recipient, name: e.target.value },
                      }))
                    }
                    className="w-full px-4 py-3 rounded-lg bg-secondary border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="John Doe"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-2">
                    Email address
                  </label>
                  <input
                    type="email"
                    value={config.recipient.email}
                    onChange={(e) =>
                      setConfig((prev) => ({
                        ...prev,
                        recipient: { ...prev.recipient, email: e.target.value },
                      }))
                    }
                    className="w-full px-4 py-3 rounded-lg bg-secondary border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="john@example.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-2">
                    Optional message
                  </label>
                  <textarea
                    value={config.recipient.message || ""}
                    onChange={(e) =>
                      setConfig((prev) => ({
                        ...prev,
                        recipient: { ...prev.recipient, message: e.target.value },
                      }))
                    }
                    rows={3}
                    className="w-full px-4 py-3 rounded-lg bg-secondary border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                    placeholder="Add a personal message..."
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 2: View type */}
          {step === 2 && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-foreground">
                Select view type
              </h3>
              <div className="space-y-3">
                {(Object.keys(VIEW_TYPE_LABELS) as ViewType[]).map((type) => {
                  const { title, description } = VIEW_TYPE_LABELS[type];
                  const isSelected = config.viewType === type;
                  return (
                    <button
                      key={type}
                      onClick={() => setConfig((prev) => ({ ...prev, viewType: type }))}
                      className={cn(
                        "w-full p-4 rounded-lg border text-left transition-all",
                        isSelected
                          ? "border-primary bg-primary/10"
                          : "border-border bg-secondary hover:border-primary/50"
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-foreground">{title}</p>
                          <p className="text-sm text-muted-foreground">{description}</p>
                        </div>
                        {isSelected && (
                          <div className="w-5 h-5 rounded-full bg-primary flex items-center justify-center">
                            <Check className="w-3 h-3 text-primary-foreground" />
                          </div>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Step 3: Select accounts */}
          {step === 3 && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-foreground">
                  Select accounts to share
                </h3>
                <span className="text-sm text-primary font-medium">
                  {config.selectedAccounts.length} accounts selected
                </span>
              </div>

              <div className="flex items-center gap-3">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-secondary border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                    placeholder="Search accounts..."
                  />
                </div>
                <button
                  onClick={selectAllAccounts}
                  className="text-sm text-primary hover:underline"
                >
                  Select all
                </button>
              </div>

              <div className="space-y-4">
                {filteredGroups.map((group) => (
                  <div key={group.bankId} className="space-y-2">
                    <div className="flex items-center gap-2">
                      <img
                        src={group.bankLogo}
                        alt={group.bankName}
                        className="w-5 h-5 rounded"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src = "/placeholder.svg";
                        }}
                      />
                      <span className="text-sm font-medium text-foreground">
                        {group.bankName}
                      </span>
                    </div>
                    <div className="space-y-1 pl-7">
                      {group.accounts.map((account) => {
                        const isSelected = config.selectedAccounts.includes(account.id);
                        return (
                          <button
                            key={account.id}
                            onClick={() => toggleAccount(account.id)}
                            className={cn(
                              "w-full flex items-center justify-between p-3 rounded-lg transition-colors",
                              isSelected
                                ? "bg-primary/10 border border-primary"
                                : "bg-secondary border border-transparent hover:border-border"
                            )}
                          >
                            <span className="text-sm text-foreground">
                              {account.name} ({account.currency})
                            </span>
                            <div
                              className={cn(
                                "w-5 h-5 rounded border-2 flex items-center justify-center transition-colors",
                                isSelected
                                  ? "bg-primary border-primary"
                                  : "border-muted-foreground"
                              )}
                            >
                              {isSelected && <Check className="w-3 h-3 text-primary-foreground" />}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Step 4: Permissions */}
          {step === 4 && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-foreground">Permissions</h3>
              <div className="space-y-4">
                {[
                  { key: "viewBalances", label: "View balances" },
                  { key: "viewTransactions", label: "View transactions" },
                  { key: "viewPerformance", label: "View performance" },
                  { key: "downloadData", label: "Download data" },
                  { key: "hideAccountNames", label: "Hide account names" },
                ].map(({ key, label }) => (
                  <div
                    key={key}
                    className="flex items-center justify-between p-4 rounded-lg bg-secondary"
                  >
                    <span className="text-foreground">{label}</span>
                    <FintechToggle
                      checked={config.permissions[key as keyof typeof config.permissions]}
                      onChange={(checked) =>
                        setConfig((prev) => ({
                          ...prev,
                          permissions: { ...prev.permissions, [key]: checked },
                        }))
                      }
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Step 5: Duration & confirm */}
          {step === 5 && (
            <div className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-foreground">Access duration</h3>
                <div className="grid grid-cols-2 gap-3">
                  {(["unlimited", "7days", "30days", "custom"] as AccessDuration[]).map(
                    (duration) => {
                      const labels: Record<AccessDuration, string> = {
                        unlimited: "Unlimited",
                        "7days": "7 days",
                        "30days": "30 days",
                        custom: "Custom date",
                      };
                      const isSelected = config.duration === duration;
                      return (
                        <button
                          key={duration}
                          onClick={() => setConfig((prev) => ({ ...prev, duration }))}
                          className={cn(
                            "p-3 rounded-lg border text-sm font-medium transition-all",
                            isSelected
                              ? "border-primary bg-primary/10 text-foreground"
                              : "border-border bg-secondary text-muted-foreground hover:border-primary/50"
                          )}
                        >
                          {labels[duration]}
                        </button>
                      );
                    }
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between p-4 rounded-lg bg-secondary">
                <div className="flex items-center gap-2">
                  <Mail className="w-4 h-4 text-muted-foreground" />
                  <span className="text-foreground">Require email verification</span>
                </div>
                <FintechToggle
                  checked={config.requireVerification}
                  onChange={(checked) =>
                    setConfig((prev) => ({ ...prev, requireVerification: checked }))
                  }
                />
              </div>

              {/* Summary */}
              <div className="p-4 rounded-lg bg-muted/50 space-y-3">
                <h4 className="text-sm font-medium text-foreground">Summary</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Recipient</span>
                    <span className="text-foreground">{config.recipient.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">View type</span>
                    <span className="text-foreground">
                      {VIEW_TYPE_LABELS[config.viewType].title}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Accounts selected</span>
                    <span className="text-foreground">{config.selectedAccounts.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Duration</span>
                    <span className="text-foreground">
                      {config.duration === "unlimited"
                        ? "Unlimited"
                        : config.duration === "7days"
                        ? "7 days"
                        : config.duration === "30days"
                        ? "30 days"
                        : "Custom"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex-shrink-0 flex items-center justify-between pt-4 border-t border-border">
          {step > 1 ? (
            <FintechButton variant="outline" onClick={handleBack}>
              Back
            </FintechButton>
          ) : (
            <div />
          )}
          <FintechButton
            variant="primary"
            onClick={handleNext}
            disabled={!isStepValid()}
            className="min-w-[140px]"
          >
            {step === totalSteps ? "Send invitation" : "Continue"}
          </FintechButton>
        </div>
      </DialogContent>
    </Dialog>
  );
}
