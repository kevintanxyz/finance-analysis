# Frontend Cleanup Plan - WealthPoint MCP

**Date**: February 12, 2026
**Objective**: Remove Supabase/auth dependencies and prepare for MCP integration

---

## 🗑️ Files & Folders to DELETE

### 1. Authentication (Complete removal)
```
src/components/auth/
src/contexts/AuthContext.tsx
src/pages/Login.tsx
src/pages/VerifyOTP.tsx
src/pages/ForgotPassword.tsx
```

### 2. Supabase Integration
```
src/integrations/supabase/
supabase/
```

### 3. Support System
```
src/components/support/
src/contexts/SupportContext.tsx
src/pages/Support.tsx
src/pages/SupportTicketDetail.tsx
src/lib/support/
```

### 4. Client Onboarding
```
src/components/client-onboarding/
src/components/onboarding/
src/contexts/OnboardingContext.tsx
src/pages/ClientOnboarding.tsx
src/pages/Onboarding.tsx
src/pages/OnboardingDetail.tsx
src/pages/OnboardingNew.tsx
src/lib/onboarding/
```

### 5. Settings (Partial - keep only theme/preferences)
```
src/components/settings/banks/
src/components/settings/billing/
src/components/settings/sharing/
src/components/settings/strategic-allocation/
```

### 6. Dependencies to Remove
**package.json**:
- `@supabase/supabase-js`
- Any auth-related packages

---

## ✅ Files & Folders to KEEP

### Core Infrastructure
- ✅ `src/components/ui/` - shadcn/ui components
- ✅ `src/contexts/ThemeContext.tsx` - Dark/light mode
- ✅ `src/components/AppLayout.tsx` - Main layout
- ✅ `src/hooks/` - Custom hooks (except auth-related)
- ✅ `src/utils/` - Utility functions
- ✅ `src/lib/` - Helper libraries

### Useful Components
- ✅ `src/components/financial-table/` - Financial tables (adapt for portfolio)
- ✅ `src/components/settings/preferences/` - Theme/language settings

### Potentially Useful Pages (to adapt)
- ✅ `src/pages/Positions.tsx` - Adapt for portfolio positions
- ✅ `src/pages/Transactions.tsx` - Adapt for portfolio transactions
- ✅ `src/pages/Settings.tsx` - Simplify (theme + preferences only)
- ✅ `src/pages/NotFound.tsx` - 404 page

---

## 🆕 Files to CREATE

### 1. MCP Client Infrastructure
```
src/services/
├── mcp-client.ts          # HTTP client for MCP server (port 3001)
├── mcp-types.ts           # TypeScript types for MCP protocol
└── mcp-tools.ts           # Typed wrappers for MCP tools

src/hooks/
├── useMCP.ts              # Generic hook to call MCP tools
├── usePortfolio.ts        # Hook for portfolio operations
├── useAnalysis.ts         # Hook for analysis tools
└── useMarketData.ts       # Hook for market data tools
```

### 2. New Pages
```
src/pages/
├── Chat.tsx               # Main MCP chat interface
├── Dashboard.tsx          # Portfolio dashboard with charts
├── Analysis.tsx           # Analysis tools page
└── Upload.tsx             # PDF upload page
```

### 3. Chart Components (Recharts wrappers)
```
src/components/charts/
├── AllocationPieChart.tsx        # Asset allocation pie chart
├── PerformanceLineChart.tsx      # Performance over time
├── RiskBarChart.tsx              # Risk metrics bar chart
├── CorrelationHeatmap.tsx        # Correlation matrix
├── DividendBarChart.tsx          # Dividend analysis
└── PortfolioSummaryCards.tsx     # KPI cards
```

### 4. Chat Components
```
src/components/chat/
├── ChatInput.tsx                 # Message input with file upload
├── ChatMessage.tsx               # Message bubble with conditional rendering
├── ChatMessageList.tsx           # Scrollable message list
├── ChatToolResult.tsx            # Render tool results (text/chart/table)
└── ChatTypingIndicator.tsx       # Loading indicator
```

