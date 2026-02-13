import { z } from "zod";

// Schema for editing Min/Max allocation with cross-field validation
export const editAssetClassSchema = z.object({
    minAllocation: z
        .number()
        .min(0, "Minimum allocation must be at least 0%")
        .max(100, "Minimum allocation cannot exceed 100%"),
    maxAllocation: z
        .number()
        .min(0, "Maximum allocation must be at least 0%")
        .max(100, "Maximum allocation cannot exceed 100%"),
}).refine(
    (data) => data.minAllocation <= data.maxAllocation,
    {
        message: "Minimum allocation cannot be greater than maximum allocation",
        path: ["minAllocation"],
    }
);

export type EditAssetClassFormData = z.infer<typeof editAssetClassSchema>;
