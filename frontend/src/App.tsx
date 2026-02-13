import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppLayout } from "@/components/AppLayout";
import { ThemeProvider } from "@/contexts/ThemeContext";
import Chat from "./pages/Chat";
import Dashboard from "./pages/Dashboard";
import Settings from "./pages/Settings";
import Positions from "./pages/Positions";
import Transactions from "./pages/Transactions";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <Routes>
              {/* Main routes */}
              <Route
                path="/"
                element={
                  <AppLayout>
                    <Chat />
                  </AppLayout>
                }
              />
              <Route
                path="/chat"
                element={
                  <AppLayout>
                    <Chat />
                  </AppLayout>
                }
              />
              <Route
                path="/dashboard"
                element={
                  <AppLayout>
                    <Dashboard />
                  </AppLayout>
                }
              />
              <Route
                path="/positions"
                element={
                  <AppLayout>
                    <Positions />
                  </AppLayout>
                }
              />
              <Route
                path="/transactions"
                element={
                  <AppLayout>
                    <Transactions />
                  </AppLayout>
                }
              />
              <Route
                path="/settings"
                element={
                  <AppLayout>
                    <Settings />
                  </AppLayout>
                }
              />

              {/* 404 */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
