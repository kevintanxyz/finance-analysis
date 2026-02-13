# Frontend Conventions & Lovable Generation Prompt

> **CONTEXTE IMPORTANT**
>
> Ce frontend sera généré avec **Lovable** (basé sur Supabase) puis migré vers un **backend custom Node.js/NestJS**.
>
> **Workflow de développement:**
> 1. Générer le frontend avec Lovable/Supabase
> 2. Documenter TOUTES les modifications backend dans `BackendChanges.md`
> 3. Créer les schemas Zod partagés dans le dossier `resources/`
> 4. Migrer les appels Supabase vers le backend custom

---

## PROMPT LOVABLE - NOUVELLES FEATURES

```
Tu es un développeur frontend expert. Tu génères une application React avec les conventions suivantes.

## CONTEXTE CRITIQUE - MIGRATION SUPABASE → BACKEND CUSTOM

⚠️ CE FRONTEND SERA MIGRÉ D'UN BACKEND SUPABASE VERS UN BACKEND CUSTOM (Node.js/NestJS) ⚠️

### 0. ARCHITECTURE API - EDGE FUNCTIONS + REACT QUERY

**RÈGLE FONDAMENTALE**: JAMAIS d'appels directs à Supabase dans les composants.

**Architecture obligatoire:**
```
Composant → React Query Hook → Edge Function Supabase → Base de données
```

**Migration — on change UNIQUEMENT l'appel dans le hook:**
```typescript
// AVANT: supabase.functions.invoke("get-users")
// APRÈS: apiClient.get("/users")
```

**Structure Edge Functions:** `supabase/functions/[action-name]/index.ts`

**EXCEPTION AuthContext:** `supabase.auth.*` autorisé UNIQUEMENT dans `AuthContext.tsx` (onAuthStateChange, getSession, signIn, signUp, signOut).

**INTERDIT:**
```typescript
// ❌ JAMAIS dans un composant
const { data } = await supabase.from("users").select("*");
// ✅ TOUJOURS via hook React Query
const { data } = useUsers();
```

### 1. API CLIENT ABSTRAIT

Créer un API client centralisé (`src/lib/api.ts`) qui switch automatiquement entre Supabase et backend custom via `VITE_API_BASE_URL`:

```typescript
// src/lib/api.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
const USE_CUSTOM_BACKEND = !!API_BASE_URL;

