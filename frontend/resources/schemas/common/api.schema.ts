import { z } from "zod";

// ============= PAGINATION =============

export const paginationParamsSchema = z.object({
    page: z.number().int().positive().default(1),
    limit: z.number().int().positive().max(100).default(20),
    sortBy: z.string().optional(),
    sortOrder: z.enum(["asc", "desc"]).default("desc"),
});
export type PaginationParams = z.infer<typeof paginationParamsSchema>;

export const paginationMetaSchema = z.object({
    page: z.number(),
    limit: z.number(),
    total: z.number(),
    totalPages: z.number(),
    hasMore: z.boolean(),
});
export type PaginationMeta = z.infer<typeof paginationMetaSchema>;

// Helper pour créer des réponses paginées
export const paginatedResponseSchema = <T extends z.ZodTypeAny>(itemSchema: T) =>
    z.object({
        data: z.array(itemSchema),
        meta: paginationMetaSchema,
    });

// ============= ERREURS API =============

export const apiErrorSchema = z.object({
    error: z.string(),
    message: z.string(),
    statusCode: z.number(),
    details: z.record(z.string(), z.array(z.string())).optional(),
});
export type ApiError = z.infer<typeof apiErrorSchema>;

// ============= RÉPONSES SUCCESS =============

export const messageResponseSchema = z.object({
    message: z.string(),
});
export type MessageResponse = z.infer<typeof messageResponseSchema>;

export const idResponseSchema = z.object({
    id: z.string().uuid(),
});
export type IdResponse = z.infer<typeof idResponseSchema>;
