# 📋 Frontend Development Conventions - React / TypeScript

> **This file is the single source of truth for code review**
>
> Any violation must be flagged by the automated review agent.
> These conventions are framework-agnostic and reusable across projects.

---

## Table of Contents

1. [Security](#-1-security)
2. [TypeScript](#-2-typescript)
3. [Architecture & File Structure](#-3-architecture--file-structure)
4. [React Components](#-4-react-components)
5. [Hooks](#-5-hooks)
6. [State Management](#-6-state-management)
7. [Props & Typing](#-7-props--typing)
8. [Styling](#-8-styling)
9. [Performance & Optimization](#-9-performance--optimization)
10. [Error Handling](#-10-error-handling)
11. [API Calls & Async Data](#-11-api-calls--async-data)
12. [Forms & Validation](#-12-forms--validation)
13. [Routing](#-13-routing)
14. [Testing](#-14-testing)
15. [Accessibility (a11y)](#-15-accessibility-a11y)
16. [Internationalization (i18n)](#-16-internationalization-i18n)
17. [Imports & Dependencies](#-17-imports--dependencies)
18. [Naming Conventions](#-18-naming-conventions)
19. [Comments & Documentation](#-19-comments--documentation)
20. [Git & Commits](#-20-git--commits)
21. [Environment Variables](#-21-environment-variables)
22. [Linting & Formatting](#-22-linting--formatting)

---

## 🔒 1. Security

### 1.1 XSS Injection

**FORBIDDEN** to use `dangerouslySetInnerHTML` without sanitization.

```tsx
// ❌ FORBIDDEN - Direct XSS injection
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// ✅ If absolutely necessary, sanitize with DOMPurify
import DOMPurify from "dompurify";
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userInput) }} />

// ✅ Prefer React native rendering (automatic escaping)
<div>{userContent}</div>
```

### 1.2 Secrets & Keys

- **Never** store API keys, tokens, passwords in source code
- **Never** commit secrets in `.env` files
- Client-side environment variables (`VITE_*`, `NEXT_PUBLIC_*`, `REACT_APP_*`) are **NOT** secret — never store sensitive credentials
- Public API keys (e.g., Google Maps) are acceptable client-side if restricted by domain

```tsx
// ❌ FORBIDDEN
const API_KEY = "sk-1234567890abcdef";
const token = "ghp_xxxxxxxxxxxx";
fetch(`https://api.example.com?key=sk-secret123`);

// ✅ Environment variable (non-secret on client)
const apiUrl = import.meta.env.VITE_API_URL;

// ✅ Authenticated calls go through your backend
const data = await fetch("/api/protected-resource", {
  headers: { Authorization: `Bearer ${sessionToken}` },
});
```

### 1.3 Dynamic Evaluation

**FORBIDDEN**: `eval()`, `Function()`, `new Function()`, `setTimeout(string)`, `setInterval(string)`.

```tsx
// ❌ FORBIDDEN
eval(userInput);
setTimeout("alert('hello')", 1000);
new Function("return " + userExpression)();

// ✅ Alternatives
setTimeout(() => alert("hello"), 1000);
```

### 1.4 URLs & Links

```tsx
// ❌ Risk of javascript: injection
<a href={userProvidedUrl}>Link</a>

// ✅ Validate protocol
const isSafeUrl = (url: string) => /^https?:\/\//i.test(url);
{isSafeUrl(url) && <a href={url}>Link</a>}

// ✅ External links: always rel="noopener noreferrer"
<a href={url} target="_blank" rel="noopener noreferrer">External</a>
```

### 1.5 Dependencies

- No dependencies from unverified sources
- Check known vulnerabilities before adding a package (`npm audit`)
- No packages with suspicious postinstall scripts
- Prefer maintained packages (>1000 stars, recent updates)
- Lock exact versions in production (`package-lock.json` committed)
- Check bundle size before adding (`bundlephobia.com`)

### 1.6 Client-side Authentication

- **Never** store JWT in `localStorage` (vulnerable to XSS)
- Prefer `httpOnly`, `secure`, `SameSite=Strict` cookies
- Verify token expiration client-side before each request
- Implement refresh token mechanism
- Redirect to `/login` as soon as 401 is received

```tsx
// ❌ FORBIDDEN - JWT in localStorage
localStorage.setItem("token", jwt);

// ✅ httpOnly cookie managed by backend (invisible to JS)
// Token is sent automatically via cookies
await fetch("/api/data", { credentials: "include" });
```

### 1.7 Content Security Policy

- Do not disable CORS protections without documented reason
- Configure strict CSP in HTTP headers
- No inline styles via `style` attribute if strict CSP (prefer CSS classes)
- No inline scripts

### 1.8 Input Validation & Sanitization

- **All user input must be validated** (frontend for UX, backend for security)
- Sanitize file uploads (validate types, sizes, content)
- Validate all data from external sources with schemas (Zod)
- Never trust client-side validation alone

### 1.9 Rate Limiting

- Implement client-side rate limiting for expensive operations
- Debounce search inputs (300ms minimum)
- Throttle scroll/resize handlers (16ms ~60fps)
- Use `AbortController` to cancel in-flight requests

---

## 🏷 2. TypeScript

### 2.1 Strict Mode Required

```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true,
    "exactOptionalPropertyTypes": true
  }
}
```

### 2.2 No `any` Type

`any` is **FORBIDDEN**. Use `unknown` with type guard if type is unknown.

```tsx
// ❌ FORBIDDEN
function parse(data: any): any { return data.value; }
const result: any = await fetchData();
catch (error: any) { console.log(error.message); }

// ✅ Use unknown + type guard
function parse(data: unknown): string {
  if (typeof data === "object" && data !== null && "value" in data) {
    return String((data as { value: unknown }).value);
  }
  throw new Error("Invalid data");
}

// ✅ Type errors in catch blocks
catch (error: unknown) {
  const message = error instanceof Error ? error.message : "Unknown error";
  console.error(message);
}
```

### 2.3 Interfaces vs Types

- `interface` for objects and public contracts (extensible)
- `type` for unions, intersections, utility types, and mapped types

```tsx
// ✅ Interface for object shapes
interface User {
  id: string;
  name: string;
  email: string;
}

// ✅ Type for unions and complex types
type Status = "idle" | "loading" | "success" | "error";
type ApiResponse<T> = { data: T; meta: PaginationMeta } | { error: ApiError };
type UserWithRole = User & { role: Role };
```

### 2.4 Enums vs Union Types

Prefer `as const` and union types over `enum`.

```tsx
// ❌ Avoid
enum Status {
  Active = "active",
  Inactive = "inactive",
}

// ✅ Prefer
const STATUS = {
  Active: "active",
  Inactive: "inactive",
} as const;

type Status = (typeof STATUS)[keyof typeof STATUS];
```

### 2.5 Type Assertions

- Avoid `as` as much as possible — prefer type guards
- **FORBIDDEN**: `as any` — it's a workaround, not a solution
- Non-null assertions (`!`) are forbidden except justified with comment

```tsx
// ❌ FORBIDDEN
const user = data as User;
const value = (data as any).nested.field;
const el = document.getElementById("root")!;

// ✅ Type guard
function isUser(data: unknown): data is User {
  return (
    typeof data === "object" &&
    data !== null &&
    "id" in data &&
    "name" in data
  );
}
if (isUser(data)) {
  console.log(data.name); // Automatically typed
}

// ✅ Explicit null check
const el = document.getElementById("root");
if (!el) throw new Error("Root element not found");
```

### 2.6 Generics

- Name generics descriptively (not just `T` if ambiguous)
- Constrain generics with `extends` when possible

```tsx
// ❌ Ambiguous
function merge<T, U>(a: T, b: U): T & U;

// ✅ Descriptive and constrained
function merge<TBase extends object, TOverride extends object>(
  base: TBase,
  override: TOverride,
): TBase & TOverride;
```

### 2.7 Function Return Types

- Always explicitly type returns for exported/public functions
- Inferred type acceptable for short, obvious internal functions

```tsx
// ❌ Implicit return on exported function
export function formatUser(user: User) {
  return { ...user, displayName: `${user.firstName} ${user.lastName}` };
}

// ✅ Explicit return
export function formatUser(user: User): FormattedUser {
  return { ...user, displayName: `${user.firstName} ${user.lastName}` };
}
```

---

## 📁 3. Architecture & File Structure

### 3.1 Folder Structure

```
src/
├── app/                    # Entry point, providers, router
│   ├── App.tsx
│   ├── providers.tsx       # Composition of all providers
│   └── router.tsx
├── components/             # Reusable components (design system)
│   ├── ui/                 # Primitive components (Button, Input, Modal...)
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   ├── Button.test.tsx
│   │   │   ├── Button.stories.tsx  # Optional (Storybook)
│   │   │   └── index.ts
│   │   └── ...
│   └── layout/             # Header, Footer, Sidebar, PageLayout...
├── features/               # Business modules (feature-based)
│   ├── auth/
│   │   ├── components/     # Feature-specific components
│   │   ├── hooks/
│   │   ├── services/       # API calls
│   │   ├── stores/         # Local state management
│   │   ├── types/
│   │   ├── utils/
│   │   └── index.ts        # Barrel export (feature's public API)
│   ├── dashboard/
│   └── ...
├── hooks/                  # Global reusable hooks
├── services/               # API clients, interceptors, HTTP config
├── stores/                 # Global state management
├── types/                  # Shared global types
├── utils/                  # Pure utility functions
├── constants/              # Global constants
├── assets/                 # Images, fonts, SVGs
└── styles/                 # Global styles, theme, CSS variables
```

### 3.2 Structure Rules

- **1 component = 1 folder** with file, tests, and index
- **No imports between features** — if two features share code, extract to `components/`, `hooks/`, or `utils/`
- **Barrel exports** (`index.ts`) only at root of each feature and component — no deep barrels
- No `helpers` folder — use `utils` (pure functions) or `hooks`
- No catch-all `shared` folder — be specific

### 3.3 Size Limits

| Element | Max Limit | Action if Exceeded |
|---------|-----------|-------------------|
| Component | 200 lines | Split into sub-components |
| Function | 50 lines | Extract into utility functions |
| File | 300 lines | Reorganize into module |
| Component props | 7 props | Group into objects or redesign API |
| JSX nesting levels | 5 levels | Extract sub-components |
| Logic nesting levels | 3 levels | Early returns / extraction |

---

## ⚛️ 4. React Components

### 4.1 Functional Components Only

Class components are **FORBIDDEN** (except legacy error boundaries).

```tsx
// ❌ FORBIDDEN
class UserCard extends React.Component<Props> {
  render() { return <div>{this.props.name}</div>; }
}

// ✅ Function component
function UserCard({ name }: UserCardProps) {
  return <div>{name}</div>;
}
```

### 4.2 Component Declaration

- Use `function` (not `const` + arrow) for components — better for debugging (name in DevTools) and hoisting
- Arrow functions acceptable for inline/anonymous components and callbacks

```tsx
// ❌ Arrow function for named component
const UserCard = ({ name }: UserCardProps) => {
  return <div>{name}</div>;
};

// ✅ Function declaration
function UserCard({ name }: UserCardProps) {
  return <div>{name}</div>;
}

// ✅ Arrow OK for callbacks and inline components
{users.map((user) => (
  <li key={user.id}>{user.name}</li>
))}
```

### 4.3 Exports

- **1 exported component per file** — no multiple exports
- Use **named exports** (no `default export`)

```tsx
// ❌ Default export
export default function UserCard() {}

// ❌ Multiple exported components
export function UserCard() {}
export function UserAvatar() {}

// ✅ Single named export
export function UserCard({ name }: UserCardProps) {
  return <div>{name}</div>;
}
```

### 4.4 Component Internal Structure

Respect this order in each component:

```tsx
export function UserProfile({ userId }: UserProfileProps) {
  // 1. React hooks (useState, useRef, useContext...)
  const [isEditing, setIsEditing] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // 2. Custom hooks
  const { data: user, isLoading } = useUser(userId);
  const { t } = useTranslation();

  // 3. Derived variables / computed
  const fullName = user ? `${user.firstName} ${user.lastName}` : "";
  const canEdit = user?.role === "admin";

  // 4. Effects
  useEffect(() => {
    document.title = fullName;
  }, [fullName]);

  // 5. Handlers (prefixed with handle)
  function handleEditClick() {
    setIsEditing(true);
    inputRef.current?.focus();
  }

  function handleSave(formData: FormData) {
    // ...
  }

  // 6. Early returns (loading, error, empty states)
  if (isLoading) return <Skeleton />;
  if (!user) return <EmptyState message="User not found" />;

  // 7. Main render
  return (
    <div>
      <h1>{fullName}</h1>
      {canEdit && <button onClick={handleEditClick}>{t("edit")}</button>}
    </div>
  );
}
```

### 4.5 Fragments

- Use `<>...</>` instead of unnecessary `<div>` wrappers
- Use `<Fragment key={}>` when a key is needed

```tsx
// ❌ Unnecessary div wrapper
return (
  <div>
    <Header />
    <Main />
  </div>
);

// ✅ Fragment
return (
  <>
    <Header />
    <Main />
  </>
);
```

### 4.6 Conditional Rendering

```tsx
// ❌ Unreadable nested ternary
{isLoading ? <Spinner /> : error ? <Error /> : data ? <Content /> : <Empty />}

// ❌ && trap with numbers (0 is rendered)
{count && <Badge count={count} />}     // Displays "0" if count === 0

// ✅ Simple ternary
{isLoading ? <Spinner /> : <Content data={data} />}

// ✅ Early return for complex cases
if (isLoading) return <Spinner />;
if (error) return <Error error={error} />;
if (!data) return <Empty />;
return <Content data={data} />;

// ✅ Explicit boolean for && with numbers
{count > 0 && <Badge count={count} />}
{Boolean(items.length) && <List items={items} />}
```

### 4.7 Keys

- **FORBIDDEN** to use index as key in lists that can change (sort, filter, add, delete)
- Use unique and stable identifier (id, slug, uuid)

```tsx
// ❌ FORBIDDEN - Index as key
{users.map((user, index) => <UserCard key={index} user={user} />)}

// ✅ Unique ID
{users.map((user) => <UserCard key={user.id} user={user} />)}

// ✅ Index OK ONLY for static lists that never change
{menuItems.map((item, i) => <li key={i}>{item.label}</li>)}
```

### 4.8 Children & Composition

- Don't pass complex JSX as props — use `children` or composition pattern
- No prop drilling beyond 2 levels — use Context or state management

```tsx
// ❌ JSX as prop
<Card header={<div><h1>Title</h1><p>Subtitle</p></div>} />

// ✅ Composition pattern
<Card>
  <Card.Header>
    <h1>Title</h1>
    <p>Subtitle</p>
  </Card.Header>
  <Card.Body>Content</Card.Body>
</Card>
```

---

## 🪝 5. Hooks

### 5.1 Fundamental Rules

- **Never** call hooks in conditions, loops, or nested functions
- **Never** call hooks in callbacks or event handlers
- Custom hooks **always** start with `use`

```tsx
// ❌ FORBIDDEN - Conditional hook
if (isLoggedIn) {
  const [name, setName] = useState("");
}

// ❌ FORBIDDEN - Hook in loop
for (const item of items) {
  useEffect(() => {}, [item]);
}

// ✅ Condition the content, not the hook
const [name, setName] = useState("");
// Use name only if isLoggedIn
```

### 5.2 useState

- One `useState` per atomic value — don't group unrelated values in object
- If multiple states always update together, group in object or use `useReducer`

```tsx
// ❌ State object with unrelated values
const [state, setState] = useState({ name: "", isOpen: false, count: 0 });

// ✅ Atomic states
const [name, setName] = useState("");
const [isOpen, setIsOpen] = useState(false);
const [count, setCount] = useState(0);

// ✅ Object if values always related
const [position, setPosition] = useState({ x: 0, y: 0 });

// ✅ Functional update when new state depends on old
setCount((prev) => prev + 1);

// ❌ Risk of stale closure
setCount(count + 1);
```

### 5.3 useEffect

- **Always** specify dependencies — never empty array for "convenience"
- **Always** cleanup side effects (listeners, timers, subscriptions, abort controllers)
- **1 effect = 1 responsibility** — not one effect doing 5 things
- **Don't use useEffect** to derive state or transform data — use `useMemo` or computed variables

```tsx
// ❌ FORBIDDEN - No cleanup
useEffect(() => {
  window.addEventListener("resize", handleResize);
}, []);

// ❌ FORBIDDEN - useEffect for derived state
useEffect(() => {
  setFullName(`${firstName} ${lastName}`);
}, [firstName, lastName]);

// ✅ Cleanup
useEffect(() => {
  window.addEventListener("resize", handleResize);
  return () => window.removeEventListener("resize", handleResize);
}, [handleResize]);

// ✅ Derived variable (no state needed)
const fullName = `${firstName} ${lastName}`;

// ✅ AbortController for fetch
useEffect(() => {
  const controller = new AbortController();
  fetchData({ signal: controller.signal });
  return () => controller.abort();
}, [fetchData]);
```

### 5.4 useRef

- Use `useRef` to access DOM, not to store state to display
- If value triggers re-render → `useState`. If not → `useRef`
- Type DOM refs with correct HTML type

```tsx
// ✅ Typed DOM ref
const inputRef = useRef<HTMLInputElement>(null);

// ✅ Mutable value without re-render
const previousValueRef = useRef<string>("");
const timerIdRef = useRef<ReturnType<typeof setTimeout>>();
```

### 5.5 Custom Hooks

- Extract reusable logic into custom hooks
- One custom hook should have **one responsibility**
- Name return explicitly (not generic `[value, setValue]`)
- Return object if >2 values, tuple if ≤2

```tsx
// ✅ Well-structured custom hook
function useUser(userId: string) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setIsLoading(true);

    fetchUser(userId, { signal: controller.signal })
      .then(setUser)
      .catch(setError)
      .finally(() => setIsLoading(false));

    return () => controller.abort();
  }, [userId]);

  return { user, isLoading, error };  // Object for >2 values
}

// ✅ Tuple for ≤2 values
function useToggle(initial = false): [boolean, () => void] {
  const [value, setValue] = useState(initial);
  const toggle = useCallback(() => setValue((v) => !v), []);
  return [value, toggle];
}
```

---

## 🗄️ 6. State Management

### 6.1 State Hierarchy

Use simplest state type possible:

1. **Derived variable** (computed) — no state, just `const`
2. **Local state** (`useState`) — for single component
3. **Shared state via lifting** — for parent and direct children
4. **Context** — for specific subtree (theme, auth, i18n)
5. **Global store** (Zustand, Redux Toolkit, Jotai...) — for cross-cutting frequently updated state

### 6.2 Context

- **Don't** use Context for frequently updated state (causes cascade re-renders)
- Separate contexts by domain (not one mega-context)
- Always provide wrapper hook (`useAuth()` instead of `useContext(AuthContext)`)

```tsx
// ❌ Mega-context
const AppContext = createContext({ user, theme, locale, cart, notifications });

// ✅ Separated contexts
const AuthContext = createContext<AuthState | null>(null);

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
```

### 6.3 Global State

- Global state = data shared between unrelated features (auth, theme, cache)
- Global state should only contain **serializable** data (no functions, classes, or instances)
- Separate stores by functional domain
- No business logic in stores — only read/write
- Each store must expose typed **selectors**

### 6.4 Server State

- Use **TanStack Query** (or SWR) for server state (API data)
- **Never** store server data in global state (Redux, Zustand) — that's the query cache's role
- Configure `staleTime`, `gcTime` (formerly `cacheTime`), and `refetchOnWindowFocus` explicitly

```tsx
// ❌ Server state in Redux
dispatch(setUsers(await fetchUsers()));

// ✅ TanStack Query
const { data: users, isLoading } = useQuery({
  queryKey: ["users"],
  queryFn: fetchUsers,
  staleTime: 5 * 60 * 1000,  // 5 minutes
});
```

---

## 📋 7. Props & Typing

### 7.1 Props Naming Conventions

| Prop Type | Prefix/Convention | Example |
|---|---|---|
| Boolean | `is`, `has`, `should`, `can` | `isOpen`, `hasError`, `canEdit` |
| Handler | `on` + event | `onClick`, `onSubmit`, `onUserSelect` |
| Render prop | `render` + name | `renderHeader`, `renderItem` |
| Data | descriptive name | `user`, `items`, `errorMessage` |

### 7.2 Props Interface

- Always define `[ComponentName]Props` interface
- Child props inherit from native HTML type when relevant

```tsx
// ✅ Typed props with HTML inheritance
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
}

export function Button({
  variant,
  size = "md",
  isLoading = false,
  children,
  disabled,
  ...rest
}: ButtonProps) {
  return (
    <button disabled={disabled || isLoading} {...rest}>
      {isLoading ? <Spinner size={size} /> : children}
    </button>
  );
}
```

### 7.3 Default Props

- Use destructuring with default values — no `defaultProps`
- Always define default values for optional props when behavior is expected

```tsx
// ❌ FORBIDDEN (deprecated since React 18.3)
Button.defaultProps = { size: "md" };

// ✅ Default values in destructuring
function Button({ size = "md", variant = "primary" }: ButtonProps) {}
```

### 7.4 Limit Props

- Maximum **7 props** per component — beyond that, group into objects or redesign API
- Prefer composition (`children`, slots) over passing many props

---

## 🎨 8. Styling

### 8.1 Approach (choose one, stay consistent)

- **CSS Modules** (`.module.css`) — recommended for scoping
- **Tailwind CSS** — recommended for rapid prototyping and consistency
- **Styled-components / Emotion** — acceptable if already in place
- **CSS-in-JS runtime** (styled-components) discouraged in new projects (perf)
- **No global CSS** except reset/normalize and CSS variables

### 8.2 Tailwind (if used)

```tsx
// ❌ Classes too long in JSX — extract
<div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4 shadow-sm hover:shadow-md transition-shadow duration-200 dark:bg-gray-800 dark:border-gray-700">

// ✅ Extract via @apply in CSS file, or clsx + constant
const cardStyles = "flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4 shadow-sm hover:shadow-md transition-shadow dark:bg-gray-800 dark:border-gray-700";
<div className={cardStyles}>

// ✅ Conditional with clsx/cn
import { cn } from "@/utils/cn";
<button className={cn(
  "rounded px-4 py-2 font-medium",
  variant === "primary" && "bg-blue-600 text-white",
  variant === "ghost" && "bg-transparent text-gray-700",
  disabled && "opacity-50 cursor-not-allowed",
)}>
```

### 8.3 Inline Styles

- **Forbidden** for static styling — use CSS classes
- Acceptable **only** for dynamic computed values (position, runtime dimensions)

```tsx
// ❌ Static style inline
<div style={{ display: "flex", color: "red", padding: 16 }} />

// ✅ Dynamic style only
<div style={{ transform: `translateX(${offset}px)`, height: calculatedHeight }} />
```

### 8.4 Responsive Design

- Mobile-first (`min-width` media queries)
- Use consistent breakpoints (defined in theme/config)
- Don't hardcode px values for widths — use `%`, `rem`, `vw` or framework utilities

### 8.5 Theme & Design Tokens

- All colors, spacing, font sizes in CSS variables or tokens
- **No hardcoded values** (`#3b82f6`) in components — use variables

```css
/* ❌ FORBIDDEN - Hardcoded color */
.button { background-color: #3b82f6; }

/* ✅ CSS variable */
.button { background-color: var(--color-primary); }
```

---

## ⚡ 9. Performance & Optimization

### 9.1 Memoization

- `useMemo`: for **expensive calculations** or **objects/arrays** passed as props/dependencies
- `useCallback`: for **functions** passed as props to memoized components
- `React.memo`: for components that receive **same props** often
- **Don't** memoize by default — measure first, optimize later

```tsx
// ❌ Unnecessary memoization (trivial calculation)
const doubled = useMemo(() => count * 2, [count]);

// ✅ Justified memoization (expensive calculation)
const sortedItems = useMemo(
  () => items.toSorted((a, b) => a.score - b.score),
  [items],
);

// ✅ useCallback for handler passed to memoized component
const handleDelete = useCallback((id: string) => {
  setItems((prev) => prev.filter((item) => item.id !== id));
}, []);

// ✅ React.memo for pure component frequently re-rendered
const ExpensiveList = React.memo(function ExpensiveList({ items }: Props) {
  return items.map((item) => <ExpensiveItem key={item.id} item={item} />);
});
```

### 9.2 Lazy Loading

- Lazy-load routes with `React.lazy` + `Suspense`
- Lazy-load heavy components (charts, editors, complex modals)
- Use dynamic import for heavy libraries used occasionally

```tsx
// ✅ Lazy-loaded route
const Dashboard = lazy(() => import("@/features/dashboard"));

<Suspense fallback={<PageSkeleton />}>
  <Dashboard />
</Suspense>

// ✅ Dynamic import for heavy lib
async function generateChart(data: ChartData) {
  const { Chart } = await import("chart.js");
  // ...
}
```

### 9.3 Virtualized Lists

- Use virtualization for lists with **>50 elements** (TanStack Virtual, react-window)
- Never render hundreds/thousands of DOM elements simultaneously

### 9.4 Images

- Always `alt` attribute (see accessibility)
- Use `loading="lazy"` for images below fold
- Use modern format (WebP, AVIF) with fallback
- Specify `width` and `height` to avoid layout shifts
- Use `srcSet` and `sizes` for responsive

```tsx
// ✅ Optimized image
<img
  src="/images/hero.webp"
  alt="Meaningful description"
  width={1200}
  height={600}
  loading="lazy"
  decoding="async"
/>
```

### 9.5 Debounce & Throttle

- Debounce search inputs (300ms minimum)
- Throttle scroll/resize handlers (16ms ~60fps or more)
- Use `AbortController` to cancel in-flight requests before next

### 9.6 Bundle Size

- No full library imports when selective import possible
- Check bundle size before adding dependency (`bundlephobia.com`)

```tsx
// ❌ Import entire lib
import _ from "lodash";
const sorted = _.sortBy(items, "name");

// ✅ Selective import
import sortBy from "lodash/sortBy";
const sorted = sortBy(items, "name");

// ✅ Even better: use native
const sorted = items.toSorted((a, b) => a.name.localeCompare(b.name));
```

---

## 🚨 10. Error Handling

### 10.1 Error Boundaries

- Each feature/route must have **Error Boundary**
- Error Boundary displays usable fallback (not blank screen)
- Log error to monitoring service (Sentry, DataDog...)

```tsx
// ✅ Error Boundary with fallback
<ErrorBoundary
  fallback={<ErrorFallback />}
  onError={(error, info) => errorReporter.capture(error, info)}
>
  <Dashboard />
</ErrorBoundary>
```

### 10.2 Try/Catch

- Always catch errors in async calls
- **FORBIDDEN**: empty catch or catch that ignores error
- Type errors

```tsx
// ❌ FORBIDDEN - Empty catch
try { await saveData(); } catch {}

// ❌ FORBIDDEN - console.log in production
try { await saveData(); } catch (e) { console.log(e); }

// ✅ Complete handling
try {
  await saveData(formData);
} catch (error: unknown) {
  const appError = toAppError(error);
  logger.error("Failed to save data", { error: appError, context: "UserForm" });
  showToast({ type: "error", message: appError.userMessage });
}
```

### 10.3 User-facing Errors

- Display **understandable** messages to users (no stack traces)
- Offer recovery action (retry, refresh, contact support)
- Distinguish network errors, validation errors, and server errors

---

## 🌐 11. API Calls & Async Data

### 11.1 HTTP Client

- Use centralized HTTP client (Axios instance or fetch wrapper)
- Configure interceptors for: auth headers, refresh token, logging, global errors
- **Always** timeout on requests

```tsx
// ✅ Centralized client
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 10_000,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await refreshToken();
      return apiClient.request(error.config);
    }
    return Promise.reject(error);
  },
);
```

### 11.2 API Services

- Group calls by domain in service files
- Type inputs AND outputs for each endpoint

```tsx
// ✅ Typed service
// features/users/services/userService.ts
export const userService = {
  getAll: (params: GetUsersParams): Promise<PaginatedResponse<User>> =>
    apiClient.get("/users", { params }).then((r) => r.data),

  getById: (id: string): Promise<User> =>
    apiClient.get(`/users/${id}`).then((r) => r.data),

  create: (data: CreateUserPayload): Promise<User> =>
    apiClient.post("/users", data).then((r) => r.data),
};
```

### 11.3 Loading & Error States

Every async call must handle **3 states**: loading, error, success.

```tsx
// ❌ No loading/error handling
const [users, setUsers] = useState([]);
useEffect(() => { fetchUsers().then(setUsers); }, []);

// ✅ Via TanStack Query (recommended)
const { data: users, isLoading, error } = useQuery({
  queryKey: ["users"],
  queryFn: userService.getAll,
});

if (isLoading) return <Skeleton />;
if (error) return <ErrorMessage error={error} />;
return <UserList users={users} />;
```

### 11.4 Mutations

- Use `useMutation` (TanStack Query) for write operations
- Cache invalidation after successful mutation
- Optimistic updates if UX justifies

---

## 📝 12. Forms & Validation

### 12.1 Form Library

- Use **React Hook Form** (or Formik) for complex forms (>3 fields)
- Use **Zod** (or Yup) for schema validation
- Simple forms (1-2 fields): local state acceptable

### 12.2 Validation

- Validate **client-side** (fast UX) AND **server-side** (security)
- Display validation errors inline under each field
- Validate on blur for individual fields, on submit for entire form
- **Never** trust only client-side validation

```tsx
// ✅ Zod + React Hook Form
const userSchema = z.object({
  email: z.string().email("Invalid email"),
  name: z.string().min(2, "Minimum 2 characters").max(50),
  age: z.number().min(18, "Must be 18 or older"),
});

type UserFormData = z.infer<typeof userSchema>;

function UserForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<UserFormData>({
    resolver: zodResolver(userSchema),
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <Input {...register("email")} error={errors.email?.message} />
      <Input {...register("name")} error={errors.name?.message} />
      <Button type="submit">Save</Button>
    </form>
  );
}
```

### 12.3 Form UX

- Disable submit button during loading
- Display visual feedback after submission (toast, redirect, or inline message)
- Handle multiple submissions (prevent double-click)
- Keep form data if user navigates accidentally (warn on unsaved changes)

---

## 🛤️ 13. Routing

### 13.1 Conventions

- Routes in kebab-case: `/user-settings`, not `/userSettings`
- Typed dynamic parameters: `/users/:userId`
- Lazy-loaded routes by default
- Explicit redirects for old URLs

### 13.2 Route Protection

```tsx
// ✅ Protected route
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) return <PageSkeleton />;
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return <>{children}</>;
}
```

### 13.3 Routing Error Handling

- 404 page for unknown routes
- Lazy loading error handling (automatic retry + fallback)

---

## 🧪 14. Testing

### 14.1 Testing Strategy

| Type | Tool | Target | Expected Coverage |
|---|---|---|---|
| Unit | Vitest | Utils, hooks, services | >80% |
| Component | Testing Library | Isolated components | Key interactions |
| Integration | Testing Library | Complete features | Happy paths + errors |
| E2E | Playwright / Cypress | Critical flows | Smoke tests |

### 14.2 Testing Conventions

- Test file next to source: `Button.test.tsx` in same folder
- Naming: `describe("ComponentName")` then `it("should...")` in English
- Test **behavior**, not implementation
- No tests on implementation details (internal state, CSS class names)

```tsx
// ❌ Implementation test
expect(component.state.isOpen).toBe(true);
expect(wrapper.find(".modal-overlay")).toHaveLength(1);

// ✅ Behavior test
await user.click(screen.getByRole("button", { name: /open/i }));
expect(screen.getByRole("dialog")).toBeInTheDocument();
```

### 14.3 Testing Library

- Prioritize accessible queries: `getByRole` > `getByLabelText` > `getByText` > `getByTestId`
- `getByTestId` as **last resort** only
- Use `userEvent` (not `fireEvent`) to simulate interactions

```tsx
// ❌ Fragile queries
screen.getByTestId("submit-btn");
screen.getByClassName("btn-primary");

// ✅ Accessible queries
screen.getByRole("button", { name: /save/i });
screen.getByLabelText(/email address/i);
```

### 14.4 Mocks

- Mock network calls with MSW (Mock Service Worker), not fetch/axios functions
- **Never** mock what you're testing — only mock external dependencies
- Reset mocks between tests (`afterEach`)

---

## ♿ 15. Accessibility (a11y)

### 15.1 Semantic HTML

- Use semantic HTML tags: `<nav>`, `<main>`, `<article>`, `<section>`, `<aside>`, `<header>`, `<footer>`
- **FORBIDDEN**: clickable `<div>` without role or keyboard support

```tsx
// ❌ FORBIDDEN - Clickable div
<div onClick={handleClick}>Click here</div>

// ✅ Semantic button
<button onClick={handleClick}>Click here</button>

// ✅ If non-interactive element MUST be clickable (rare)
<div role="button" tabIndex={0} onClick={handleClick} onKeyDown={handleKeyDown}>
  Click here
</div>
```

### 15.2 Images & Media

- All images have `alt` — descriptive if informative, empty (`alt=""`) if decorative
- Interactive icons have `aria-label`
- Videos have captions

```tsx
// ❌ No alt
<img src="/logo.png" />

// ✅ Descriptive alt
<img src="/chart-q3.png" alt="Q3 2024 sales chart showing 15% growth" />

// ✅ Empty alt for decorative
<img src="/decorative-border.svg" alt="" />

// ✅ Icon with label
<button aria-label="Close dialog">
  <XIcon aria-hidden="true" />
</button>
```

### 15.3 Forms

- Each input has explicitly associated `<label>` (via `htmlFor`)
- Field groups use `<fieldset>` and `<legend>`
- Validation errors associated via `aria-describedby`
- Required fields use `aria-required="true"`

```tsx
// ✅ Accessible input
<div>
  <label htmlFor="email">Email</label>
  <input
    id="email"
    type="email"
    aria-required="true"
    aria-invalid={!!errors.email}
    aria-describedby={errors.email ? "email-error" : undefined}
  />
  {errors.email && (
    <p id="email-error" role="alert">{errors.email.message}</p>
  )}
</div>
```

### 15.4 Keyboard Navigation

- All interactive elements focusable via Tab
- Tab order follows logical visual order
- Modals trap focus (focus trap)
- Escape closes modals/dropdowns
- Focus always visible — **never** `outline: none` without alternative

### 15.5 ARIA

- Prefer semantic HTML over ARIA attributes (first rule of ARIA is don't use ARIA)
- Dynamic elements use `aria-live` to announce changes
- Custom components (tabs, accordions, combobox) follow WAI-ARIA patterns

### 15.6 Contrast & Colors

- Minimum contrast ratio 4.5:1 for normal text, 3:1 for large text
- Never communicate information **only** by color (add icon or text)

---

## 🌍 16. Internationalization (i18n)

### 16.1 General Rules

- **No hardcoded text anywhere** — UI components, error messages, schemas, API responses
- Use **react-i18next** (most popular React i18n library)
- Translation keys follow convention: `feature.component.element`
- Support RTL (right-to-left) languages if relevant
- Format dates, numbers, and currencies with `Intl` API

```tsx
// ❌ Hardcoded text
<h1>Welcome to our platform</h1>
<p>You have {count} messages</p>

// ✅ Translation key
const { t } = useTranslation();
<h1>{t("dashboard.welcome.title")}</h1>
<p>{t("dashboard.messages.count", { count })}</p>

// ✅ Date formatting
const formatted = new Intl.DateTimeFormat(locale, {
  dateStyle: "long",
}).format(date);
```

### 16.2 react-i18next Setup

**Installation:**
```bash
npm install i18next react-i18next i18next-browser-languagedetector
```

**Configuration** (`src/i18n/config.ts`):
```tsx
import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

import en from "./locales/en.json";
// import fr from "./locales/fr.json";

export const defaultNS = "translation";
export const resources = {
  en: { translation: en },
  // fr: { translation: fr },
} as const;

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    defaultNS,
    fallbackLng: "en",
    detection: {
      order: ["localStorage", "navigator"],
      caches: ["localStorage"],
      lookupLocalStorage: "i18nextLng",
    },
    interpolation: {
      escapeValue: false, // React already escapes
    },
    debug: import.meta.env.DEV,
  });

export default i18n;
```

**Import in main.tsx** (BEFORE App):
```tsx
import "./i18n/config";
import App from "./App";
```

**Translation Files** (`src/i18n/locales/en.json`):
```json
{
  "common": {
    "submit": "Submit",
    "cancel": "Cancel",
    "save": "Save"
  },
  "auth": {
    "login": {
      "title": "Sign In",
      "submit": "Sign In"
    }
  },
  "validation": {
    "email": {
      "invalid": "Invalid email format"
    }
  }
}
```

**Usage in Components:**
```tsx
import { useTranslation } from "react-i18next";

export function LoginForm() {
  const { t } = useTranslation();

  return (
    <>
      <h1>{t("auth.login.title")}</h1>
      <Button>{t("common.submit")}</Button>

      {/* With interpolation */}
      <p>{t("auth.welcome", { name: user.name })}</p>

      {/* With pluralization */}
      <p>{t("items.count", { count: items.length })}</p>
    </>
  );
}
```

### 16.3 Zod Schemas — NO Hardcoded Messages

**Critical Rule:** Zod schemas MUST NOT contain hardcoded error messages in any language.

**Why:**
- Schemas are shared across multiple contexts (frontend validation, API responses, etc.)
- Error messages should be internationalized at the UI layer, not in the schema layer
- Backend validation messages should be handled server-side and translated via API

**Three Acceptable Approaches:**

#### Option 1: Generic English Messages (Recommended for shared schemas)

```tsx
// ✅ Generic English messages (will be translated at UI layer)
export const loginRequestSchema = z.object({
  email: z.string().email("Invalid email format"),
  password: z.string().min(1, "Password is required"),
});

// In your component:
const errors = zodErrors.map(err => t(`validation.${err.code}`, err.params));
```

#### Option 2: No Custom Messages (Let Zod provide defaults)

```tsx
// ✅ No custom message — Zod provides default English error
export const loginRequestSchema = z.object({
  email: z.string().email(), // Default: "Invalid email"
  password: z.string().min(8), // Default: "String must contain at least 8 character(s)"
});

// Frontend can then map these to i18n keys
```

#### Option 3: Message Keys (For advanced i18n setups)

```tsx
// ✅ Use translation keys directly in schemas
export const loginRequestSchema = z.object({
  email: z.string().email("validation.email.invalid"),
  password: z.string().min(1, "validation.password.required"),
});

// Requires a Zod error map that resolves keys:
z.setErrorMap((issue, ctx) => {
  return { message: t(ctx.defaultError) };
});
```

### 16.4 Forbidden Patterns

```tsx
// ❌ FORBIDDEN - Hardcoded French in schema
export const loginRequestSchema = z.object({
  email: z.string().email("Format email invalide"),
  password: z.string().min(8, "Minimum 8 caractères"),
});

// ❌ FORBIDDEN - Any non-English hardcoded text in schemas
export const passwordSchema = z.string()
  .min(8, "Mínimo 8 caracteres") // Spanish
  .regex(/[A-Z]/, "Mindestens ein Großbuchstabe"); // German

// ❌ FORBIDDEN - Hardcoded text in toast notifications
toast({ title: "Erreur", description: "Le code est invalide" });

// ✅ Use translation keys
toast({
  title: t("error.title"),
  description: t("error.otp.invalid")
});

// ❌ FORBIDDEN - Hardcoded labels in forms
<Label>Nom d'utilisateur</Label>

// ✅ Use translation keys
<Label>{t("form.username.label")}</Label>
```

### 16.5 Component Text

Every visible text must use translation keys:

```tsx
// ❌ Hardcoded
<Button>Submit</Button>
<Placeholder>Enter your email...</Placeholder>
<ErrorMessage>Invalid input</ErrorMessage>

// ✅ Translated
<Button>{t("common.submit")}</Button>
<Placeholder>{t("form.email.placeholder")}</Placeholder>
<ErrorMessage>{t(error.message)}</ErrorMessage>
```

### 16.6 API Error Messages

When displaying errors from API:

```tsx
// API should return error codes, not localized messages
interface ApiError {
  code: "INVALID_CREDENTIALS" | "ACCOUNT_LOCKED" | "OTP_EXPIRED";
  params?: Record<string, unknown>;
}

// Frontend translates based on code
const errorMessage = t(`api.errors.${error.code}`, error.params);

toast({
  title: t("error.title"),
  description: errorMessage,
  variant: "destructive",
});
```

### 16.7 Translation Key Conventions

Use a consistent, hierarchical structure:

```
common.button.save
common.button.cancel
common.error.generic
auth.login.title
auth.login.email.label
auth.login.email.placeholder
auth.login.password.label
auth.otp.title
auth.otp.helper
validation.email.invalid
validation.password.min_length
validation.required
api.errors.INVALID_CREDENTIALS
api.errors.ACCOUNT_LOCKED
```

### 16.8 Migration Strategy

When removing hardcoded text from existing code:

1. **Identify all hardcoded text** (grep for string literals in quotes)
2. **Create translation keys** following the convention
3. **Add translations** to all supported language files
4. **Replace hardcoded text** with `t()` calls
5. **Test all languages** to ensure nothing is missing

```bash
# Find hardcoded French text in schemas
grep -r "é\|è\|à\|ê\|ô" resources/schemas/

# Find hardcoded strings in components
grep -r "=\"[A-Z]" src/components/
```

---

## 📦 17. Imports & Dependencies

### 17.1 Import Order

Separate with blank line between each group:

```tsx
// 1. React and React libraries
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

// 2. External libraries
import { z } from "zod";
import { useQuery } from "@tanstack/react-query";

// 3. Internal aliases (absolute)
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/features/auth";
import { formatDate } from "@/utils/formatDate";

// 4. Relative imports (same feature)
import { UserAvatar } from "./UserAvatar";
import type { UserCardProps } from "./types";

// 5. Styles
import styles from "./UserCard.module.css";
```

### 17.2 Rules

- **Path aliases** mandatory (`@/` = `src/`) — no deep relative imports (`../../../`)
- No unused imports
- No `import *` except justified (e.g., d3 namespace)
- Separate **type** imports with `import type`

```tsx
// ❌ Deep relative import
import { Button } from "../../../components/ui/Button";
import { User } from "../../../types";

// ✅ Alias + import type
import { Button } from "@/components/ui/Button";
import type { User } from "@/types";
```

### 17.3 Dependencies

- Check bundle size on bundlephobia.com before adding package
- Prefer native solutions when they exist
- No packages with 0 maintenance (last commit >1 year, unaddressed open issues)
- Document **why** for each non-obvious dependency in README

---

## 📛 18. Naming Conventions

### 18.1 Conventions

| Element | Convention | Example |
|---|---|---|
| Components | PascalCase | `UserProfileCard` |
| Component files | PascalCase | `UserProfileCard.tsx` |
| Hooks | camelCase with `use` | `useUserProfile` |
| Hook files | camelCase | `useUserProfile.ts` |
| Utils / functions | camelCase | `formatCurrency`, `parseDate` |
| Util files | camelCase | `formatCurrency.ts` |
| Constants | UPPER_SNAKE_CASE | `MAX_FILE_SIZE`, `API_ENDPOINTS` |
| Types / Interfaces | PascalCase | `UserProfile`, `ApiResponse` |
| Type files | camelCase or PascalCase | `types.ts`, `UserTypes.ts` |
| Enum values (as const) | PascalCase or UPPER_SNAKE | `Status.Active`, `STATUS.ACTIVE` |
| CSS modules | camelCase | `styles.userCard` |
| CSS classes (plain) | kebab-case | `user-card` |
| URL routes | kebab-case | `/user-settings` |
| Query keys | camelCase array | `["users", "list", { page }]` |
| Folders | kebab-case or camelCase | `user-profile/` or `userProfile/` |

### 18.2 Descriptive Naming

- Names must be **self-documenting** — no cryptic abbreviations
- Booleans start with `is`, `has`, `should`, `can`, `will`
- Handlers start with `handle` (in component) or `on` (as prop)
- Functions returning boolean start with `is`, `has`, `can`

```tsx
// ❌ Cryptic names
const d = new Date();
const arr = users.filter((u) => u.a);
const handleCl = () => {};
const flag = true;

// ✅ Descriptive names
const createdAt = new Date();
const activeUsers = users.filter((user) => user.isActive);
const handleDeleteClick = () => {};
const isModalOpen = true;
```

### 18.3 Name Length

- Minimum 3 characters (except `i`, `j` in loops, `e` for events, `t` for translations)
- Component names reflect their role: `UserProfileEditForm`, not `Form1`
- File names exactly match main export name

---

## 💬 19. Comments & Documentation

### 19.1 Rules

- Comment the **why**, never the **what** (code should be self-explanatory)
- No commented-out code — delete it (Git keeps history)
- `TODO` and `FIXME` include link to ticket/issue

```tsx
// ❌ Useless comment
// Increment counter
setCount(count + 1);

// ❌ Commented code
// const oldImplementation = () => { ... };

// ✅ Useful comment (explains why)
// 300ms delay to avoid API calls during fast typing
const SEARCH_DEBOUNCE_MS = 300;

// ✅ TODO with ticket
// TODO(JIRA-1234): Replace with v2 API when backend is ready
```

### 19.2 JSDoc

- Document public components (design system), custom hooks, and exported utility functions
- No JSDoc for obvious internal functions

```tsx
/**
 * Format amount in local currency.
 *
 * @param amount - Amount in cents
 * @param currency - ISO 4217 currency code (e.g., "EUR", "USD")
 * @param locale - BCP 47 locale (default: "en-US")
 * @returns Formatted amount (e.g., "$12.50")
 *
 * @example
 * formatCurrency(1250, "USD") // "$12.50"
 * formatCurrency(1250, "EUR", "fr-FR") // "12,50 €"
 */
export function formatCurrency(
  amount: number,
  currency: string,
  locale = "en-US",
): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
  }).format(amount / 100);
}
```

---

## 📌 20. Git & Commits

### 20.1 Conventional Commits

Format: `type(scope): description`

| Type | Usage |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Refactoring without behavior change |
| `style` | Style/formatting changes (not CSS) |
| `docs` | Documentation |
| `test` | Add/modify tests |
| `chore` | Maintenance, dependencies, config |
| `perf` | Performance improvement |
| `ci` | CI/CD configuration |

```bash
# ✅ Good commit messages
feat(auth): add OAuth2 Google login
fix(dashboard): prevent crash when user has no data
refactor(api): extract HTTP client into shared service
test(UserCard): add tests for loading and error states
chore(deps): upgrade React to 19.1

# ❌ Bad
fix: fix stuff
update code
WIP
```

### 20.2 Branches

- `main` / `master`: production, always stable
- `develop`: integration
- `feature/TICKET-description`: features
- `fix/TICKET-description`: fixes
- `hotfix/TICKET-description`: urgent production fixes

### 20.3 Commit Size

- **One commit = one logical change** — no mega-commits
- Files unrelated to change should not be included
- Diff should be reviewable in <15 minutes

---

## 🔧 21. Environment Variables

### 21.1 Conventions

- Mandatory prefix per framework: `VITE_`, `NEXT_PUBLIC_`, `REACT_APP_`
- Committed `.env.example` file with all variables (empty values)
- `.env`, `.env.local`, `.env.production` in `.gitignore`
- Validate variables at app startup

```tsx
// ✅ Validation at startup (e.g., with Zod)
const envSchema = z.object({
  VITE_API_URL: z.string().url(),
  VITE_APP_ENV: z.enum(["development", "staging", "production"]),
  VITE_SENTRY_DSN: z.string().optional(),
});

export const env = envSchema.parse(import.meta.env);
```

### 21.2 `.env.example` File

```env
# API
VITE_API_URL=
VITE_API_TIMEOUT=10000

# Auth
VITE_AUTH_DOMAIN=
VITE_AUTH_CLIENT_ID=

# Monitoring
VITE_SENTRY_DSN=

# Feature flags
VITE_FEATURE_NEW_DASHBOARD=false
```

---

## 🧹 22. Linting & Formatting

### 22.1 Required Tools

| Tool | Role |
|---|---|
| ESLint | Code quality, bug detection |
| Prettier | Automatic formatting |
| TypeScript | Type checking |
| Husky + lint-staged | Pre-commit hooks |

### 22.2 Recommended ESLint Rules

```json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/strict-type-checked",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "plugin:jsx-a11y/strict",
    "plugin:import/typescript",
    "prettier"
  ],
  "rules": {
    "no-console": ["warn", { "allow": ["warn", "error"] }],
    "no-debugger": "error",
    "no-alert": "error",
    "prefer-const": "error",
    "no-var": "error",
    "eqeqeq": ["error", "always"],
    "curly": ["error", "all"],
    "react/prop-types": "off",
    "react/react-in-jsx-scope": "off",
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    "@typescript-eslint/consistent-type-imports": "error",
    "import/order": ["error", {
      "groups": ["builtin", "external", "internal", "parent", "sibling", "index"],
      "newlines-between": "always"
    }]
  }
}
```

### 22.3 Prettier Config

```json
{
  "semi": true,
  "singleQuote": false,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "bracketSpacing": true,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

### 22.4 Pre-commit

```json
// package.json
{
  "lint-staged": {
    "*.{ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{css,json,md}": [
      "prettier --write"
    ]
  }
}
```

---

## 📋 SUMMARY CHECKLIST

Before delivering any feature, validate:

✅ **Security**
- [ ] No XSS vulnerabilities (no `dangerouslySetInnerHTML` without sanitization)
- [ ] No secrets in code or committed `.env` files
- [ ] No `eval()` or dynamic code execution
- [ ] URLs validated before use
- [ ] External links have `rel="noopener noreferrer"`
- [ ] No JWT in `localStorage` (use httpOnly cookies)
- [ ] Input validation and sanitization

✅ **TypeScript**
- [ ] Strict mode enabled
- [ ] No `any` types
- [ ] Explicit return types for exported functions
- [ ] Proper error typing in catch blocks
- [ ] Type guards instead of assertions

✅ **Architecture**
- [ ] Components organized by feature/domain
- [ ] No imports between features
- [ ] Component <200 lines, functions <50 lines
- [ ] No prop drilling beyond 2 levels

✅ **Components**
- [ ] Function declarations (not const + arrow)
- [ ] Named exports (not default)
- [ ] Proper internal structure (hooks → computed → effects → handlers → render)
- [ ] Early returns for loading/error states
- [ ] Unique stable keys in lists (not index)

✅ **Hooks**
- [ ] No conditional hooks
- [ ] useEffect with cleanup
- [ ] Proper dependencies array
- [ ] Custom hooks for reusable logic

✅ **State**
- [ ] Server state in TanStack Query (not Redux/Zustand)
- [ ] Local state for component-specific data
- [ ] Context for domain-specific subtrees
- [ ] Global store only for cross-cutting concerns

✅ **Validation**
- [ ] NO hardcoded validations in components
- [ ] All forms use `useForm` + `zodResolver`
- [ ] Zod schemas for request and response
- [ ] Schema tests written

✅ **API**
- [ ] All API calls through hooks (no direct calls in components)
- [ ] Query keys exported
- [ ] Mutations with cache invalidation
- [ ] Error handling with toast
- [ ] Loading and error states

✅ **Security**
- [ ] No sensitive data in localStorage
- [ ] Protected routes implemented
- [ ] XSS prevention
- [ ] Input validation and sanitization

✅ **Performance**
- [ ] Code splitting for routes
- [ ] Memoization where appropriate (measured first)
- [ ] Query optimization (staleTime, prefetch)
- [ ] Lazy loading for heavy components
- [ ] Virtualization for long lists (>50 items)

✅ **Accessibility**
- [ ] ARIA labels on interactive elements
- [ ] Keyboard navigation support
- [ ] Semantic HTML
- [ ] Error announcements with `role="alert"`
- [ ] Alt text on all images

✅ **Code Quality**
- [ ] All comments in English
- [ ] Descriptive naming (no abbreviations)
- [ ] Conventional commits
- [ ] ESLint passing
- [ ] Prettier formatted

---

> **💡 How to use this file**
>
> 1. Copy to your React project root
> 2. Remove sections that don't apply (e.g., i18n if not multilingual)
> 3. Adapt technical choices (CSS Modules vs Tailwind, Zustand vs Redux, etc.)
> 4. Add your specific conventions (business patterns, API architecture, etc.)
> 5. Review agents will use this file as absolute reference
> 6. Update as your project evolves and new patterns emerge
