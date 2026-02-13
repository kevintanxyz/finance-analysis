import { z } from "zod";
import {
    MeetingStatusEnum,
    TaskCategoryEnum,
    TaskStatusEnum,
    TaskPriorityEnum,
    DataStatusEnum,
    DataSourceEnum,
    CashflowTypeEnum,
    ActivityTypeEnum,
    OnboardingStatusEnum,
    SortOptionEnum,
} from "../../enums";
import { paginationParamsSchema, paginationMetaSchema } from "../common/api.schema";

// ============= CLIENT SCHEMAS =============

export const clientAddressSchema = z.object({
    line1: z.string().min(1, "L'adresse est requise"),
    line2: z.string().optional(),
    city: z.string().min(1, "La ville est requise"),
    postalCode: z.string().min(1, "Le code postal est requis"),
    country: z.string().min(1, "Le pays est requis"),
});
export type ClientAddress = z.infer<typeof clientAddressSchema>;

export const clientSchema = z.object({
    id: z.string().uuid(),
    firstName: z.string().min(1, "Le prénom est requis"),
    lastName: z.string().min(1, "Le nom est requis"),
    email: z.string().email("Format email invalide"),
    phone: z.string().min(1, "Le téléphone est requis"),
    address: clientAddressSchema,
    notes: z.string().optional(),
});
export type Client = z.infer<typeof clientSchema>;

export const clientFormDataSchema = z.object({
    firstName: z.string().min(1, "Le prénom est requis"),
    lastName: z.string().min(1, "Le nom est requis"),
    email: z.string().email("Format email invalide"),
    phone: z.string().min(1, "Le téléphone est requis"),
    addressLine1: z.string().min(1, "L'adresse est requise"),
    addressLine2: z.string().optional().default(""),
    city: z.string().min(1, "La ville est requise"),
    postalCode: z.string().min(1, "Le code postal est requis"),
    country: z.string().min(1, "Le pays est requis"),
    notes: z.string().optional().default(""),
});
export type ClientFormData = z.infer<typeof clientFormDataSchema>;

// ============= MEETING SCHEMAS =============

export const meetingSchema = z.object({
    id: z.number(),
    title: z.string(),
    description: z.string(),
    status: MeetingStatusEnum,
    date: z.string().datetime().optional(),
    notes: z.string().optional(),
});
export type Meeting = z.infer<typeof meetingSchema>;

export const updateMeetingSchema = meetingSchema.partial().omit({ id: true });
export type UpdateMeetingRequest = z.infer<typeof updateMeetingSchema>;

// ============= TASK SCHEMAS =============

export const taskSchema = z.object({
    id: z.string(),
    title: z.string().min(1, "Le titre est requis"),
    category: TaskCategoryEnum,
    status: TaskStatusEnum,
    priority: TaskPriorityEnum,
    blocked: z.boolean(),
    dueDate: z.string().datetime().optional(),
});
export type Task = z.infer<typeof taskSchema>;

export const createTaskSchema = taskSchema.omit({ id: true });
export type CreateTaskRequest = z.infer<typeof createTaskSchema>;

export const updateTaskSchema = taskSchema.partial().omit({ id: true });
export type UpdateTaskRequest = z.infer<typeof updateTaskSchema>;

// ============= PORTFOLIO DATA SCHEMAS =============

export const performanceRowSchema = z.object({
    id: z.string(),
    date: z.string(),
    value: z.number(),
});
export type PerformanceRow = z.infer<typeof performanceRowSchema>;

export const navCashflowRowSchema = z.object({
    id: z.string(),
    date: z.string(),
    type: CashflowTypeEnum,
    value: z.number(),
});
export type NavCashflowRow = z.infer<typeof navCashflowRowSchema>;

export const transactionRowSchema = z.object({
    id: z.string(),
    asset: z.string(),
    quantity: z.number(),
    price: z.number(),
    fee: z.number(),
    total: z.number(),
});
export type TransactionRow = z.infer<typeof transactionRowSchema>;

export const datasetSchema = <T extends z.ZodTypeAny>(rowSchema: T) =>
    z.object({
        status: DataStatusEnum,
        rows: z.array(rowSchema),
        source: DataSourceEnum.optional(),
        importedAt: z.string().datetime().optional(),
        fileName: z.string().optional(),
    });

