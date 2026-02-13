import { PreferencesPage } from "@/components/settings/preferences/PreferencesPage";

export default function Settings() {
  return (
    <div className="container mx-auto py-6">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">
            Manage your application preferences
          </p>
        </div>

        <PreferencesPage />
      </div>
    </div>
  );
}
