import { useState } from "react";
import { SettingsCard } from "./SettingsCard";
import { StatusBadge } from "./StatusBadge";
import { FintechButton } from "./FintechButton";
import { FintechToggle } from "./FintechToggle";
import { useToast } from "@/hooks/use-toast";
import { ShieldCheck, Fingerprint, Smartphone, Key, Clock, Badge } from "lucide-react";

interface SecurityMethod {
	id: string;
	label: string;
	description: string;
	icon: React.ElementType;
	enabled: boolean;
	lastUsed?: string;
	mandatory?: boolean;
	recommended?: boolean;
}

export function SecurityAuthCard() {
	const { toast } = useToast();

	const [methods, setMethods] = useState<SecurityMethod[]>([
		{
			id: "otp-email",
			label: "OTP par email",
			description: "Code de vérification envoyé par email à chaque connexion",
			icon: ShieldCheck,
			enabled: true,
			lastUsed: "Aujourd'hui, 09:42",
			mandatory: true,
		},
		{
			id: "otp-sms",
			label: "OTP par SMS",
			description: "Code de vérification envoyé par SMS",
			icon: Smartphone,
			enabled: false,
			lastUsed: undefined,
		},
		{
			id: "passkey",
			label: "Passkey",
			description: "Connexion biométrique via Face ID, Touch ID ou clé de sécurité",
			icon: Fingerprint,
			enabled: false,
			recommended: true,
		},
		{
			id: "security-key",
			label: "Clé de sécurité physique",
			description: "Authentification par clé USB FIDO2 / YubiKey",
			icon: Key,
			enabled: false,
		},
	]);

	const toggleMethod = (id: string) => {
		setMethods((prev) =>
			prev.map((m) => {
				if (m.id === id) {
					if (m.mandatory) {
						toast({
							title: "Non modifiable",
							description: "Cette méthode est obligatoire pour votre rôle.",
							variant: "destructive",
						});
						return m;
					}
					const newEnabled = !m.enabled;
					toast({
						title: newEnabled ? "Méthode activée" : "Méthode désactivée",
						description: `${m.label} a été ${newEnabled ? "activé" : "désactivé"}.`,
					});
					return { ...m, enabled: newEnabled, lastUsed: newEnabled ? m.lastUsed : undefined };
				}
				return m;
			}),
		);
	};

	const activeCount = methods.filter((m) => m.enabled).length;

	return (
		<SettingsCard
			title="Sécurité & Authentification"
			description="Gérez vos méthodes de vérification pour sécuriser votre compte."
			rightElement={
				<StatusBadge status={activeCount > 0 ? "success" : "disabled"}>
					{activeCount} ACTIVE{activeCount > 1 ? "S" : ""}
				</StatusBadge>
			}
		>
			<div className="divide-y divide-border">
				{methods.map((method) => {
					const Icon = method.icon;
					return (
						<div
							key={method.id}
							className="flex items-start gap-4 py-4 first:pt-0 last:pb-0"
						>
							{/* Icon */}
							<div className="h-9 w-9 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
								<Icon className="h-4 w-4 text-primary" />
							</div>

							{/* Info */}
							<div className="flex-1 min-w-0">
								<div className="flex items-center gap-2">
									<span className="text-foreground font-medium text-sm">{method.label}</span>
									{method.mandatory && (
										<span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary uppercase tracking-wider">
											Obligatoire
										</span>
									)}
									{method.recommended && !method.enabled && (
										<span className="inline-flex items-center rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-500 uppercase tracking-wider">
											Recommandé
										</span>
									)}
								</div>
								<p className="text-muted-foreground text-xs mt-0.5">{method.description}</p>
								{method.enabled && method.lastUsed && (
									<div className="flex items-center gap-1 mt-1.5 text-muted-foreground/60">
										<Clock className="h-3 w-3" />
										<span className="text-[10px]">Dernière utilisation : {method.lastUsed}</span>
									</div>
								)}
							</div>

							{/* Toggle */}
							<div className="flex-shrink-0 pt-1">
								<FintechToggle
									checked={method.enabled}
									onChange={() => toggleMethod(method.id)}
									disabled={method.mandatory}
								/>
							</div>
						</div>
					);
				})}
			</div>
		</SettingsCard>
	);
}
