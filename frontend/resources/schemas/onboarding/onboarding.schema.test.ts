import { describe, it, expect } from "vitest";
import {
    clientSchema,
    clientFormDataSchema,
    meetingSchema,
    taskSchema,
    createOnboardingSchema,
    assetAllocationSchema,
    bankConnectionSchema,
} from "./onboarding.schema";

describe("clientSchema", () => {
    it("validates correct client data", () => {
        const result = clientSchema.safeParse({
            id: "550e8400-e29b-41d4-a716-446655440000",
            firstName: "Jean",
            lastName: "Dupont",
            email: "jean.dupont@example.com",
            phone: "+33612345678",
            address: {
                line1: "123 Rue de Paris",
                city: "Paris",
                postalCode: "75001",
                country: "France",
            },
        });
        expect(result.success).toBe(true);
    });

    it("rejects missing required fields", () => {
        const result = clientSchema.safeParse({
            id: "550e8400-e29b-41d4-a716-446655440000",
            firstName: "Jean",
            // missing lastName, email, phone, address
        });
        expect(result.success).toBe(false);
    });

    it("rejects invalid email", () => {
        const result = clientSchema.safeParse({
            id: "550e8400-e29b-41d4-a716-446655440000",
            firstName: "Jean",
            lastName: "Dupont",
            email: "invalid",
            phone: "+33612345678",
            address: {
                line1: "123 Rue de Paris",
                city: "Paris",
                postalCode: "75001",
                country: "France",
            },
        });
        expect(result.success).toBe(false);
    });
});

describe("clientFormDataSchema", () => {
    it("validates correct form data", () => {
        const result = clientFormDataSchema.safeParse({
            firstName: "Jean",
            lastName: "Dupont",
            email: "jean.dupont@example.com",
            phone: "+33612345678",
            addressLine1: "123 Rue de Paris",
            city: "Paris",
            postalCode: "75001",
            country: "France",
        });
        expect(result.success).toBe(true);
    });
});

describe("meetingSchema", () => {
    it("validates correct meeting", () => {
        const result = meetingSchema.safeParse({
            id: 1,
            title: "Discovery call",
            description: "Initial meeting",
            status: "scheduled",
            date: "2025-02-15T10:00:00.000Z",
        });
        expect(result.success).toBe(true);
    });

    it("rejects invalid status", () => {
        const result = meetingSchema.safeParse({
            id: 1,
            title: "Discovery call",
            description: "Initial meeting",
            status: "invalid_status",
        });
        expect(result.success).toBe(false);
    });
});

describe("taskSchema", () => {
    it("validates correct task", () => {
        const result = taskSchema.safeParse({
            id: "task-1",
            title: "Send welcome email",
            category: "CSM",
            status: "todo",
            priority: "high",
            blocked: false,
        });
        expect(result.success).toBe(true);
    });

    it("rejects invalid category", () => {
        const result = taskSchema.safeParse({
            id: "task-1",
            title: "Send welcome email",
            category: "Invalid",
            status: "todo",
            priority: "high",
            blocked: false,
        });
        expect(result.success).toBe(false);
    });

    it("rejects invalid status", () => {
        const result = taskSchema.safeParse({
            id: "task-1",
            title: "Send welcome email",
            category: "CSM",
            status: "invalid",
            priority: "high",
            blocked: false,
        });
        expect(result.success).toBe(false);
    });
});

describe("assetAllocationSchema", () => {
    it("validates correct allocation", () => {
        const result = assetAllocationSchema.safeParse({
            type: "Public Equities",
            percentage: 40,
        });
        expect(result.success).toBe(true);
    });

    it("rejects percentage over 100", () => {
        const result = assetAllocationSchema.safeParse({
            type: "Public Equities",
            percentage: 150,
        });
        expect(result.success).toBe(false);
    });

    it("rejects negative percentage", () => {
        const result = assetAllocationSchema.safeParse({
            type: "Public Equities",
            percentage: -10,
        });
        expect(result.success).toBe(false);
    });
});

describe("bankConnectionSchema", () => {
    it("validates correct bank connection", () => {
        const result = bankConnectionSchema.safeParse({
            name: "BNP Paribas",
            connectionMethod: "API",
        });
        expect(result.success).toBe(true);
    });

    it("rejects empty name", () => {
        const result = bankConnectionSchema.safeParse({
            name: "",
            connectionMethod: "API",
        });
        expect(result.success).toBe(false);
    });
});

describe("createOnboardingSchema", () => {
    it("validates correct create request", () => {
        const result = createOnboardingSchema.safeParse({
            client: {
                firstName: "Jean",
                lastName: "Dupont",
                email: "jean.dupont@example.com",
                phone: "+33612345678",
                address: {
                    line1: "123 Rue de Paris",
                    city: "Paris",
                    postalCode: "75001",
                    country: "France",
                },
            },
            assetAllocation: [
                { type: "Public Equities", percentage: 60 },
                { type: "Fixed Income", percentage: 40 },
            ],
            banks: [{ name: "BNP Paribas", connectionMethod: "API" }],
            owner: "CSM Team",
            targetDays: 90,
        });
        expect(result.success).toBe(true);
    });

    it("rejects negative targetDays", () => {
        const result = createOnboardingSchema.safeParse({
            client: {
                firstName: "Jean",
                lastName: "Dupont",
                email: "jean.dupont@example.com",
                phone: "+33612345678",
                address: {
                    line1: "123 Rue de Paris",
                    city: "Paris",
                    postalCode: "75001",
                    country: "France",
                },
            },
            assetAllocation: [],
            banks: [],
            owner: "CSM Team",
            targetDays: -10,
        });
        expect(result.success).toBe(false);
    });
});
