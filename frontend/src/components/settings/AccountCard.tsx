import { cn } from "@/lib/utils";
import { MessageCircle } from "lucide-react";

interface Account {
  id: string;
  name: string;
  logo?: string;
  logoText?: string;
  lastSync?: string;
  status: "synced" | "syncing" | "consolidating";
}

const accounts: Account[] = [
  { id: "1", name: "BCVS", status: "syncing" },
  { id: "2", name: "Rothschild & co", lastSync: "Fri. 12 Dec. 15:04", status: "synced" },
  { id: "3", name: "Degiro", logoText: "DEGIRO", status: "consolidating" },
  { id: "4", name: "UBS", logoText: "UBS", status: "synced", lastSync: "Fri. 12 Dec. 15:04" },
  { id: "5", name: "BCF", status: "synced", lastSync: "Fri. 12 Dec. 15:04" },
];

function getStatusText(status: Account["status"]) {
  switch (status) {
    case "synced":
      return "Synced";
    case "syncing":
      return "Syncing in progress";
    case "consolidating":
      return "Portfolio Consolidating";
  }
}

export function AccountCard() {
  return (
    <div className="flex-1">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-5 h-5 rounded-full border border-primary flex items-center justify-center">
          <div className="w-2 h-2 rounded-full bg-primary" />
        </div>
        <h2 className="text-lg font-medium text-foreground">Accounts</h2>
      </div>
      
      <div className="bg-card rounded-2xl border border-border overflow-hidden">
        {accounts.map((account, index) => (
          <div
            key={account.id}
            className={cn(
              "flex items-center justify-between px-6 py-5",
              index !== accounts.length - 1 && "border-b border-border"
            )}
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-foreground rounded-full flex items-center justify-center overflow-hidden">
                {account.logoText ? (
                  <span className="text-xs font-bold text-background">{account.logoText}</span>
                ) : (
                  <span className="text-lg font-semibold text-muted-foreground">
                    {account.name.charAt(0)}
                  </span>
                )}
              </div>
              <span className="text-foreground font-medium">{account.name}</span>
            </div>
            
            <div className="flex items-center gap-3">
              <div className="text-right">
                {account.lastSync && (
                  <p className="text-sm text-muted-foreground">
                    Last sync : {account.lastSync}
                  </p>
                )}
                <p className="text-sm text-muted-foreground">
                  Status : {getStatusText(account.status)}
                </p>
              </div>
              {account.status === "consolidating" && (
                <button className="w-10 h-10 rounded-full border border-border flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors">
                  <MessageCircle className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
