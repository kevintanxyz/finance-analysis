import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FintechButton } from "../FintechButton";
import { ShareStatusBadge } from "./ShareStatusBadge";
import { ShareViewModal } from "./ShareViewModal";
import { Eye, Share2, Users } from "lucide-react";
import { cn } from "@/lib/utils";
import type { SharedUser } from "./types";
import { MOCK_SHARED_USERS, VIEW_TYPE_LABELS } from "./types";

export function SharingAccessPage() {
  const [sharedUsers, setSharedUsers] = useState<SharedUser[]>(MOCK_SHARED_USERS);
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);

  const handleRevoke = (userId: string) => {
    setSharedUsers((prev) =>
      prev.map((user) =>
        user.id === userId ? { ...user, status: "revoked" as const } : user
      )
    );
  };

  const hasSharedUsers = sharedUsers.length > 0;

  return (
    <div className="flex-1 space-y-6 max-w-[1100px]">
      {/* Top bar */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Shared views</h1>
          <p className="text-muted-foreground mt-1">
            Manage who can see parts of your financial data.
          </p>
        </div>
        <FintechButton variant="primary" onClick={() => setIsShareModalOpen(true)}>
          <Share2 className="w-4 h-4 mr-2" />
          Share a view
        </FintechButton>
      </div>

      {/* Shared users card */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-lg font-medium">Active shares</CardTitle>
        </CardHeader>
        <CardContent>
          {hasSharedUsers ? (
            <>
              {/* Desktop Table */}
              <div className="hidden md:block overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                        Name
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                        Email
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                        View type
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                        Accounts shared
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                        Status
                      </th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {sharedUsers.map((user, index) => (
                      <tr
                        key={user.id}
                        className={cn(
                          "transition-colors hover:bg-muted/30",
                          index !== sharedUsers.length - 1 && "border-b border-border/50"
                        )}
                      >
                        <td className="py-4 px-4 text-sm font-medium text-foreground">
                          {user.name}
                        </td>
                        <td className="py-4 px-4 text-sm text-muted-foreground">
                          {user.email}
                        </td>
                        <td className="py-4 px-4 text-sm text-foreground">
                          {VIEW_TYPE_LABELS[user.viewType].title}
                        </td>
                        <td className="py-4 px-4 text-sm text-foreground">
                          {user.accountsShared} accounts
                        </td>
                        <td className="py-4 px-4">
                          <ShareStatusBadge status={user.status} />
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex items-center justify-end gap-2">
                            {user.status !== "revoked" && (
                              <>
                                <FintechButton variant="outline" className="text-xs py-1.5 px-3">
                                  Edit
                                </FintechButton>
                                {user.status === "pending" && (
                                  <FintechButton variant="outline" className="text-xs py-1.5 px-3">
                                    Resend
                                  </FintechButton>
                                )}
                                <button
                                  onClick={() => handleRevoke(user.id)}
                                  className="text-xs py-1.5 px-3 rounded-full border border-destructive text-destructive hover:bg-destructive/10 transition-colors"
                                >
                                  Revoke
                                </button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Mobile Cards */}
              <div className="md:hidden space-y-4">
                {sharedUsers.map((user) => (
                  <div
                    key={user.id}
                    className="p-4 rounded-lg bg-secondary/50 space-y-3"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium text-foreground">{user.name}</p>
                        <p className="text-sm text-muted-foreground">{user.email}</p>
                      </div>
                      <ShareStatusBadge status={user.status} />
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">
                        {VIEW_TYPE_LABELS[user.viewType].title}
                      </span>
                      <span className="text-foreground">
                        {user.accountsShared} accounts
                      </span>
                    </div>
                    {user.status !== "revoked" && (
                      <div className="flex items-center gap-2 pt-2 border-t border-border">
                        <FintechButton variant="outline" className="flex-1 text-xs py-2">
                          Edit
                        </FintechButton>
                        {user.status === "pending" && (
                          <FintechButton variant="outline" className="flex-1 text-xs py-2">
                            Resend
                          </FintechButton>
                        )}
                        <button
                          onClick={() => handleRevoke(user.id)}
                          className="flex-1 text-xs py-2 rounded-full border border-destructive text-destructive hover:bg-destructive/10 transition-colors"
                        >
                          Revoke
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </>
          ) : (
            /* Empty state */
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
                <Users className="w-8 h-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-medium text-foreground mb-2">
                No shared views yet
              </h3>
              <p className="text-muted-foreground mb-6 max-w-sm">
                Share parts of your financial data securely with advisors, family members, or
                anyone you trust.
              </p>
              <FintechButton variant="primary" onClick={() => setIsShareModalOpen(true)}>
                <Share2 className="w-4 h-4 mr-2" />
                Share your first view
              </FintechButton>
            </div>
          )}
        </CardContent>
      </Card>

      <ShareViewModal isOpen={isShareModalOpen} onClose={() => setIsShareModalOpen(false)} />
    </div>
  );
}
