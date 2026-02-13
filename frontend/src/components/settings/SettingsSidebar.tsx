import { cn } from "@/lib/utils";
import { User, Building2, BarChart3, Share2, Sliders, Settings, SlidersHorizontal, Shield, Bell, CreditCard, Eye } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface MenuItem {
  id: string;
  label: string;
  icon: LucideIcon;
  disabled?: boolean;
}

interface MenuSection {
  title: string;
  items: MenuItem[];
}

const menuSections: MenuSection[] = [
  {
    title: "Account",
    items: [
      { id: "profile", label: "Profile", icon: User },
      { id: "accounts", label: "Banks & Accounts", icon: Building2 },
      { id: "sharing", label: "Sharing & Access", icon: Eye },
      { id: "risk-analytics", label: "Risk analytics", icon: BarChart3, disabled: true },
      { id: "strategic-allocation", label: "Strategic Asset Allocation", icon: Sliders },
    ],
  },
  {
    title: "Settings",
    items: [
      { id: "preferences", label: "Preferences", icon: SlidersHorizontal },
      { id: "security", label: "Security", icon: Shield },
      { id: "notifications", label: "Notifications", icon: Bell },
      { id: "billing", label: "Billing", icon: CreditCard },
    ],
  },
];

interface SettingsSidebarProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
}

export function SettingsSidebar({
  activeSection,
  onSectionChange,
}: SettingsSidebarProps) {
  return (
    <aside className="w-64 flex-shrink-0 space-y-4">
      {menuSections.map((section) => (
        <div 
          key={section.title} 
          className="bg-card rounded-2xl border border-border overflow-hidden"
        >
          {/* Section header */}
          <div className="px-5 py-4 border-b border-border">
            <h2 className="text-sm font-medium text-muted-foreground">
              {section.title}
            </h2>
          </div>
          
          {/* Menu items */}
          <nav className="p-3">
            <ul className="space-y-1">
              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive = activeSection === item.id;
                const isDisabled = item.disabled;
                return (
                  <li key={item.id}>
                    <button
                      onClick={() => !isDisabled && onSectionChange(item.id)}
                      disabled={isDisabled}
                      className={cn(
                        "w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm transition-all duration-200 text-left",
                        isActive
                          ? "bg-sidebar-accent text-primary font-medium"
                          : isDisabled
                            ? "text-muted-foreground/40 cursor-not-allowed"
                            : "text-muted-foreground hover:text-foreground hover:bg-sidebar-accent/50"
                      )}
                    >
                      <Icon className={cn("h-4 w-4", isActive && "text-primary", isDisabled && "opacity-40")} />
                      {item.label}
                    </button>
                  </li>
                );
              })}
            </ul>
          </nav>
        </div>
      ))}
    </aside>
  );
}
