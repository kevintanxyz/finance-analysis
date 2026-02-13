import { z } from "zod";

// === ENUMS ===

export const UserStateEnum = z.enum([
	"created",
	"email_pending",
	"password_pending",
	"active",
	"2fa_required",
	"locked",
	"suspended",
	"deleted",
]);
export type UserState = z.infer<typeof UserStateEnum>;

export const AppRoleEnum = z.enum(["admin", "client", "relationship_manager", "support", "compliance"]);
export type AppRole = z.infer<typeof AppRoleEnum>;

// === REQUEST SCHEMAS ===

export const loginRequestSchema = z.object({
	email: z.string().email("Format email invalide"),
	password: z.string().min(1, "Le mot de passe est requis"),
});
export type LoginRequest = z.infer<typeof loginRequestSchema>;

export const registerRequestSchema = z.object({
	email: z.string().email("Format email invalide"),
	password: z.string().min(8, "Minimum 8 caractères"),
});
export type RegisterRequest = z.infer<typeof registerRequestSchema>;

export const resetPasswordRequestSchema = z.object({
	email: z.string().email("Format email invalide"),
});
export type ResetPasswordRequest = z.infer<typeof resetPasswordRequestSchema>;

export const verifyOtpRequestSchema = z.object({
	otp: z.string().length(6, "Le code doit contenir 6 chiffres"),
});
export type VerifyOtpRequest = z.infer<typeof verifyOtpRequestSchema>;

export const setupMfaRequestSchema = z.object({
	action: z.enum(["generate", "verify", "disable"]),
	token: z.string().optional(),
});
export type SetupMfaRequest = z.infer<typeof setupMfaRequestSchema>;

export const magicLinkRequestSchema = z.object({
	email: z.string().email("Format email invalide"),
});
export type MagicLinkRequest = z.infer<typeof magicLinkRequestSchema>;

export const passwordStrengthSchema = z.object({
	password: z
		.string()
		.min(8, "Minimum 8 caractères")
		.regex(/[A-Z]/, "Au moins une majuscule")
		.regex(/[a-z]/, "Au moins une minuscule")
		.regex(/[0-9]/, "Au moins un chiffre")
		.regex(/[^A-Za-z0-9]/, "Au moins un caractère spécial"),
});
export type PasswordStrength = z.infer<typeof passwordStrengthSchema>;

// === RESPONSE SCHEMAS ===

export const userSchema = z.object({
	id: z.string().uuid(),
	email: z.string().email().nullable(),
	created_at: z.string().datetime().optional(),
});
export type User = z.infer<typeof userSchema>;

export const authProfileSchema = z.object({
	id: z.string().uuid(),
	user_id: z.string().uuid(),
	email: z.string().nullable(),
	display_name: z.string().nullable(),
	phone: z.string().nullable(),
	avatar_url: z.string().nullable(),
	user_state: UserStateEnum,
	mfa_enabled: z.boolean(),
	last_login_at: z.string().nullable(),
	created_at: z.string(),
	updated_at: z.string(),
});
export type AuthProfile = z.infer<typeof authProfileSchema>;

export const authResponseSchema = z.object({
	user: userSchema.nullable(),
	session: z
		.object({
			access_token: z.string(),
			refresh_token: z.string(),
			expires_in: z.number(),
		})
		.nullable(),
	profile: authProfileSchema.optional(),
});
export type AuthResponse = z.infer<typeof authResponseSchema>;

export const messageResponseSchema = z.object({
	message: z.string(),
});
export type MessageResponse = z.infer<typeof messageResponseSchema>;

export const mfaSetupResponseSchema = z.object({
	qr_code: z.string().optional(),
	secret: z.string().optional(),
	verified: z.boolean().optional(),
	message: z.string().optional(),
});
export type MfaSetupResponse = z.infer<typeof mfaSetupResponseSchema>;

export const deviceSchema = z.object({
	id: z.string().uuid(),
	device_name: z.string().nullable(),
	device_type: z.string().nullable(),
	browser: z.string().nullable(),
	os: z.string().nullable(),
	is_trusted: z.boolean(),
	last_seen_at: z.string(),
	created_at: z.string(),
});
export type Device = z.infer<typeof deviceSchema>;

export const auditLogSchema = z.object({
	id: z.string().uuid(),
	event_type: z.string(),
	ip_address: z.string().nullable(),
	metadata: z.record(z.unknown()).nullable(),
	created_at: z.string(),
});
export type AuditLog = z.infer<typeof auditLogSchema>;
