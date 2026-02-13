import { useState } from "react";
import { SettingsCard } from "../SettingsCard";
import { FintechButton } from "../FintechButton";
import { StatusBadge } from "../StatusBadge";
import { toast } from "@/hooks/use-toast";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { CreditCard, Download, Plus, Trash2, AlertTriangle, FileText, Check } from "lucide-react";
import billingMock from "@/mocks/billing.mock.json";

const CURRENT_CARD = billingMock.currentCard;
const SUBSCRIPTION = billingMock.subscription;
const INVOICES = billingMock.invoices as { id: string; date: string; amount: string; status: "paid" | "pending" }[];

const EU_COUNTRIES = [
  "Austria", "Belgium", "France", "Germany", "Ireland", "Italy",
  "Netherlands", "Portugal", "Spain", "Sweden", "Switzerland",
];

type ModalType = "changeCard" | "removeCard" | "cancelSubscription" | null;

export function BillingPage() {
  const [activeModal, setActiveModal] = useState<ModalType>(null);
  const [hasCard, setHasCard] = useState(true);
  const [billingInfo, setBillingInfo] = useState({
    fullName: billingMock.billingInfo.fullName,
    email: billingMock.billingInfo.email,
    address: billingMock.billingInfo.address,
    country: billingMock.billingInfo.country,
    vatNumber: "",
  });
  const [cardForm, setCardForm] = useState({
    number: "",
    expiry: "",
    cvc: "",
    name: "",
  });

  const inputClasses = "w-full bg-input border border-border rounded-lg px-4 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all";
  const labelClasses = "block text-sm font-medium text-foreground mb-2";

  const handleSaveCard = () => {
    setActiveModal(null);
    setCardForm({ number: "", expiry: "", cvc: "", name: "" });
    toast({ title: "Card saved", description: "Your payment method has been updated." });
  };

  const handleRemoveCard = () => {
    setHasCard(false);
    setActiveModal(null);
    toast({ title: "Card removed", description: "Your payment method has been removed." });
  };

  const handleCancelSubscription = () => {
    setActiveModal(null);
    toast({ title: "Subscription cancelled", description: "Your subscription will end at the current billing period." });
  };

  const handleSaveBillingInfo = () => {
    toast({ title: "Billing info saved", description: "Your billing information has been updated." });
  };

  const formatCardExpiry = (value: string) => {
    const cleaned = value.replace(/\D/g, "");
    if (cleaned.length >= 2) {
      return cleaned.slice(0, 2) + " / " + cleaned.slice(2, 4);
    }
    return cleaned;
  };

  return (
    <div className="flex-1 space-y-6 max-w-[1100px]">
      {/* CARD 1: Payment Method */}
      <SettingsCard
        title="Payment method"
        description="Manage your default payment method."
      >
        <div className="space-y-4">
          {hasCard ? (
            <>
              {/* Card Preview */}
              <div className="p-4 rounded-xl border border-border bg-secondary/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-8 rounded bg-gradient-to-r from-blue-600 to-blue-400 flex items-center justify-center">
                    {CURRENT_CARD.brand === "visa" ? (
                      <span className="text-white font-bold text-xs italic">VISA</span>
                    ) : (
                      <CreditCard className="w-5 h-5 text-white" />
                    )}
                  </div>
                  <div className="space-y-0.5">
                    <p className="text-foreground font-medium font-mono">
                      •••• •••• •••• {CURRENT_CARD.last4}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {CURRENT_CARD.name} • Expires {CURRENT_CARD.expMonth}/{CURRENT_CARD.expYear}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <FintechButton
                    variant="outline"
                    onClick={() => setActiveModal("changeCard")}
                    className="px-4 py-2 text-sm"
                  >
                    Change card
                  </FintechButton>
                  <FintechButton
                    variant="outline"
                    onClick={() => setActiveModal("removeCard")}
                    className="px-3 py-2 text-destructive border-destructive/50 hover:bg-destructive/10"
                  >
                    <Trash2 className="w-4 h-4" />
                  </FintechButton>
                </div>
              </div>
            </>
          ) : (
            <div className="py-8 text-center space-y-4">
              <div className="w-14 h-14 rounded-full bg-muted flex items-center justify-center mx-auto">
                <CreditCard className="w-7 h-7 text-muted-foreground" />
              </div>
              <div>
                <p className="text-foreground font-medium">No payment method</p>
                <p className="text-sm text-muted-foreground">Add a card to manage your subscription</p>
              </div>
            </div>
          )}

          <div className="flex justify-end pt-2">
            <FintechButton
              variant="primary"
              onClick={() => setActiveModal("changeCard")}
              className="px-4 py-2.5"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add new card
            </FintechButton>
          </div>
        </div>
      </SettingsCard>

      {/* CARD 2: Subscription */}
      <SettingsCard
        title="Subscription"
        description="Your current plan and billing details."
      >
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="space-y-1">
              <span className="text-sm text-muted-foreground">Current plan</span>
              <p className="text-foreground font-semibold text-lg">{SUBSCRIPTION.plan}</p>
            </div>
            <div className="space-y-1">
              <span className="text-sm text-muted-foreground">Price</span>
              <p className="text-foreground font-medium">{SUBSCRIPTION.price} / month</p>
            </div>
            <div className="space-y-1">
              <span className="text-sm text-muted-foreground">Next billing</span>
              <p className="text-foreground font-medium">{SUBSCRIPTION.nextBillingDate}</p>
            </div>
            <div className="space-y-1">
              <span className="text-sm text-muted-foreground">Status</span>
              <StatusBadge status={SUBSCRIPTION.status === "active" ? "success" : "disabled"}>
                {SUBSCRIPTION.status === "active" ? "Active" : "Cancelled"}
              </StatusBadge>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row justify-end gap-3 pt-4 border-t border-border">
            <FintechButton
              variant="outline"
              onClick={() => setActiveModal("cancelSubscription")}
              className="px-4 py-2.5 text-destructive border-destructive/50 hover:bg-destructive/10"
            >
              Cancel subscription
            </FintechButton>
            <FintechButton variant="primary" className="px-4 py-2.5">
              Upgrade plan
            </FintechButton>
          </div>
        </div>
      </SettingsCard>

      {/* CARD 3: Invoices */}
      <SettingsCard
        title="Invoices"
        description="Download your billing history."
      >
        {INVOICES.length > 0 ? (
          <div className="overflow-x-auto">
            {/* Desktop Table */}
            <table className="w-full hidden sm:table">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Date</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Invoice #</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Amount</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Status</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Download</th>
                </tr>
              </thead>
              <tbody>
                {INVOICES.map((invoice) => (
                  <tr key={invoice.id} className="border-b border-border/50 hover:bg-secondary/30 transition-colors">
                    <td className="py-4 px-4 text-sm text-foreground">{invoice.date}</td>
                    <td className="py-4 px-4 text-sm text-foreground font-mono">{invoice.id}</td>
                    <td className="py-4 px-4 text-sm text-foreground">{invoice.amount}</td>
                    <td className="py-4 px-4">
                      <span className={cn(
                        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium",
                        invoice.status === "paid" ? "bg-success/20 text-success" : "bg-orange-500/20 text-orange-400"
                      )}>
                        {invoice.status === "paid" && <Check className="w-3 h-3" />}
                        {invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-right">
                      <button className="p-2 rounded-lg hover:bg-muted transition-colors" title="Download PDF">
                        <Download className="w-4 h-4 text-muted-foreground hover:text-foreground" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Mobile List */}
            <div className="sm:hidden space-y-3">
              {INVOICES.map((invoice) => (
                <div key={invoice.id} className="p-4 rounded-lg bg-secondary/30 border border-border/50 space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-medium text-foreground">{invoice.date}</p>
                      <p className="text-xs text-muted-foreground font-mono">{invoice.id}</p>
                    </div>
                    <span className={cn(
                      "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium",
                      invoice.status === "paid" ? "bg-success/20 text-success" : "bg-orange-500/20 text-orange-400"
                    )}>
                      {invoice.status === "paid" && <Check className="w-3 h-3" />}
                      {invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-lg font-semibold text-foreground">{invoice.amount}</span>
                    <FintechButton variant="outline" className="px-3 py-1.5 text-xs">
                      <Download className="w-3.5 h-3.5 mr-1.5" />
                      Download
                    </FintechButton>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="py-12 text-center space-y-3">
            <div className="w-14 h-14 rounded-full bg-muted flex items-center justify-center mx-auto">
              <FileText className="w-7 h-7 text-muted-foreground" />
            </div>
            <p className="text-muted-foreground">No invoices available yet.</p>
          </div>
        )}
      </SettingsCard>

      {/* CARD 4: Billing Information */}
      <SettingsCard
        title="Billing information"
        description="Information used for invoicing."
      >
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className={labelClasses}>Full name</label>
              <input
                type="text"
                value={billingInfo.fullName}
                onChange={(e) => setBillingInfo(prev => ({ ...prev, fullName: e.target.value }))}
                placeholder="Full name"
                className={inputClasses}
              />
            </div>
            <div>
              <label className={labelClasses}>Billing email</label>
              <input
                type="email"
                value={billingInfo.email}
                onChange={(e) => setBillingInfo(prev => ({ ...prev, email: e.target.value }))}
                placeholder="billing@example.com"
                className={inputClasses}
              />
            </div>
          </div>
          <div>
            <label className={labelClasses}>Address</label>
            <input
              type="text"
              value={billingInfo.address}
              onChange={(e) => setBillingInfo(prev => ({ ...prev, address: e.target.value }))}
              placeholder="Street address, city, postal code"
              className={inputClasses}
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className={labelClasses}>Country</label>
              <Select value={billingInfo.country} onValueChange={(v) => setBillingInfo(prev => ({ ...prev, country: v }))}>
                <SelectTrigger className={cn(inputClasses, "h-auto")}>
                  <SelectValue placeholder="Select country" />
                </SelectTrigger>
                <SelectContent className="bg-popover border-border">
                  {EU_COUNTRIES.map((c) => (
                    <SelectItem key={c} value={c}>{c}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className={labelClasses}>VAT number <span className="text-muted-foreground">(optional)</span></label>
              <input
                type="text"
                value={billingInfo.vatNumber}
                onChange={(e) => setBillingInfo(prev => ({ ...prev, vatNumber: e.target.value }))}
                placeholder="EU123456789"
                className={inputClasses}
              />
            </div>
          </div>

          <div className="flex justify-end pt-4">
            <FintechButton variant="primary" onClick={handleSaveBillingInfo} className="px-6 py-2.5">
              Save billing info
            </FintechButton>
          </div>
        </div>
      </SettingsCard>

      {/* MODAL: Change Card */}
      <Dialog open={activeModal === "changeCard"} onOpenChange={() => setActiveModal(null)}>
        <DialogContent className="bg-card border-border rounded-2xl max-w-md">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold text-foreground">
              {hasCard ? "Change payment method" : "Add payment method"}
            </DialogTitle>
            <DialogDescription className="text-muted-foreground">
              Enter your card details below.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div>
              <label className={labelClasses}>Card number</label>
              <input
                type="text"
                value={cardForm.number}
                onChange={(e) => setCardForm(prev => ({ ...prev, number: e.target.value }))}
                placeholder="1234 5678 9012 3456"
                maxLength={19}
                className={inputClasses}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelClasses}>Expiry</label>
                <input
                  type="text"
                  value={cardForm.expiry}
                  onChange={(e) => setCardForm(prev => ({ ...prev, expiry: formatCardExpiry(e.target.value) }))}
                  placeholder="MM / YY"
                  maxLength={7}
                  className={inputClasses}
                />
              </div>
              <div>
                <label className={labelClasses}>CVC</label>
                <input
                  type="text"
                  value={cardForm.cvc}
                  onChange={(e) => setCardForm(prev => ({ ...prev, cvc: e.target.value.replace(/\D/g, "").slice(0, 4) }))}
                  placeholder="123"
                  maxLength={4}
                  className={inputClasses}
                />
              </div>
            </div>
            <div>
              <label className={labelClasses}>Cardholder name</label>
              <input
                type="text"
                value={cardForm.name}
                onChange={(e) => setCardForm(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Name on card"
                className={inputClasses}
              />
            </div>
          </div>

          <DialogFooter className="flex flex-col-reverse sm:flex-row gap-3">
            <FintechButton variant="outline" onClick={() => setActiveModal(null)} className="px-5 py-2.5 flex-1 sm:flex-none">
              Cancel
            </FintechButton>
            <FintechButton variant="primary" onClick={handleSaveCard} className="px-5 py-2.5 flex-1 sm:flex-none">
              Save card
            </FintechButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* MODAL: Remove Card */}
      <Dialog open={activeModal === "removeCard"} onOpenChange={() => setActiveModal(null)}>
        <DialogContent className="bg-card border-border rounded-2xl max-w-md">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold text-foreground flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-destructive" />
              Remove payment method?
            </DialogTitle>
            <DialogDescription className="text-muted-foreground">
              Are you sure you want to remove this payment method? You won't be able to renew your subscription without a valid card.
            </DialogDescription>
          </DialogHeader>

          <DialogFooter className="flex flex-col-reverse sm:flex-row gap-3 pt-4">
            <FintechButton variant="outline" onClick={() => setActiveModal(null)} className="px-5 py-2.5 flex-1 sm:flex-none">
              Cancel
            </FintechButton>
            <FintechButton variant="destructive" onClick={handleRemoveCard} className="px-5 py-2.5 flex-1 sm:flex-none">
              Remove card
            </FintechButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* MODAL: Cancel Subscription */}
      <Dialog open={activeModal === "cancelSubscription"} onOpenChange={() => setActiveModal(null)}>
        <DialogContent className="bg-card border-border rounded-2xl max-w-md">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold text-foreground flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-destructive" />
              Cancel subscription?
            </DialogTitle>
          </DialogHeader>

          <div className="py-4 space-y-4">
            <p className="text-muted-foreground">
              Your subscription will remain active until the end of the current billing period on <strong className="text-foreground">{SUBSCRIPTION.nextBillingDate}</strong>.
            </p>
            <div className="p-4 rounded-lg border border-destructive/30 bg-destructive/5 space-y-2">
              <p className="text-sm text-destructive font-medium">You will lose access to:</p>
              <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                <li>Premium features and analytics</li>
                <li>Priority customer support</li>
                <li>Advanced reporting tools</li>
              </ul>
            </div>
          </div>

          <DialogFooter className="flex flex-col-reverse sm:flex-row gap-3">
            <FintechButton variant="outline" onClick={() => setActiveModal(null)} className="px-5 py-2.5 flex-1 sm:flex-none">
              Keep subscription
            </FintechButton>
            <FintechButton variant="destructive" onClick={handleCancelSubscription} className="px-5 py-2.5 flex-1 sm:flex-none">
              Confirm cancel
            </FintechButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