export const bankPortfolioDataSchema = z.object({
    performance: datasetSchema(performanceRowSchema),
    navCashflows: datasetSchema(navCashflowRowSchema),
    transactions: datasetSchema(transactionRowSchema),
});
export type BankPortfolioData = z.infer<typeof bankPortfolioDataSchema>;

export const portfolioDataSchema = z.record(z.string(), bankPortfolioDataSchema);
export type PortfolioData = z.infer<typeof portfolioDataSchema>;

// ============= ASSET ALLOCATION SCHEMAS =============

export const assetAllocationSchema = z.object({
    type: z.string().min(1, "Le type d'actif est requis"),
    percentage: z.number().min(0).max(100),
});
export type AssetAllocation = z.infer<typeof assetAllocationSchema>;

// ============= BANK CONNECTION SCHEMAS =============

export const bankConnectionSchema = z.object({
    name: z.string().min(1, "Le nom de la banque est requis"),
    connectionMethod: z.string().min(1, "La méthode de connexion est requise"),
});
export type BankConnection = z.infer<typeof bankConnectionSchema>;

// ============= ACTIVITY LOG SCHEMAS =============

export const activityLogEntrySchema = z.object({
    id: z.string(),
    timestamp: z.string().datetime(),
    author: z.string(),
    type: ActivityTypeEnum,
    message: z.string(),
});
export type ActivityLogEntry = z.infer<typeof activityLogEntrySchema>;

export const addActivityLogSchema = activityLogEntrySchema.omit({ id: true, timestamp: true });
export type AddActivityLogRequest = z.infer<typeof addActivityLogSchema>;

// ============= ONBOARDING SCHEMAS =============

export const onboardingSchema = z.object({
    id: z.string().uuid(),
    client: clientSchema,
    assetAllocation: z.array(assetAllocationSchema),
    banks: z.array(bankConnectionSchema),
    createdAt: z.string().datetime(),
    targetEndAt: z.string().datetime(),
    owner: z.string(),
    meetings: z.array(meetingSchema),
    tasks: z.array(taskSchema),
    portfolioData: portfolioDataSchema,
    activityLog: z.array(activityLogEntrySchema),
});
export type Onboarding = z.infer<typeof onboardingSchema>;

export const createOnboardingSchema = z.object({
    client: clientSchema.omit({ id: true }),
    assetAllocation: z.array(assetAllocationSchema),
    banks: z.array(bankConnectionSchema),
    owner: z.string(),
    targetDays: z.number().positive(),
});
export type CreateOnboardingRequest = z.infer<typeof createOnboardingSchema>;

export const updateOnboardingSchema = onboardingSchema.partial().omit({ id: true, createdAt: true });
export type UpdateOnboardingRequest = z.infer<typeof updateOnboardingSchema>;

// ============= FILTER/SORT SCHEMAS =============

export const onboardingFiltersSchema = z.object({
    status: OnboardingStatusEnum.optional(),
    sortBy: SortOptionEnum.optional(),
});
export type OnboardingFilters = z.infer<typeof onboardingFiltersSchema>;

// ============= PAGINATION SCHEMAS =============

export const onboardingListParamsSchema = paginationParamsSchema.extend({
    status: OnboardingStatusEnum.optional(),
    search: z.string().optional(),
});
export type OnboardingListParams = z.infer<typeof onboardingListParamsSchema>;

// ============= API RESPONSE SCHEMAS =============

export const onboardingListResponseSchema = z.object({
    data: z.array(onboardingSchema),
    meta: paginationMetaSchema,
});
export type OnboardingListResponse = z.infer<typeof onboardingListResponseSchema>;

export const onboardingResponseSchema = z.object({
    onboarding: onboardingSchema,
});
export type OnboardingResponse = z.infer<typeof onboardingResponseSchema>;

export const onboardingMessageResponseSchema = z.object({
    message: z.string(),
});
export type OnboardingMessageResponse = z.infer<typeof onboardingMessageResponseSchema>;

// ============= RE-EXPORT ENUMS =============
export {
    MeetingStatusEnum,
    TaskCategoryEnum,
    TaskStatusEnum,
    TaskPriorityEnum,
    DataStatusEnum,
    DataSourceEnum,
    CashflowTypeEnum,
    ActivityTypeEnum,
    OnboardingStatusEnum,
    SortOptionEnum,
};
export type {
    MeetingStatus,
    TaskCategory,
    TaskStatus,
    TaskPriority,
    DataStatus,
    DataSource,
    CashflowType,
    ActivityType,
    OnboardingStatus,
    SortOption,
} from "../../enums";
