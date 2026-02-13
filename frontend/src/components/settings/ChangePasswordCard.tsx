import { useState } from "react";
import { SettingsCard } from "./SettingsCard";
import { FintechButton } from "./FintechButton";

export function ChangePasswordCard() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const passwordsMatch = newPassword === confirmPassword;
  const showMismatchError = confirmPassword.length > 0 && !passwordsMatch;
  const isFormValid =
    currentPassword.length > 0 &&
    newPassword.length >= 6 &&
    confirmPassword.length > 0 &&
    passwordsMatch;

  const requirements = [
    "One special character",
    "Min 6 characters",
    "One number (2 are recommended)",
    "Change it often",
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isFormValid) {
      // Placeholder for password update logic
      console.log("Password update submitted");
    }
  };

  const inputClasses =
    "w-full bg-background border border-border rounded-xl px-4 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors";

  return (
    <SettingsCard title="Change Password">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-4">
          <div>
            <label
              htmlFor="current-password"
              className="block text-sm font-medium text-foreground mb-2"
            >
              Current Password
            </label>
            <input
              id="current-password"
              type="password"
              placeholder="Current Password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className={inputClasses}
            />
          </div>

          <div>
            <label
              htmlFor="new-password"
              className="block text-sm font-medium text-foreground mb-2"
            >
              New Password
            </label>
            <input
              id="new-password"
              type="password"
              placeholder="New Password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className={inputClasses}
            />
          </div>

          <div>
            <label
              htmlFor="confirm-password"
              className="block text-sm font-medium text-foreground mb-2"
            >
              Confirm New Password
            </label>
            <input
              id="confirm-password"
              type="password"
              placeholder="Confirm Password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className={`${inputClasses} ${
                showMismatchError ? "border-destructive focus:border-destructive focus:ring-destructive" : ""
              }`}
            />
            {showMismatchError && (
              <p className="mt-2 text-sm text-destructive">
                Passwords do not match
              </p>
            )}
          </div>
        </div>

        <div className="pt-4 border-t border-border">
          <h4 className="text-sm font-medium text-foreground mb-2">
            Password requirements
          </h4>
          <p className="text-xs text-muted-foreground mb-3">
            Please follow this guide for a strong password
          </p>
          <ul className="space-y-1.5">
            {requirements.map((req, index) => (
              <li
                key={index}
                className="text-xs text-muted-foreground flex items-center gap-2"
              >
                <span className="w-1 h-1 rounded-full bg-muted-foreground" />
                {req}
              </li>
            ))}
          </ul>
        </div>

        <div className="flex justify-end pt-2">
          <FintechButton
            type="submit"
            variant="primary"
            disabled={!isFormValid}
            className="px-6 py-2.5"
          >
            UPDATE PASSWORD
          </FintechButton>
        </div>
      </form>
    </SettingsCard>
  );
}
