import { z } from "zod";

// ============= ENUMS =============

export const ThemeEnum = z.enum(["light", "dark", "system"]);
export type Theme = z.infer<typeof ThemeEnum>;

export const LanguageEnum = z.enum(["fr", "en", "de", "es"]);
export type Language = z.infer<typeof LanguageEnum>;

export const CurrencyDisplayEnum = z.enum(["EUR", "USD", "GBP", "CHF"]);
export type CurrencyDisplay = z.infer<typeof CurrencyDisplayEnum>;

export const DateFormatEnum = z.enum(["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"]);
export type DateFormat = z.infer<typeof DateFormatEnum>;

export const BankConnectionStatusEnum = z.enum(["connected", "disconnected", "error", "pending"]);
export type BankConnectionStatus = z.infer<typeof BankConnectionStatusEnum>;

export const SubscriptionPlanEnum = z.enum(["free", "pro", "enterprise"]);
export type SubscriptionPlan = z.infer<typeof SubscriptionPlanEnum>;

export const BillingCycleEnum = z.enum(["monthly", "yearly"]);
export type BillingCycle = z.infer<typeof BillingCycleEnum>;

// ============= PROFILE SCHEMAS =============

export const profileSchema = z.object({
    id: z.string().uuid(),
    userId: z.string().uuid(),
    firstName: z.string().min(1, "Le prénom est requis"),
    lastName: z.string().min(1, "Le nom est requis"),
    email: z.string().email("Format email invalide"),
    phone: z.string().optional(),
    avatarUrl: z.string().url().optional().nullable(),
    company: z.string().optional(),
    jobTitle: z.string().optional(),
    createdAt: z.string().datetime(),
    updatedAt: z.string().datetime(),
});
export type Profile = z.infer<typeof profileSchema>;

export const updateProfileSchema = z.object({
    firstName: z.string().min(1, "Le prénom est requis").optional(),
    lastName: z.string().min(1, "Le nom est requis").optional(),
    phone: z.string().optional(),
    company: z.string().optional(),
    jobTitle: z.string().optional(),
});
export type UpdateProfileRequest = z.infer<typeof updateProfileSchema>;

export const changePasswordSchema = z.object({
    currentPassword: z.string().min(1, "Le mot de passe actuel est requis"),
    newPassword: z.string().min(6, "Minimum 6 caractères"),
    confirmPassword: z.string(),
}).refine((data) => data.newPassword === data.confirmPassword, {
    message: "Les mots de passe ne correspondent pas",
    path: ["confirmPassword"],
});
export type ChangePasswordRequest = z.infer<typeof changePasswordSchema>;

// ============= PREFERENCES SCHEMAS =============

export const preferencesSchema = z.object({
    id: z.string().uuid(),
    userId: z.string().uuid(),
    theme: ThemeEnum,
    language: LanguageEnum,
    currency: CurrencyDisplayEnum,
    dateFormat: DateFormatEnum,
    emailNotifications: z.boolean(),
    pushNotifications: z.boolean(),
    weeklyDigest: z.boolean(),
    marketAlerts: z.boolean(),
    twoFactorEnabled: z.boolean(),
    createdAt: z.string().datetime(),
    updatedAt: z.string().datetime(),
});
export type Preferences = z.infer<typeof preferencesSchema>;

export const updatePreferencesSchema = preferencesSchema.partial().omit({
    id: true,
    userId: true,
    createdAt: true,
    updatedAt: true,
});
export type UpdatePreferencesRequest = z.infer<typeof updatePreferencesSchema>;

// ============= BANK CONNECTION SCHEMAS =============

export const bankAccountSchema = z.object({
    id: z.string().uuid(),
    name: z.string(),
    type: z.string(),
    balance: z.number(),
    currency: z.string(),
    lastSync: z.string().datetime(),
    enabled: z.boolean(),
});
export type BankAccount = z.infer<typeof bankAccountSchema>;

