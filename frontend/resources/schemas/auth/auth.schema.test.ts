import { describe, it, expect } from "vitest";
import {
    loginRequestSchema,
    registerRequestSchema,
    resetPasswordRequestSchema,
    verifyOtpRequestSchema,
} from "./auth.schema";

describe("loginRequestSchema", () => {
    it("validates correct data", () => {
        const result = loginRequestSchema.safeParse({
            email: "john@example.com",
            password: "password123",
        });
        expect(result.success).toBe(true);
    });

    it("rejects invalid email", () => {
        const result = loginRequestSchema.safeParse({
            email: "invalid",
            password: "password123",
        });
        expect(result.success).toBe(false);
    });

    it("rejects empty password", () => {
        const result = loginRequestSchema.safeParse({
            email: "john@example.com",
            password: "",
        });
        expect(result.success).toBe(false);
    });
});

describe("registerRequestSchema", () => {
    it("validates correct data", () => {
        const result = registerRequestSchema.safeParse({
            email: "john@example.com",
            password: "password123",
        });
        expect(result.success).toBe(true);
    });

    it("rejects invalid email", () => {
        const result = registerRequestSchema.safeParse({
            email: "invalid",
            password: "password123",
        });
        expect(result.success).toBe(false);
    });

    it("rejects short password", () => {
        const result = registerRequestSchema.safeParse({
            email: "john@example.com",
            password: "12345",
        });
        expect(result.success).toBe(false);
    });
});

describe("resetPasswordRequestSchema", () => {
    it("validates correct data", () => {
        const result = resetPasswordRequestSchema.safeParse({
            email: "john@example.com",
        });
        expect(result.success).toBe(true);
    });

    it("rejects invalid email", () => {
        const result = resetPasswordRequestSchema.safeParse({
            email: "invalid",
        });
        expect(result.success).toBe(false);
    });
});

describe("verifyOtpRequestSchema", () => {
    it("validates correct 6-digit OTP", () => {
        const result = verifyOtpRequestSchema.safeParse({
            otp: "123456",
        });
        expect(result.success).toBe(true);
    });

    it("rejects OTP with wrong length", () => {
        const result = verifyOtpRequestSchema.safeParse({
            otp: "12345",
        });
        expect(result.success).toBe(false);
    });

    it("rejects OTP with 7 digits", () => {
        const result = verifyOtpRequestSchema.safeParse({
            otp: "1234567",
        });
        expect(result.success).toBe(false);
    });
});
