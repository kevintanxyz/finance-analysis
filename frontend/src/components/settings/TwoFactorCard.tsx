import { useState } from "react";
import { SettingsCard } from "./SettingsCard";
import { StatusBadge } from "./StatusBadge";
import { FintechButton } from "./FintechButton";

interface TwoFactorMethod {
  id: string;
  label: string;
  value: string;
  buttonText: string;
}

export function TwoFactorCard() {
  const [isEnabled] = useState(true);

  const methods: TwoFactorMethod[] = [
    {
      id: "security-keys",
      label: "Security keys",
      value: "No Security keys",
      buttonText: "ADD",
    },
    {
      id: "sms",
      label: "SMS number",
      value: "+41 79 123 45 67",
      buttonText: "EDIT",
    },
    {
      id: "authenticator",
      label: "Authenticator app",
      value: "Not Configured",
      buttonText: "SET UP",
    },
  ];

  return (
    <SettingsCard
      title="Two-factor authentication"
      description={
        !isEnabled
          ? "Protect your account by enabling two-factor authentication."
          : undefined
      }
      rightElement={
        <StatusBadge status={isEnabled ? "success" : "disabled"}>
          {isEnabled ? "ENABLED" : "DISABLED"}
        </StatusBadge>
      }
    >
      <div className="divide-y divide-border">
        {methods.map((method) => (
          <div
            key={method.id}
            className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 py-4 first:pt-0 last:pb-0"
          >
            <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-6 flex-1">
              <span className="text-foreground font-medium min-w-[140px]">
                {method.label}
              </span>
              <span className="text-muted-foreground text-sm">
                {method.value}
              </span>
            </div>
            <FintechButton
              variant="outline"
              className="self-end sm:self-auto text-xs px-4 py-2"
            >
              {method.buttonText}
            </FintechButton>
          </div>
        ))}
      </div>
    </SettingsCard>
  );
}
