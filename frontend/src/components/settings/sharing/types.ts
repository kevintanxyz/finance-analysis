export type ShareStatus = "active" | "pending" | "revoked";
export type ViewType = "portfolio" | "accounts" | "custom";
export type AccessDuration = "unlimited" | "7days" | "30days" | "custom";

export interface SharedUser {
  id: string;
  name: string;
  email: string;
  viewType: ViewType;
  accountsShared: number;
  status: ShareStatus;
  createdAt: string;
  expiresAt?: string;
}

export interface SharePermissions {
  viewBalances: boolean;
  viewTransactions: boolean;
  viewPerformance: boolean;
  downloadData: boolean;
  hideAccountNames: boolean;
}

export interface ShareConfig {
  recipient: {
    name: string;
    email: string;
    message?: string;
  };
  viewType: ViewType;
  selectedAccounts: string[];
  permissions: SharePermissions;
  duration: AccessDuration;
  customDate?: string;
  requireVerification: boolean;
}

export interface AccountGroup {
  bankId: string;
  bankName: string;
  bankLogo: string;
  accounts: {
    id: string;
    name: string;
    currency: string;
  }[];
}

export const VIEW_TYPE_LABELS: Record<ViewType, { title: string; description: string }> = {
  portfolio: {
    title: "Portfolio summary",
    description: "High-level balances and performance",
  },
  accounts: {
    title: "Accounts view",
    description: "Selected accounts and transactions",
  },
  custom: {
    title: "Custom view",
    description: "Choose specific accounts and data",
  },
};

import mockSharedUsersJson from "@/mocks/shared-users.mock.json";
import mockAccountGroupsJson from "@/mocks/account-groups.mock.json";

export const MOCK_SHARED_USERS: SharedUser[] = mockSharedUsersJson as SharedUser[];

export const MOCK_ACCOUNT_GROUPS: AccountGroup[] = mockAccountGroupsJson as AccountGroup[];
