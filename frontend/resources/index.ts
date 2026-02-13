// ============= RESOURCES EXPORTS =============
// Shared schemas and enums for frontend/backend migration

export * from "./enums";
export * from "./schemas/auth";
export * from "./schemas/onboarding";
export * from "./schemas/support";
export * from "./schemas/settings";

// Common schemas are imported directly by domain schemas
// To use pagination schemas, import from "resources/schemas/common"