### 5. Portfolio Components
```
src/components/portfolio/
├── PositionsTable.tsx            # Portfolio positions table
├── AllocationBreakdown.tsx       # Allocation breakdown
├── PerformanceSummary.tsx        # Performance summary
└── RiskMetrics.tsx               # Risk metrics display
```

---

## 🔧 Files to MODIFY

### 1. App.tsx
**Changes**:
- Remove AuthProvider, SupportProvider
- Remove ProtectedRoute wrapper
- Update routes (remove auth routes, add Chat/Dashboard/Analysis)
- Keep ThemeProvider, QueryClientProvider

**New routes**:
```tsx
<Routes>
  <Route path="/" element={<AppLayout><Dashboard /></AppLayout>} />
  <Route path="/chat" element={<AppLayout><Chat /></AppLayout>} />
  <Route path="/upload" element={<AppLayout><Upload /></AppLayout>} />
  <Route path="/analysis" element={<AppLayout><Analysis /></AppLayout>} />
  <Route path="/positions" element={<AppLayout><Positions /></AppLayout>} />
  <Route path="/transactions" element={<AppLayout><Transactions /></AppLayout>} />
  <Route path="/settings" element={<AppLayout><Settings /></AppLayout>} />
  <Route path="*" element={<NotFound />} />
</Routes>
```

### 2. AppLayout.tsx
**Changes**:
- Remove auth-dependent logic (user profile, logout)
- Update navigation menu (Chat, Dashboard, Analysis, Upload)
- Keep theme switcher

### 3. package.json
**Remove**:
```json
"@supabase/supabase-js": "^2.93.2",
```

**Add** (if not present):
```json
"@modelcontextprotocol/sdk": "^1.0.0",  // MCP TypeScript SDK
"axios": "^1.6.0"  // HTTP client for MCP server
```

### 4. .env
**Remove Supabase vars**:
```env
# REMOVE
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
```

**Add MCP vars**:
```env
# MCP Server
VITE_MCP_SERVER_URL=http://localhost:3001
VITE_MCP_TRANSPORT=streamable-http
```

### 5. Settings.tsx
**Simplify to only**:
- Theme preferences (dark/light/system)
- Language selection (if i18n)
- Remove: billing, sharing, strategic allocation, banks

---

## 📋 Cleanup Execution Order

1. **Delete folders** (auth, supabase, support, onboarding)
2. **Delete pages** (Login, VerifyOTP, ForgotPassword, etc.)
3. **Delete contexts** (AuthContext, SupportContext, OnboardingContext)
4. **Remove dependencies** (package.json: @supabase/supabase-js)
5. **Update App.tsx** (remove providers, update routes)
6. **Update AppLayout.tsx** (remove auth logic, update nav)
7. **Simplify Settings.tsx** (theme only)
8. **Update .env** (remove Supabase, add MCP)
9. **Test cleanup** (`npm run dev` should start without errors)
10. **Create new structure** (services/, pages/, components/charts/, components/chat/)

---

## ⚠️ Breaking Changes

After cleanup, the following will NOT work until recreated:
- ❌ Login/authentication flow (removed)
- ❌ Protected routes (removed - all routes public for now)
- ❌ Supabase database queries (removed)
- ❌ Support ticket system (removed)
- ❌ Client onboarding wizard (removed)

**New functionality to implement**:
- ✅ MCP chat interface
- ✅ Portfolio dashboard
- ✅ Chart visualizations
- ✅ MCP tool calling

---

## ✅ Validation Checklist

After cleanup:
- [ ] `npm install` completes without Supabase errors
- [ ] `npm run dev` starts dev server
- [ ] No auth-related imports in codebase
- [ ] No Supabase imports in codebase
- [ ] Navigation menu shows: Chat, Dashboard, Analysis, Upload, Positions
- [ ] Theme switcher works (dark/light mode)
- [ ] 404 page works for unknown routes

---

**Ready to proceed?** This cleanup will remove ~40% of the current codebase and prepare for MCP integration.
