import { useState } from "react";
import { SettingsCard } from "./SettingsCard";
import { FintechToggle } from "./FintechToggle";

interface NotificationPreference {
  id: string;
  title: string;
  description?: string;
  email: boolean;
  push: boolean;
  sms: boolean;
}

const initialPreferences: NotificationPreference[] = [
  {
    id: "mentions",
    title: "Mentions",
    description: "Notify when another user mentions you in a comment",
    email: true,
    push: true,
    sms: false,
  },
  {
    id: "comments",
    title: "Comments",
    description: "Notify when another user comments your item.",
    email: true,
    push: false,
    sms: false,
  },
  {
    id: "follows",
    title: "Follows",
    description: "Notify when another user follows you.",
    email: true,
    push: false,
    sms: false,
  },
  {
    id: "new-device",
    title: "Log in from a new device",
    email: true,
    push: true,
    sms: true,
  },
];

export function NotificationsCard() {
  const [preferences, setPreferences] = useState<NotificationPreference[]>(initialPreferences);

  const updatePreference = (
    id: string,
    channel: "email" | "push" | "sms",
    value: boolean
  ) => {
    setPreferences((prev) =>
      prev.map((pref) =>
        pref.id === id ? { ...pref, [channel]: value } : pref
      )
    );
  };

  return (
    <SettingsCard
      title="Notifications"
      description="Choose how you receive notifications. These notification settings apply to the things you're watching."
    >
      {/* Desktop Table View */}
      <div className="hidden md:block mt-6">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left text-sm font-medium text-muted-foreground pb-4 w-1/2">
                Activity
              </th>
              <th className="text-center text-sm font-medium text-muted-foreground pb-4">
                Email
              </th>
              <th className="text-center text-sm font-medium text-muted-foreground pb-4">
                Push
              </th>
              <th className="text-center text-sm font-medium text-muted-foreground pb-4">
                SMS
              </th>
            </tr>
          </thead>
          <tbody>
            {preferences.map((pref, index) => (
              <tr
                key={pref.id}
                className={`group transition-colors duration-200 hover:bg-muted/30 ${
                  index !== preferences.length - 1 ? "border-b border-border" : ""
                }`}
              >
                <td className="py-5">
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-foreground">
                      {pref.title}
                    </p>
                    {pref.description && (
                      <p className="text-xs text-muted-foreground">
                        {pref.description}
                      </p>
                    )}
                  </div>
                </td>
                <td className="py-5 text-center">
                  <div className="flex justify-center">
                    <FintechToggle
                      checked={pref.email}
                      onChange={(checked) =>
                        updatePreference(pref.id, "email", checked)
                      }
                    />
                  </div>
                </td>
                <td className="py-5 text-center">
                  <div className="flex justify-center">
                    <FintechToggle
                      checked={pref.push}
                      onChange={(checked) =>
                        updatePreference(pref.id, "push", checked)
                      }
                    />
                  </div>
                </td>
                <td className="py-5 text-center">
                  <div className="flex justify-center">
                    <FintechToggle
                      checked={pref.sms}
                      onChange={(checked) =>
                        updatePreference(pref.id, "sms", checked)
                      }
                    />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Stacked View */}
      <div className="md:hidden mt-6 space-y-4">
        {preferences.map((pref, index) => (
          <div
            key={pref.id}
            className={`pb-4 ${
              index !== preferences.length - 1 ? "border-b border-border" : ""
            }`}
          >
            <div className="mb-3">
              <p className="text-sm font-medium text-foreground">{pref.title}</p>
              {pref.description && (
                <p className="text-xs text-muted-foreground mt-1">
                  {pref.description}
                </p>
              )}
            </div>
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">Email</span>
                <FintechToggle
                  checked={pref.email}
                  onChange={(checked) =>
                    updatePreference(pref.id, "email", checked)
                  }
                />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">Push</span>
                <FintechToggle
                  checked={pref.push}
                  onChange={(checked) =>
                    updatePreference(pref.id, "push", checked)
                  }
                />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">SMS</span>
                <FintechToggle
                  checked={pref.sms}
                  onChange={(checked) =>
                    updatePreference(pref.id, "sms", checked)
                  }
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </SettingsCard>
  );
}
