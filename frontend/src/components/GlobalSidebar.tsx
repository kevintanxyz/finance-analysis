import { cn } from "@/lib/utils";
import logoVp from "@/assets/logoVp.svg";
import logoIcon from "@/assets/logoIcon.svg";
import { 
  Settings, 
  LayoutDashboard,
  PieChart,
  TrendingUp,
  ShieldAlert,
  Calculator,
  Layers,
  ArrowLeftRight,
  PlusCircle,
  Wallet,
  CreditCard,
} from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { useState } from "react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";


// Disabled nav items (greyed out)
const disabledNavItems = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "allocation", label: "Allocation", icon: PieChart },
  { id: "performance", label: "Performance", icon: TrendingUp },
  { id: "risque", label: "Risque", icon: ShieldAlert },
  { id: "cost-analysis", label: "Cost Analysis", icon: Calculator },
  { id: "add-asset", label: "Add an Asset", icon: PlusCircle },
  { id: "cash", label: "Cash", icon: Wallet },
  { id: "liabilities", label: "Liabilities", icon: CreditCard },
];

// Active nav items in main section
const activeNavItems = [
  { id: "positions", label: "Positions", icon: Layers, path: "/positions" },
  { id: "transactions", label: "Transactions", icon: ArrowLeftRight, path: "/transactions" },
];

// Bottom nav items (active)
const bottomNavItems = [
  { id: "settings", label: "Settings", icon: Settings, path: "/settings" },
];

export function GlobalSidebar() {
  const [expanded, setExpanded] = useState(false);

  return (
    <TooltipProvider delayDuration={100}>
      <aside 
        className={cn(
          "flex-shrink-0 bg-card border-r border-border flex flex-col py-6 transition-all duration-300 h-screen sticky top-0 overflow-hidden",
          expanded ? "w-48" : "w-16"
        )}
      >
        {/* App logo / brand - clickable to toggle */}
        <button
          onClick={() => setExpanded(!expanded)}
          className={cn(
            "flex items-center gap-3 mb-6 cursor-pointer hover:opacity-80 transition-opacity",
            expanded ? "px-4" : "justify-center"
          )}
        >
          <img src={expanded ? logoVp : logoIcon} alt="WealthPoint" className={cn("flex-shrink-0 transition-all duration-300", expanded ? "h-6" : "h-3.5")} />
        </button>

        {/* Navigation items */}
        <nav className={cn("flex flex-col gap-2 flex-1", expanded ? "px-3" : "items-center")}>
          {/* Active nav items */}
          {activeNavItems.map((item) => {
            const Icon = item.icon;
            
            return (
              <Tooltip key={item.id}>
                <TooltipTrigger asChild>
                  <NavLink
                    to={item.path}
                    className={cn(
                      "relative flex items-center gap-3 rounded text-muted-foreground hover:text-foreground hover:bg-sidebar-accent/50 transition-all duration-200",
                      expanded ? "px-3 py-2.5" : "w-10 h-10 justify-center"
                    )}
                    activeClassName="bg-sidebar-accent text-primary"
                  >
                    <Icon className="h-5 w-5 flex-shrink-0" />
                    {expanded && (
                      <span className="text-sm font-medium whitespace-nowrap">{item.label}</span>
                    )}
                  </NavLink>
                </TooltipTrigger>
                {!expanded && (
                  <TooltipContent side="right" className="bg-popover text-popover-foreground border border-border">
                    <p>{item.label}</p>
                  </TooltipContent>
                )}
              </Tooltip>
            );
          })}

          {/* Separator */}
          <div className={cn("h-px bg-border my-2", expanded ? "" : "w-8")} />

          {/* Disabled nav items */}
          {disabledNavItems.map((item) => {
            const Icon = item.icon;
            
            return (
              <div
                key={item.id}
                className={cn(
                  "relative flex items-center gap-3 rounded text-muted-foreground/40 cursor-not-allowed transition-all duration-200",
                  expanded ? "px-3 py-2.5" : "w-10 h-10 justify-center"
                )}
              >
                <Icon className="h-5 w-5 flex-shrink-0" />
                {expanded && (
                  <span className="text-sm font-medium whitespace-nowrap">{item.label}</span>
                )}
              </div>
            );
          })}
        </nav>

        {/* Bottom navigation */}
        <div className="mt-auto border-t border-border pt-4">
          <div className="flex items-center justify-center">
            {bottomNavItems.map((item) => {
              const Icon = item.icon;
              return (
                <Tooltip key={item.id}>
                  <TooltipTrigger asChild>
                    <NavLink
                      to={item.path}
                      className={cn(
                        "relative flex items-center justify-center rounded text-muted-foreground hover:text-foreground hover:bg-sidebar-accent/50 transition-all duration-200",
                        expanded ? "w-10 h-10" : "w-10 h-10"
                      )}
                      activeClassName="bg-sidebar-accent text-primary"
                    >
                      <Icon className="h-5 w-5" />
                    </NavLink>
                  </TooltipTrigger>
                  {!expanded && (
                    <TooltipContent side="right" className="bg-popover text-popover-foreground border border-border">
                      <p>{item.label}</p>
                    </TooltipContent>
                  )}
                  {expanded && (
                    <TooltipContent side="top" className="bg-popover text-popover-foreground border border-border">
                      <p>{item.label}</p>
                    </TooltipContent>
                  )}
                </Tooltip>
              );
            })}
          </div>
        </div>

      </aside>
    </TooltipProvider>
  );
}