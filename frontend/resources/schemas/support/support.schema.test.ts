import { describe, it, expect } from "vitest";
import {
    ticketClientSchema,
    supportTicketSchema,
    createTicketSchema,
    updateTicketStatusSchema,
    assignTicketSchema,
    resolveTicketSchema,
    updatePrioritySchema,
    ticketFiltersSchema,
} from "./support.schema";

describe("ticketClientSchema", () => {
    it("validates correct client", () => {
        const result = ticketClientSchema.safeParse({
            id: "client-1",
            name: "Jean Dupont",
            email: "jean@example.com",
            company: "Acme Corp",
        });
        expect(result.success).toBe(true);
    });

    it("accepts client without company", () => {
        const result = ticketClientSchema.safeParse({
            id: "client-1",
            name: "Jean Dupont",
            email: "jean@example.com",
        });
        expect(result.success).toBe(true);
    });

    it("rejects invalid email", () => {
        const result = ticketClientSchema.safeParse({
            id: "client-1",
            name: "Jean Dupont",
            email: "invalid",
        });
        expect(result.success).toBe(false);
    });
});

describe("createTicketSchema", () => {
    it("validates correct create request", () => {
        const result = createTicketSchema.safeParse({
            client: {
                name: "Jean Dupont",
                email: "jean@example.com",
            },
            issueType: "bug",
            comment: "Something is broken",
            pageUrl: "/dashboard",
        });
        expect(result.success).toBe(true);
    });

    it("applies default priority", () => {
        const result = createTicketSchema.safeParse({
            client: {
                name: "Jean Dupont",
                email: "jean@example.com",
            },
            issueType: "bug",
            comment: "Something is broken",
            pageUrl: "/dashboard",
        });
        expect(result.success).toBe(true);
        if (result.success) {
            expect(result.data.priority).toBe("medium");
        }
    });

    it("rejects invalid issue type", () => {
        const result = createTicketSchema.safeParse({
            client: {
                name: "Jean Dupont",
                email: "jean@example.com",
            },
            issueType: "invalid_type",
            comment: "Something is broken",
            pageUrl: "/dashboard",
        });
        expect(result.success).toBe(false);
    });

    it("rejects empty comment", () => {
        const result = createTicketSchema.safeParse({
            client: {
                name: "Jean Dupont",
                email: "jean@example.com",
            },
            issueType: "bug",
            comment: "",
            pageUrl: "/dashboard",
        });
        expect(result.success).toBe(false);
    });
});

describe("updateTicketStatusSchema", () => {
    it("validates correct status update", () => {
        const result = updateTicketStatusSchema.safeParse({
            status: "in_progress",
            message: "Working on it",
        });
        expect(result.success).toBe(true);
    });

    it("allows update without message", () => {
        const result = updateTicketStatusSchema.safeParse({
            status: "resolved",
        });
        expect(result.success).toBe(true);
    });

    it("rejects invalid status", () => {
        const result = updateTicketStatusSchema.safeParse({
            status: "invalid_status",
        });
        expect(result.success).toBe(false);
    });
});

describe("assignTicketSchema", () => {
    it("validates partial assignment", () => {
        const result = assignTicketSchema.safeParse({
            support: "Alice Martin",
        });
        expect(result.success).toBe(true);
    });

    it("validates full assignment", () => {
        const result = assignTicketSchema.safeParse({
            support: "Alice Martin",
            tech: "Bob Tech",
            csm: "Carol CSM",
        });
        expect(result.success).toBe(true);
    });

    it("accepts empty assignment", () => {
        const result = assignTicketSchema.safeParse({});
        expect(result.success).toBe(true);
    });
});

describe("resolveTicketSchema", () => {
    it("validates correct resolution", () => {
        const result = resolveTicketSchema.safeParse({
            resolutionMessage: "Fixed the issue by updating the config",
            notifyClient: true,
        });
        expect(result.success).toBe(true);
    });

    it("applies default notifyClient", () => {
        const result = resolveTicketSchema.safeParse({
            resolutionMessage: "Fixed the issue",
        });
        expect(result.success).toBe(true);
        if (result.success) {
            expect(result.data.notifyClient).toBe(true);
        }
    });

    it("rejects empty resolution message", () => {
        const result = resolveTicketSchema.safeParse({
            resolutionMessage: "",
            notifyClient: true,
        });
        expect(result.success).toBe(false);
    });
});

describe("updatePrioritySchema", () => {
    it("validates correct priority", () => {
        const result = updatePrioritySchema.safeParse({
            priority: "critical",
        });
        expect(result.success).toBe(true);
    });

    it("rejects invalid priority", () => {
        const result = updatePrioritySchema.safeParse({
            priority: "urgent",
        });
        expect(result.success).toBe(false);
    });
});

describe("ticketFiltersSchema", () => {
    it("validates empty filters", () => {
        const result = ticketFiltersSchema.safeParse({});
        expect(result.success).toBe(true);
    });

    it("validates status filter", () => {
        const result = ticketFiltersSchema.safeParse({
            status: ["open", "in_progress"],
        });
        expect(result.success).toBe(true);
    });

    it("validates priority filter", () => {
        const result = ticketFiltersSchema.safeParse({
            priority: ["high", "critical"],
        });
        expect(result.success).toBe(true);
    });

    it("validates team filter", () => {
        const result = ticketFiltersSchema.safeParse({
            assignedTeam: ["support", "tech"],
        });
        expect(result.success).toBe(true);
    });

    it("rejects invalid status values", () => {
        const result = ticketFiltersSchema.safeParse({
            status: ["invalid"],
        });
        expect(result.success).toBe(false);
    });
});
