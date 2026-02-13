import React, { useMemo } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { SettingsCard } from "./SettingsCard";
import { FintechButton } from "./FintechButton";
import { StatusBadge } from "./StatusBadge";
import { toast } from "@/hooks/use-toast";
import { cn } from "@/utils/cn";
import { useProfile, useUpdateProfile } from "@/hooks/queries/useSettings";
import { updateProfileSchema, type UpdateProfileRequest } from "resources/schemas/settings";
import { Skeleton } from "@/components/ui/skeleton";

export function ProfilePersonalInfoCard() {
    const { data: profile, isLoading, error } = useProfile();
    const updateProfileMutation = useUpdateProfile();

    const {
        register,
        handleSubmit,
        formState: { errors, isDirty },
        reset,
    } = useForm<UpdateProfileRequest>({
        resolver: zodResolver(updateProfileSchema),
        values: profile
            ? {
                  firstName: profile.firstName,
                  lastName: profile.lastName,
                  phone: profile.phone ?? "",
                  company: profile.company ?? "",
                  jobTitle: profile.jobTitle ?? "",
              }
            : undefined,
    });

    const onSubmit = (data: UpdateProfileRequest) => {
        updateProfileMutation.mutate(data, {
            onSuccess: (updatedProfile) => {
                reset({
                    firstName: updatedProfile.firstName,
                    lastName: updatedProfile.lastName,
                    phone: updatedProfile.phone ?? "",
                    company: updatedProfile.company ?? "",
                    jobTitle: updatedProfile.jobTitle ?? "",
                });
                toast({
                    title: "Profil mis à jour",
                    description: "Vos modifications ont été enregistrées.",
                });
            },
            onError: (err) => {
                toast({
                    title: "Erreur",
                    description: err.message,
                    variant: "destructive",
                });
            },
        });
    };

    const inputClasses =
        "w-full bg-input border border-border rounded-lg px-4 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all";
    const labelClasses = "block text-sm font-medium text-foreground mb-2";
    const errorClasses = "text-destructive text-xs mt-1";

    if (error) {
        return (
            <SettingsCard title="Profile information" description="Manage your personal details.">
                <div className="text-destructive">Erreur lors du chargement du profil.</div>
            </SettingsCard>
        );
    }

    return (
        <SettingsCard title="Profile information" description="Manage your personal details.">
            {isLoading ? (
                <div className="space-y-6">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <Skeleton className="h-12" />
                        <Skeleton className="h-12" />
                    </div>
                    <Skeleton className="h-12" />
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <Skeleton className="h-12" />
                        <Skeleton className="h-12" />
                    </div>
                </div>
            ) : (
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
                    {/* Identity Section */}
                    <div className="space-y-4">
                        <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                            Identity
                        </h4>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div>
                                <label className={labelClasses}>First name</label>
                                <input
                                    type="text"
                                    {...register("firstName")}
                                    placeholder="First name"
                                    className={inputClasses}
                                />
                                {errors.firstName && (
                                    <p className={errorClasses}>{errors.firstName.message}</p>
                                )}
                            </div>
                            <div>
                                <label className={labelClasses}>Last name</label>
                                <input
                                    type="text"
                                    {...register("lastName")}
                                    placeholder="Last name"
                                    className={inputClasses}
                                />
                                {errors.lastName && (
                                    <p className={errorClasses}>{errors.lastName.message}</p>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Contact Section */}
                    <div className="space-y-4 pt-4 border-t border-border">
                        <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                            Contact
                        </h4>
                        <div>
                            <label className={labelClasses}>Email</label>
                            <div className="flex flex-col sm:flex-row gap-3">
                                <div className="flex-1 relative">
                                    <input
                                        type="email"
                                        value={profile?.email ?? ""}
                                        disabled
                                        className={cn(inputClasses, "opacity-60 cursor-not-allowed pr-24")}
                                    />
                                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                                        <StatusBadge status="success">Verified</StatusBadge>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div>
                            <label className={labelClasses}>Phone number</label>
                            <input
                                type="tel"
                                {...register("phone")}
                                placeholder="+41 79 123 45 67"
                                className={inputClasses}
                            />
                            {errors.phone && <p className={errorClasses}>{errors.phone.message}</p>}
                            <p className="text-xs text-muted-foreground mt-1">
                                Used for two-factor authentication
                            </p>
                        </div>
                    </div>

                    {/* Professional Section */}
                    <div className="space-y-4 pt-4 border-t border-border">
                        <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                            Professional
                        </h4>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div>
                                <label className={labelClasses}>Company</label>
                                <input
                                    type="text"
                                    {...register("company")}
                                    placeholder="Company name"
                                    className={inputClasses}
                                />
                            </div>
                            <div>
                                <label className={labelClasses}>Job title</label>
                                <input
                                    type="text"
                                    {...register("jobTitle")}
                                    placeholder="Your role"
                                    className={inputClasses}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Save Section */}
                    <div className="flex items-center justify-between pt-4 border-t border-border">
                        <div>
                            {isDirty && (
                                <span className="text-sm text-accent animate-pulse">
                                    Unsaved changes
                                </span>
                            )}
                        </div>
                        <FintechButton
                            type="submit"
                            variant="primary"
                            disabled={!isDirty || updateProfileMutation.isPending}
                            className="px-6 py-2.5"
                        >
                            {updateProfileMutation.isPending ? "Saving..." : "Save changes"}
                        </FintechButton>
                    </div>
                </form>
            )}
        </SettingsCard>
    );
}