export const apiClient = {
    async get<T>(endpoint: string): Promise<T> {
        if (USE_CUSTOM_BACKEND) {
            const token = await getAuthToken();
            const res = await fetch(`${API_BASE_URL}${endpoint}`, {
                headers: { "Content-Type": "application/json", ...(token && { Authorization: `Bearer ${token}` }) },
            });
            if (!res.ok) throw new Error(await res.text());
            return res.json();
        }
        const functionName = endpoint.replace("/api/", "").replace(/\//g, "-");
        const { data, error } = await supabase.functions.invoke(functionName);
        if (error) throw new Error(error.message);
        return data;
    },
    // post, patch, delete suivent le même pattern
};
```

### 2. DOCUMENTATION OBLIGATOIRE - BackendChanges.md

À CHAQUE feature nécessitant un backend, mettre à jour `BackendChanges.md`:
- Edge Functions créées (nom, méthode, description, hook React Query associé)
- Routes API backend pour migration (méthode, path)
- Schemas Zod créés dans `resources/schemas/`
- Logique backend

### 3. SCHEMAS PARTAGÉS - Dossier resources/

Tous les types/validateurs dans `resources/` (partagé frontend/backend):

```
resources/
├── schemas/
│   ├── common/api.schema.ts          # Pagination, erreurs, réponses
│   └── [domain]/[domain].schema.ts
├── enums/
│   └── [name].enum.ts
└── index.ts
```

### 4. SCHEMAS COMMUNS OBLIGATOIRES

```typescript
// resources/schemas/common/api.schema.ts
export const paginationParamsSchema = z.object({
    page: z.number().int().positive().default(1),
    limit: z.number().int().positive().max(100).default(20),
    sortBy: z.string().optional(),
    sortOrder: z.enum(["asc", "desc"]).default("desc"),
});

export const paginationMetaSchema = z.object({
    page: z.number(), limit: z.number(), total: z.number(),
    totalPages: z.number(), hasMore: z.boolean(),
});

export const paginatedResponseSchema = <T extends z.ZodTypeAny>(itemSchema: T) =>
    z.object({ data: z.array(itemSchema), meta: paginationMetaSchema });

export const apiErrorSchema = z.object({
    error: z.string(), message: z.string(), statusCode: z.number(),
    details: z.record(z.string(), z.array(z.string())).optional(),
});
```

### 5. PATTERN SCHEMA avec Zod

Un seul fichier par domaine, avec enums, request schemas et response schemas:

```typescript
// resources/schemas/[domain]/[domain].schema.ts
import { z } from "zod";

// Enums
export const UserRoleEnum = z.enum(["admin", "user", "guest"]);

// Request
export const createUserSchema = z.object({
    firstName: z.string().min(2),
    email: z.string().email("Format email invalide"),
});
export type CreateUserRequest = z.infer<typeof createUserSchema>;

// Response
export const userSchema = z.object({
    id: z.string().uuid(),
    firstName: z.string(),
    email: z.string().email(),
    role: UserRoleEnum,
    createdAt: z.string().datetime(),
});
export type User = z.infer<typeof userSchema>;
```

## STACK TECHNIQUE

- **Framework**: React 19+ avec TypeScript 5.8+ (mode strict)
- **Build**: Vite
- **State serveur**: TanStack React Query v5
- **Routing**: React Router DOM v6
- **Validation**: Zod + React Hook Form (@hookform/resolvers/zod)
- **Animations**: Framer Motion

## STRUCTURE DES DOSSIERS

```
projet/
├── src/
│   ├── components/
│   │   ├── ui/
│   │   ├── auth/                  # AuthCard, AuthLayout, ProtectedRoute
│   │   ├── layout/                # AppLayout, GlobalSidebar, PageHeader
│   │   └── [feature]/             # Par domaine métier
│   ├── contexts/                  # AuthContext, ThemeContext
│   ├── hooks/
│   │   ├── use-toast.ts
│   │   ├── use-mobile.tsx
│   │   └── queries/               # ⚠️ TOUS les appels API ici (use[Domain].ts)
│   ├── mocks/                     # ⚠️ DONNÉES MOCK/DEMO (JSON uniquement)
│   │   └── [domain].mock.json
│   ├── pages/
│   ├── utils/                     # cn.ts, formatters.ts
│   ├── lib/                       # api.ts, supabase.ts, queryClient.ts
│   ├── App.tsx, Routing.tsx, main.tsx
├── supabase/functions/[action-name]/index.ts
├── resources/schemas/             # ⚠️ SCHEMAS PARTAGÉS
├── BackendChanges.md              # ⚠️ LOG MODIFICATIONS BACKEND
└── .env.example
```

## VARIABLES D'ENVIRONNEMENT

```bash
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=eyJxxx
# Décommenter lors de la migration:
# VITE_API_BASE_URL=http://localhost:3000
```

## CONVENTIONS DE NOMMAGE

| Type | Convention | Exemple |
|------|------------|---------|
| Composants/Pages | PascalCase | `UserProfile.tsx` |
| Hooks | camelCase + "use" | `useAuth.ts` |
| Schemas | camelCase + "Schema" | `loginRequestSchema` |
| Types (inférés) | PascalCase | `LoginRequest` |
| Enums Zod | PascalCase + "Enum" | `CurrencyEnum` |
| Fichiers schemas | kebab-case | `auth.schema.ts` |
| Query Keys | camelCase + "Keys" | `userKeys` |

## FORMATAGE CODE

```javascript
// prettier.config.js
module.exports = {
    overrides: [{
        files: ["./*.ts", "./*.tsx", "./*.json", "src/**/*.ts", "src/**/*.tsx", "src/**/*.scss", "./*.js"],
        options: { tabWidth: 4, useTabs: true, singleQuote: false, trailingComma: "all", printWidth: 180, semi: true, bracketSameLine: true },
    }],
};
```

## PATTERNS À SUIVRE

### Pattern Hook React Query (OBLIGATOIRE)

Chaque fichier hook DOIT exporter ses query keys + queries + mutations:

```typescript
// hooks/queries/useUsers.ts

// ============= QUERY KEYS =============
export const userKeys = {
    all: ["users"] as const,
    list: () => [...userKeys.all, "list"] as const,
    listWithParams: (params: UserListParams) => [...userKeys.list(), params] as const,
    detail: (id: string) => [...userKeys.all, "detail", id] as const,
};

// ============= QUERIES =============
export function useUsersList(params?: UserListParams) {
    return useQuery({
        queryKey: userKeys.listWithParams(params ?? {}),
        queryFn: async (): Promise<UserListResponse> => {
            const data = await apiClient.get(`/api/users?${new URLSearchParams(params as any)}`);
            return userListResponseSchema.parse(data);
        },
    });
}

// ============= MUTATIONS =============
export function useCreateUser() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (input: CreateUserRequest): Promise<User> => {
            const validated = createUserSchema.parse(input);
            const data = await apiClient.post("/api/users", validated);
            return userSchema.parse(data);
        },
        onSuccess: () => queryClient.invalidateQueries({ queryKey: userKeys.all }),
    });
}
```

### Pattern Error Handling

```typescript
const { data, error } = await supabase.functions.invoke("...");
if (error) throw new Error(error.message);
if (data?.error) throw new Error(data.error);
return schema.parse(data);
```

### RÈGLE CRITIQUE - Composants et données serveur

⚠️ **AUCUN composant ne doit avoir de données hardcodées ou d'état local pour les données serveur**

**INTERDIT:** `useState` avec données hardcodées, `setSavedData(formData)` sans appel API.

**OBLIGATOIRE pour chaque composant qui affiche/modifie des données:**
- Données chargées via `useQuery` hook → Loading state (Skeleton) + Error state
- Modifications via `useMutation` hook → Toast succès/erreur
- Formulaire: `useForm` avec `values: serverData` (pas `defaultValues`) pour sync serveur
- Validation Zod via `zodResolver`

```typescript
// Pattern résumé
const { data, isLoading, isError } = useProfile();
const mutation = useUpdateProfile();
const form = useForm({ resolver: zodResolver(schema), values: data });
const onSubmit = (d) => mutation.mutate(d, {
    onSuccess: () => toast({ title: "Mis à jour" }),
    onError: (e) => toast({ title: "Erreur", description: e.message, variant: "destructive" }),
});
```

### RÈGLE - Données Mock/Demo (PAS sur Supabase)

⚠️ **Les données mock/demo DOIVENT être dans des fichiers JSON séparés. Ne JAMAIS insérer dans Supabase ou hardcoder dans les composants.**

**Convention:** `src/mocks/[domain].mock.json`

```typescript
// ❌ await supabase.from("users").insert([...]); ou const mockUsers = [...]
// ✅ import usersMock from "@/mocks/users.mock.json";
```

### Pattern Réponse paginée

Toutes les listes DOIVENT utiliser le format `{ data: T[], meta: PaginationMeta }`:

```typescript
// Schema: paginatedResponseSchema(itemSchema)
// Hook: useQuery + queryFn → schema.parse(data)
// Composant: <Table data={data?.data ?? []} /> + <Pagination meta={data?.meta} />
```

### Pattern ProtectedRoute

```typescript
// src/components/auth/ProtectedRoute.tsx
// Props: { children, requireOtp?: boolean }
// Vérifie: loading → spinner, !user → /login, requireOtp && !isOtpVerified → /verify-otp
```

### Pattern Toast

```typescript
toast({ title: "Succès" }); // Succès
toast({ title: "Erreur", description: err.message, variant: "destructive" }); // Erreur
```

### Pattern File Upload

```typescript
// hooks/queries/useUploadFile.ts — useMutation qui upload vers Supabase Storage
// MIGRATION: Remplacer par apiClient.post("/api/upload", formData)
```

### Pattern Storybook (optionnel)

Config: `.storybook/main.ts` (aliases Vite `@/` et `resources/`) + `preview.ts` (import `index.css`).
Stories: `src/components/[feature]/[Component].stories.tsx` avec Meta + StoryObj pattern.

## PROCESSUS DE DÉVELOPPEMENT

### Étape 1: Créer la feature (Lovable)
1. Schemas Zod dans `resources/schemas/[domain]/` (pagination si liste)
2. Edge Function dans `supabase/functions/[action-name]/`
3. Hook React Query dans `src/hooks/queries/` (avec `apiClient` + query keys)
4. Composants UI
5. Documenter dans `BackendChanges.md`

### Étape 2: Migration (Backend custom)
1. Lire `BackendChanges.md`
2. Créer routes ExpressJS avec mêmes Schemas Zod
3. Définir `VITE_API_BASE_URL` dans `.env`
4. Les hooks switchent automatiquement via `apiClient`

## TESTS

Tests schemas Zod obligatoires (`vitest`): valider données correctes, rejeter données invalides.

```typescript
describe("schema", () => {
    it("validates correct data", () => expect(schema.safeParse(validData).success).toBe(true));
    it("rejects invalid data", () => expect(schema.safeParse(invalidData).success).toBe(false));
});
```
```
