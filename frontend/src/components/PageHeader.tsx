import { SettingsHeader } from "@/components/settings/SettingsHeader";

interface PageHeaderProps {
  title: string;
}

export function PageHeader({ title }: PageHeaderProps) {
  return (
    <header className="flex items-center justify-between px-6 md:px-8 py-4 border-b border-border">
      <h1 className="text-2xl font-semibold text-foreground">{title}</h1>
      <SettingsHeader />
    </header>
  );
}
