// ============= SHARED ENUMS =============
import { z } from "zod";

// ============= ONBOARDING ENUMS =============
export const MeetingStatusEnum = z.enum(["not_started", "scheduled", "completed", "blocked"]);
export type MeetingStatus = z.infer<typeof MeetingStatusEnum>;

export const TaskCategoryEnum = z.enum(["Tech", "CSM"]);
export type TaskCategory = z.infer<typeof TaskCategoryEnum>;

export const TaskStatusEnum = z.enum(["todo", "in_progress", "done"]);
export type TaskStatus = z.infer<typeof TaskStatusEnum>;

export const TaskPriorityEnum = z.enum(["low", "medium", "high"]);
export type TaskPriority = z.infer<typeof TaskPriorityEnum>;

export const DataStatusEnum = z.enum(["not_added", "draft", "validated"]);
export type DataStatus = z.infer<typeof DataStatusEnum>;

export const DataSourceEnum = z.enum(["manual", "import"]);
export type DataSource = z.infer<typeof DataSourceEnum>;

export const CashflowTypeEnum = z.enum(["NAV", "Inflow", "Outflow"]);
export type CashflowType = z.infer<typeof CashflowTypeEnum>;

export const ActivityTypeEnum = z.enum(["meeting", "task", "note", "data", "status"]);
export type ActivityType = z.infer<typeof ActivityTypeEnum>;

export const OnboardingStatusEnum = z.enum(["in_progress", "blocked", "completed"]);
export type OnboardingStatus = z.infer<typeof OnboardingStatusEnum>;

export const SortOptionEnum = z.enum(["alphabetical", "time_remaining", "created_date"]);
export type SortOption = z.infer<typeof SortOptionEnum>;

// ============= SUPPORT ENUMS =============
export const TicketStatusEnum = z.enum([
    "open",
    "in_progress",
    "waiting_client",
    "escalated",
    "resolved",
    "closed",
]);
export type TicketStatus = z.infer<typeof TicketStatusEnum>;

export const TicketPriorityEnum = z.enum(["low", "medium", "high", "critical"]);
export type TicketPriority = z.infer<typeof TicketPriorityEnum>;

export const IssueTypeEnum = z.enum(["bug", "data_issue", "ui_problem", "performance", "other"]);
export type IssueType = z.infer<typeof IssueTypeEnum>;

export const TicketLogTypeEnum = z.enum([
    "created",
    "assigned",
    "status_change",
    "escalated",
    "note",
    "client_notification",
    "resolved",
]);
export type TicketLogType = z.infer<typeof TicketLogTypeEnum>;

export const AnnotationToolEnum = z.enum(["freehand", "rectangle", "circle", "arrow"]);
export type AnnotationTool = z.infer<typeof AnnotationToolEnum>;

export const TicketSortOptionEnum = z.enum(["priority", "sla", "created_date"]);
export type TicketSortOption = z.infer<typeof TicketSortOptionEnum>;
