import { z } from "zod";
import {
    TicketStatusEnum,
    TicketPriorityEnum,
    IssueTypeEnum,
    TicketLogTypeEnum,
    AnnotationToolEnum,
    TicketSortOptionEnum,
} from "../../enums";
import { paginationParamsSchema, paginationMetaSchema } from "../common/api.schema";

// ============= ANNOTATION SCHEMAS =============

export const annotationPointSchema = z.object({
    x: z.number(),
    y: z.number(),
});
export type AnnotationPoint = z.infer<typeof annotationPointSchema>;

export const annotationSchema = z.object({
    id: z.string(),
    tool: AnnotationToolEnum,
    points: z.array(annotationPointSchema),
    color: z.string(),
    strokeWidth: z.number(),
});
export type Annotation = z.infer<typeof annotationSchema>;

export const screenshotDataSchema = z.object({
    image: z.string(), // base64
    annotations: z.array(annotationSchema),
    width: z.number(),
    height: z.number(),
});
export type ScreenshotData = z.infer<typeof screenshotDataSchema>;

// ============= CLIENT SCHEMAS =============

export const ticketClientSchema = z.object({
    id: z.string(),
    name: z.string().min(1, "Le nom est requis"),
    email: z.string().email("Format email invalide"),
    company: z.string().optional(),
});
export type TicketClient = z.infer<typeof ticketClientSchema>;

// ============= LOG SCHEMAS =============

export const ticketLogEntrySchema = z.object({
    id: z.string(),
    timestamp: z.string().datetime(),
    author: z.string(),
    type: TicketLogTypeEnum,
    message: z.string(),
});
export type TicketLogEntry = z.infer<typeof ticketLogEntrySchema>;

export const addTicketLogSchema = ticketLogEntrySchema.omit({ id: true, timestamp: true });
export type AddTicketLogRequest = z.infer<typeof addTicketLogSchema>;

// ============= TICKET SCHEMAS =============

export const supportTicketSchema = z.object({
    id: z.string(),
    ticketNumber: z.string(),
    client: ticketClientSchema,
    onboardingId: z.string().optional(),
    issueType: IssueTypeEnum,
    subject: z.string(),
    comment: z.string().min(1, "La description est requise"),
    screenshot: screenshotDataSchema.optional(),
    pageUrl: z.string(),
    status: TicketStatusEnum,
    priority: TicketPriorityEnum,
    assignedSupport: z.string().optional(),
    assignedTech: z.string().optional(),
    assignedCSM: z.string().optional(),
    createdAt: z.string().datetime(),
    slaDeadline: z.string().datetime(),
    resolvedAt: z.string().datetime().optional(),
    resolutionMessage: z.string().optional(),
    logs: z.array(ticketLogEntrySchema),
});
export type SupportTicket = z.infer<typeof supportTicketSchema>;

// ============= CREATE TICKET SCHEMAS =============

export const createTicketSchema = z.object({
    client: ticketClientSchema.omit({ id: true }),
    onboardingId: z.string().optional(),
    issueType: IssueTypeEnum,
    comment: z.string().min(1, "La description est requise"),
    screenshot: screenshotDataSchema.optional(),
    pageUrl: z.string(),
    priority: TicketPriorityEnum.optional().default("medium"),
});
export type CreateTicketRequest = z.infer<typeof createTicketSchema>;

// ============= UPDATE TICKET SCHEMAS =============

export const updateTicketStatusSchema = z.object({
    status: TicketStatusEnum,
    message: z.string().optional(),
});
export type UpdateTicketStatusRequest = z.infer<typeof updateTicketStatusSchema>;

export const assignTicketSchema = z.object({
    support: z.string().optional(),
    tech: z.string().optional(),
    csm: z.string().optional(),
});
export type AssignTicketRequest = z.infer<typeof assignTicketSchema>;

export const escalateTicketSchema = z.object({
    techAgent: z.string().min(1, "L'agent tech est requis"),
});
export type EscalateTicketRequest = z.infer<typeof escalateTicketSchema>;

export const resolveTicketSchema = z.object({
    resolutionMessage: z.string().min(1, "Le message de résolution est requis"),
    notifyClient: z.boolean().default(true),
});
export type ResolveTicketRequest = z.infer<typeof resolveTicketSchema>;

export const updatePrioritySchema = z.object({
    priority: TicketPriorityEnum,
});
export type UpdatePriorityRequest = z.infer<typeof updatePrioritySchema>;

// ============= FILTER SCHEMAS =============

export const ticketFiltersSchema = z.object({
    status: z.array(TicketStatusEnum).optional(),
    priority: z.array(TicketPriorityEnum).optional(),
    assignedTeam: z.array(z.enum(["support", "tech", "csm"])).optional(),
});
export type TicketFilters = z.infer<typeof ticketFiltersSchema>;

// ============= FORM DATA SCHEMAS =============

export const ticketFormDataSchema = z.object({
    issueType: IssueTypeEnum,
    comment: z.string().min(1, "La description est requise"),
    email: z.string().email("Format email invalide"),
});
export type TicketFormData = z.infer<typeof ticketFormDataSchema>;

// ============= PAGINATION SCHEMAS =============

export const ticketListParamsSchema = paginationParamsSchema.extend({
    status: z.array(TicketStatusEnum).optional(),
    priority: z.array(TicketPriorityEnum).optional(),
    search: z.string().optional(),
});
export type TicketListParams = z.infer<typeof ticketListParamsSchema>;

// ============= API RESPONSE SCHEMAS =============

export const ticketListResponseSchema = z.object({
    data: z.array(supportTicketSchema),
    meta: paginationMetaSchema,
});
export type TicketListResponse = z.infer<typeof ticketListResponseSchema>;

export const ticketResponseSchema = z.object({
    ticket: supportTicketSchema,
});
export type TicketResponse = z.infer<typeof ticketResponseSchema>;

export const supportMessageResponseSchema = z.object({
    message: z.string(),
});
export type SupportMessageResponse = z.infer<typeof supportMessageResponseSchema>;

// ============= RE-EXPORT ENUMS =============
export {
    TicketStatusEnum,
    TicketPriorityEnum,
    IssueTypeEnum,
    TicketLogTypeEnum,
    AnnotationToolEnum,
    TicketSortOptionEnum,
};
export type {
    TicketStatus,
    TicketPriority,
    IssueType,
    TicketLogType,
    AnnotationTool,
    TicketSortOption,
} from "../../enums";
