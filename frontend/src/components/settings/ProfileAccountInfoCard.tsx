import { SettingsCard } from "./SettingsCard";
import { StatusBadge } from "./StatusBadge";

interface AccountInfo {
  accountId: string;
  createdAt: string;
  lastLogin: string;
  kycStatus: "verified" | "pending" | "not_required";
}

const accountData: AccountInfo = {
  accountId: "ACC-2024-XK7M9P",
  createdAt: "January 15, 2024",
  lastLogin: "Today at 2:34 PM",
  kycStatus: "verified",
};

const KYC_LABELS: Record<AccountInfo["kycStatus"], { text: string; status: "success" | "disabled" }> = {
  verified: { text: "Verified", status: "success" },
  pending: { text: "Pending", status: "disabled" },
  not_required: { text: "Not Required", status: "disabled" },
};

export function ProfileAccountInfoCard() {
  const kycInfo = KYC_LABELS[accountData.kycStatus];

  const fields = [
    { label: "Account ID", value: accountData.accountId },
    { label: "Account created at", value: accountData.createdAt },
    { label: "Last login", value: accountData.lastLogin },
    { label: "KYC status", value: null, badge: kycInfo },
  ];

  return (
    <SettingsCard
      title="Account information"
      description="Your account details and verification status."
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {fields.map((field) => (
          <div key={field.label} className="flex flex-col gap-1">
            <span className="text-sm text-muted-foreground">{field.label}</span>
            {field.badge ? (
              <StatusBadge status={field.badge.status}>{field.badge.text}</StatusBadge>
            ) : (
              <span className="text-foreground font-medium">{field.value}</span>
            )}
          </div>
        ))}
      </div>
    </SettingsCard>
  );
}