export const bankConnectionDetailSchema = z.object({
    id: z.string().uuid(),
    userId: z.string().uuid(),
    bankName: z.string(),
    bankLogo: z.string().url().optional(),
    status: BankConnectionStatusEnum,
    accounts: z.array(bankAccountSchema),
    lastSync: z.string().datetime().optional(),
    errorMessage: z.string().optional(),
    createdAt: z.string().datetime(),
    updatedAt: z.string().datetime(),
});
export type BankConnectionDetail = z.infer<typeof bankConnectionDetailSchema>;

export const connectBankSchema = z.object({
    bankId: z.string().min(1, "L'identifiant de la banque est requis"),
    credentials: z.record(z.string(), z.string()).optional(),
});
export type ConnectBankRequest = z.infer<typeof connectBankSchema>;

export const updateBankAccountsSchema = z.object({
    accounts: z.array(z.object({
        id: z.string().uuid(),
        enabled: z.boolean(),
    })),
});
export type UpdateBankAccountsRequest = z.infer<typeof updateBankAccountsSchema>;

// ============= BILLING SCHEMAS =============

export const invoiceSchema = z.object({
    id: z.string().uuid(),
    number: z.string(),
    date: z.string().datetime(),
    amount: z.number(),
    currency: z.string(),
    status: z.enum(["paid", "pending", "failed"]),
    pdfUrl: z.string().url().optional(),
});
export type Invoice = z.infer<typeof invoiceSchema>;

export const subscriptionSchema = z.object({
    id: z.string().uuid(),
    userId: z.string().uuid(),
    plan: SubscriptionPlanEnum,
    billingCycle: BillingCycleEnum,
    status: z.enum(["active", "cancelled", "past_due", "trialing"]),
    currentPeriodStart: z.string().datetime(),
    currentPeriodEnd: z.string().datetime(),
    cancelAtPeriodEnd: z.boolean(),
    amount: z.number(),
    currency: z.string(),
    createdAt: z.string().datetime(),
    updatedAt: z.string().datetime(),
});
export type Subscription = z.infer<typeof subscriptionSchema>;

export const billingInfoSchema = z.object({
    subscription: subscriptionSchema.nullable(),
    invoices: z.array(invoiceSchema),
    paymentMethod: z.object({
        type: z.enum(["card", "sepa"]),
        last4: z.string(),
        expiryMonth: z.number().optional(),
        expiryYear: z.number().optional(),
        brand: z.string().optional(),
    }).nullable(),
});
export type BillingInfo = z.infer<typeof billingInfoSchema>;

export const updateSubscriptionSchema = z.object({
    plan: SubscriptionPlanEnum,
    billingCycle: BillingCycleEnum.optional(),
});
export type UpdateSubscriptionRequest = z.infer<typeof updateSubscriptionSchema>;

export const cancelSubscriptionSchema = z.object({
    cancelAtPeriodEnd: z.boolean().default(true),
    reason: z.string().optional(),
});
export type CancelSubscriptionRequest = z.infer<typeof cancelSubscriptionSchema>;

// ============= API RESPONSE SCHEMAS =============

export const profileResponseSchema = z.object({
    profile: profileSchema,
});
export type ProfileResponse = z.infer<typeof profileResponseSchema>;

export const preferencesResponseSchema = z.object({
    preferences: preferencesSchema,
});
export type PreferencesResponse = z.infer<typeof preferencesResponseSchema>;

export const bankConnectionsResponseSchema = z.object({
    connections: z.array(bankConnectionDetailSchema),
    total: z.number(),
});
export type BankConnectionsResponse = z.infer<typeof bankConnectionsResponseSchema>;

export const billingResponseSchema = z.object({
    billing: billingInfoSchema,
});
export type BillingResponse = z.infer<typeof billingResponseSchema>;

export const settingsMessageResponseSchema = z.object({
    message: z.string(),
});
export type SettingsMessageResponse = z.infer<typeof settingsMessageResponseSchema>;
