# Backend Changes Log

Ce fichier documente toutes les modifications backend pour faciliter la migration vers un backend custom (Node.js/NestJS).

---

## Authentification - Login

### Edge Functions créées
| Nom | Méthode | Description | Hook React Query |
|-----|---------|-------------|------------------|
| auth-login | POST | Connexion utilisateur | useLogin() |

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| POST | /api/auth/login | Connexion utilisateur |

### Schemas Zod créés dans resources/schemas/auth/
- `loginRequestSchema`: email, password
- `authResponseSchema`: user, session

---

## Authentification - Register

### Edge Functions créées
| Nom | Méthode | Description | Hook React Query |
|-----|---------|-------------|------------------|
| auth-register | POST | Inscription utilisateur | useRegister() |

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| POST | /api/auth/register | Inscription utilisateur |

---

## Authentification - Logout

### Edge Functions créées
| Nom | Méthode | Description | Hook React Query |
|-----|---------|-------------|------------------|
| auth-logout | POST | Déconnexion utilisateur | useLogout() |

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| POST | /api/auth/logout | Déconnexion utilisateur |

---

## Authentification - Reset Password

### Edge Functions créées
| Nom | Méthode | Description | Hook React Query |
|-----|---------|-------------|------------------|
| auth-reset-password | POST | Réinitialisation mot de passe | useResetPassword() |

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| POST | /api/auth/reset-password | Envoyer email de réinitialisation |

---

## Authentification - Verify OTP

### Note
La vérification OTP est actuellement simulée côté client (code fixe "123456").
Pour la migration, implémenter une vraie vérification SMS via Twilio ou autre.

### Routes API backend (pour migration future)
| Méthode | Path | Description |
|---------|------|-------------|
| POST | /api/auth/verify-otp | Vérifier code OTP |
| POST | /api/auth/send-otp | Envoyer code OTP par SMS |

---

## Onboarding - Liste

### Edge Functions créées
| Nom | Méthode | Description | Hook React Query |
|-----|---------|-------------|------------------|
| onboardings-list | GET | Liste des onboardings | useOnboardingsList() |

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| GET | /api/onboardings | Liste des onboardings de l'utilisateur |

### Schemas Zod créés dans resources/schemas/onboarding/
- `onboardingListResponseSchema`: { onboardings: Onboarding[], total: number }

---

## Onboarding - Détail

### Edge Functions créées
| Nom | Méthode | Description | Hook React Query |
|-----|---------|-------------|------------------|
| onboardings-get | GET | Détail d'un onboarding | useOnboardingDetail() |

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| GET | /api/onboardings/:id | Détail d'un onboarding |

### Schemas Zod créés
- `onboardingResponseSchema`: { onboarding: Onboarding }

---

## Onboarding - Création

### Edge Functions créées
| Nom | Méthode | Description | Hook React Query |
|-----|---------|-------------|------------------|
| onboardings-create | POST | Créer un onboarding | useCreateOnboarding() |

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| POST | /api/onboardings | Créer un nouvel onboarding |

### Schemas Zod créés
- `createOnboardingSchema`:
  - client: Client (sans id)
  - assetAllocation: AssetAllocation[]
  - banks: BankConnection[]
  - owner: string
  - targetDays: number

### Logique Backend
1. Valider les données entrantes
2. Générer l'ID client
3. Calculer targetEndAt depuis targetDays
4. Initialiser meetings, tasks, portfolioData, activityLog
5. Sauvegarder en base

---

## Onboarding - Mise à jour

### Edge Functions créées
| Nom | Méthode | Description | Hook React Query |
|-----|---------|-------------|------------------|
| onboardings-update | PATCH | Mettre à jour un onboarding | useUpdateOnboarding() |

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| PATCH | /api/onboardings/:id | Mise à jour partielle |

### Schemas Zod créés
- `updateOnboardingSchema`: Partial de onboardingSchema (sans id, createdAt)

---

## Onboarding - Suppression

### Edge Functions créées
| Nom | Méthode | Description | Hook React Query |
|-----|---------|-------------|------------------|
| onboardings-delete | DELETE | Supprimer un onboarding | useDeleteOnboarding() |

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| DELETE | /api/onboardings/:id | Supprimer un onboarding |

---

## Support Tickets - Liste

### Edge Functions créées
| Nom | Méthode | Description | Hook React Query |
|-----|---------|-------------|------------------|
| tickets-list | GET | Liste des tickets | useTicketsList() |

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| GET | /api/tickets | Liste des tickets support |

### Schemas Zod créés dans resources/schemas/support/
- `ticketListResponseSchema`: { tickets: SupportTicket[], total: number }

---

## Support Tickets - Détail

### Edge Functions créées
| Nom | Méthode | Description | Hook React Query |
|-----|---------|-------------|------------------|
| tickets-get | GET | Détail d'un ticket | useTicketDetail() |

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| GET | /api/tickets/:id | Détail d'un ticket |

---

## Support Tickets - Création

### Edge Functions créées
| Nom | Méthode | Description | Hook React Query |
|-----|---------|-------------|------------------|
| tickets-create | POST | Créer un ticket | useCreateTicket() |

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| POST | /api/tickets | Créer un ticket support |

### Schemas Zod créés
- `createTicketSchema`:
  - client: TicketClient (sans id)
  - onboardingId?: string
  - issueType: IssueType
  - comment: string
  - screenshot?: ScreenshotData
  - pageUrl: string
  - priority?: TicketPriority

### Logique Backend
1. Générer ticketNumber (TKT-XXXXX)
2. Calculer slaDeadline selon priority
3. Créer log initial "Ticket created"
4. Sauvegarder en base

---

## Support Tickets - Mise à jour Status

### Edge Functions créées
| Nom | Méthode | Description | Hook React Query |
|-----|---------|-------------|------------------|
| tickets-update | PATCH | Mettre à jour un ticket | useUpdateTicketStatus() |

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| PATCH | /api/tickets/:id/status | Changer le status |

### Schemas Zod créés
- `updateTicketStatusSchema`: { status, message? }

---

## Support Tickets - Assignation

### Hook React Query
- useAssignTicket()

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| PATCH | /api/tickets/:id/assign | Assigner à support/tech/csm |

### Schemas Zod créés
- `assignTicketSchema`: { support?, tech?, csm? }

---

## Support Tickets - Résolution

### Hook React Query
- useResolveTicket()

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| POST | /api/tickets/:id/resolve | Résoudre le ticket |

### Schemas Zod créés
- `resolveTicketSchema`: { resolutionMessage, notifyClient }

---

## Support Tickets - Priorité

### Hook React Query
- useUpdateTicketPriority()

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| PATCH | /api/tickets/:id/priority | Changer la priorité |

### Schemas Zod créés
- `updatePrioritySchema`: { priority }

---

## Support Tickets - Logs

### Hook React Query
- useAddTicketLog()

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| POST | /api/tickets/:id/logs | Ajouter une note/log |

### Schemas Zod créés
- `addTicketLogSchema`: { author, type, message }

---

## Settings - Profile

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| GET | /api/settings/profile | Récupérer le profil utilisateur |
| PATCH | /api/settings/profile | Mettre à jour le profil |
| POST | /api/settings/password | Changer le mot de passe |

### Schemas Zod créés dans resources/schemas/settings/
- `profileSchema`: id, userId, firstName, lastName, email, phone, avatarUrl, company, jobTitle
- `updateProfileSchema`: Partial de profileSchema
- `changePasswordSchema`: currentPassword, newPassword, confirmPassword

---

## Settings - Preferences

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| GET | /api/settings/preferences | Récupérer les préférences |
| PATCH | /api/settings/preferences | Mettre à jour les préférences |

### Schemas Zod créés
- `preferencesSchema`: theme, language, currency, dateFormat, notifications settings
- `updatePreferencesSchema`: Partial de preferencesSchema

---

## Settings - Bank Connections

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| GET | /api/settings/banks | Liste des connexions bancaires |
| POST | /api/settings/banks/connect | Connecter une banque |
| DELETE | /api/settings/banks/:id | Déconnecter une banque |
| PATCH | /api/settings/banks/:id/accounts | Activer/désactiver des comptes |
| POST | /api/settings/banks/:id/sync | Synchroniser une banque |

### Schemas Zod créés
- `bankConnectionDetailSchema`: id, bankName, status, accounts, lastSync
- `bankAccountSchema`: id, name, type, balance, currency, enabled
- `connectBankSchema`: bankId, credentials?
- `updateBankAccountsSchema`: accounts[]

---

## Settings - Billing

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| GET | /api/settings/billing | Récupérer infos facturation |
| POST | /api/settings/billing/subscribe | Souscrire à un plan |
| POST | /api/settings/billing/cancel | Annuler l'abonnement |
| GET | /api/settings/billing/invoices | Liste des factures |
| GET | /api/settings/billing/invoices/:id/pdf | Télécharger facture PDF |

### Schemas Zod créés
- `subscriptionSchema`: plan, billingCycle, status, amount
- `invoiceSchema`: id, number, date, amount, status
- `billingInfoSchema`: subscription, invoices, paymentMethod
- `updateSubscriptionSchema`: plan, billingCycle?
- `cancelSubscriptionSchema`: cancelAtPeriodEnd, reason?

---

## Récapitulatif des fichiers créés

### Schemas Zod (resources/)
- `resources/schemas/auth/auth.schema.ts`
- `resources/schemas/onboarding/onboarding.schema.ts`
- `resources/schemas/support/support.schema.ts`
- `resources/schemas/settings/settings.schema.ts`
- `resources/enums/index.ts`

### Edge Functions
- `supabase/functions/auth-login/index.ts`
- `supabase/functions/auth-register/index.ts`
- `supabase/functions/auth-logout/index.ts`
- `supabase/functions/auth-reset-password/index.ts`
- `supabase/functions/onboardings-list/index.ts`
- `supabase/functions/onboardings-get/index.ts`
- `supabase/functions/onboardings-create/index.ts`
- `supabase/functions/onboardings-update/index.ts`
- `supabase/functions/onboardings-delete/index.ts`
- `supabase/functions/tickets-list/index.ts`
- `supabase/functions/tickets-get/index.ts`
- `supabase/functions/tickets-create/index.ts`
- `supabase/functions/tickets-update/index.ts`
- `supabase/functions/settings-profile-get/index.ts`
- `supabase/functions/settings-profile-update/index.ts`
- `supabase/functions/settings-preferences-get/index.ts`
- `supabase/functions/settings-preferences-update/index.ts`

### Hooks React Query
- `src/hooks/queries/useAuth.ts`
- `src/hooks/queries/useOnboardings.ts`
- `src/hooks/queries/useTickets.ts`
- `src/hooks/queries/useSettings.ts`

---

## Tables de base de données (créées)

### Table: onboardings ✅
| Colonne | Type | Description |
|---------|------|-------------|
| id | uuid | Primary key |
| user_id | uuid | FK vers auth.users |
| client | jsonb | Données client |
| asset_allocation | jsonb | Allocation d'actifs |
| banks | jsonb | Connexions bancaires |
| owner | text | Responsable |
| meetings | jsonb | Liste des meetings |
| tasks | jsonb | Liste des tâches |
| portfolio_data | jsonb | Données portfolio par banque |
| activity_log | jsonb | Log d'activité |
| created_at | timestamptz | Date création |
| target_end_at | timestamptz | Date cible de fin |
| updated_at | timestamptz | Date mise à jour |

### Table: support_tickets ✅
| Colonne | Type | Description |
|---------|------|-------------|
| id | uuid | Primary key |
| user_id | uuid | FK vers auth.users |
| ticket_number | text | Numéro unique (TKT-XXXXX) |
| client | jsonb | Données client |
| onboarding_id | uuid | FK vers onboardings (optionnel) |
| issue_type | text | Type de problème |
| subject | text | Sujet |
| comment | text | Description |
| screenshot | jsonb | Capture d'écran + annotations |
| page_url | text | URL de la page |
| status | text | Status du ticket |
| priority | text | Priorité |
| assigned_support | text | Agent support assigné |
| assigned_tech | text | Agent tech assigné |
| assigned_csm | text | CSM assigné |
| created_at | timestamptz | Date création |
| sla_deadline | timestamptz | Deadline SLA |
| resolved_at | timestamptz | Date résolution |
| resolution_message | text | Message de résolution |
| logs | jsonb | Historique des actions |
| updated_at | timestamptz | Date mise à jour |

---

## RLS Policies (créées)

### onboardings
- Users can view their own onboardings
- Users can create their own onboardings
- Users can update their own onboardings
- Users can delete their own onboardings

### support_tickets
- Users can view their own tickets
- Users can create their own tickets
- Users can update their own tickets
- Users can delete their own tickets

---

## Prochaines étapes

1. ✅ Tables `onboardings` et `support_tickets` créées
2. ✅ RLS policies configurées
3. ✅ Contexts remplacés par les hooks React Query dans tous les composants
4. ✅ Edge Functions Settings créées (profile, preferences)
5. ✅ Module Auth complet (voir section ci-dessous)
6. ⏳ Créer les Edge Functions pour banks et billing

---

## Module Auth Complet (Phase 2)

### Tables créées
| Table | Description |
|-------|-------------|
| profiles | Profil utilisateur avec user_state, MFA, tentatives échouées |
| user_devices | Appareils connectés, trusted devices |
| auth_audit_log | Journal d'audit des événements auth |
| user_roles | Rôles utilisateur (admin, client, RM, support, compliance) |

### Enums créés
- `user_state`: created, email_pending, password_pending, active, 2fa_required, locked, suspended, deleted
- `app_role`: admin, client, relationship_manager, support, compliance

### Edge Functions créées/mises à jour
| Nom | Méthode | Description | Hook React Query |
|-----|---------|-------------|------------------|
| auth-login | POST | Login avec device tracking + account locking | useLogin() |
| auth-magic-link | POST | Envoi magic link email | useMagicLink() |
| auth-profile | GET/PATCH | Profil + rôles + devices + audit log | useAuthProfile(), useUpdateAuthProfile() |
| auth-devices | GET/PATCH | Gestion des appareils | useUserDevices(), useManageDevice() |

### Routes API backend (pour migration)
| Méthode | Path | Description |
|---------|------|-------------|
| POST | /api/auth/login | Login avec device tracking |
| POST | /api/auth/magic-link | Envoi magic link |
| GET | /api/auth/profile | Profil complet + rôles + devices |
| PATCH | /api/auth/profile | Mise à jour profil |
| GET | /api/auth/devices | Liste des appareils |
| PATCH | /api/auth/devices | Gérer un appareil (trust/untrust/remove) |

### Schemas Zod créés/mis à jour dans resources/schemas/auth/
- `UserStateEnum`, `AppRoleEnum`
- `magicLinkRequestSchema`, `setupMfaRequestSchema`, `passwordStrengthSchema`
- `authProfileSchema`, `deviceSchema`, `auditLogSchema`
- `mfaSetupResponseSchema`

### Fonctions DB créées
- `handle_new_user()` — auto-create profile on signup
- `handle_new_user_role()` — auto-assign 'client' role
- `check_and_lock_account()` — lock after 5 failed attempts
- `has_role()` — security definer pour vérifier les rôles

### Sécurité
- Account locking après 5 tentatives échouées
- Avertissement après 4 tentatives
- Audit log de tous les événements auth
- Device tracking
- RLS sur toutes les tables

---

## Corrections Mineures

### ProfilePersonalInfoCard
- ✅ Connecté au hook `useProfile()` pour la lecture des données
- ✅ Connecté au hook `useUpdateProfile()` pour la sauvegarde via mutation
- ✅ Suppression des données hardcodées (initialData)
- ✅ Utilisation de `react-hook-form` avec `zodResolver` et `updateProfileSchema`
- ✅ Gestion des états loading/error
- ✅ Affichage "Unsaved changes" basé sur `isDirty` du form

### Structure utils/
- ✅ Création du dossier `src/utils/`
- ✅ `src/utils/cn.ts` - Fonction `cn()` pour Tailwind (clsx + tailwind-merge)
- ✅ `src/utils/formatters.ts` - Fonctions de formatage:
  - `formatDate()`, `formatDateTime()`, `formatDateRelative()`, `formatDateISO()`
  - `formatCurrency()`, `formatCurrencyCompact()`
  - `formatNumber()`, `formatPercent()`, `formatCompactNumber()`
  - `formatPhoneNumber()`, `truncate()`, `capitalize()`, `formatInitials()`
- ✅ `src/utils/index.ts` - Exports centralisés

### Imports
- Note: `src/lib/utils.ts` est conservé pour compatibilité avec les composants existants
- Les nouveaux composants doivent importer depuis `@/utils/cn`

---

## Migration vers format paginé (data + meta)

### Changements de format de réponse

Les listes utilisent désormais le format standardisé:
```json
{
  "data": [...],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "totalPages": 8,
    "hasMore": true
  }
}
```

### Fichiers modifiés

#### Schemas Zod
- ✅ `resources/schemas/common/api.schema.ts` - Schemas de pagination communs
  - `paginationParamsSchema`: page, limit, sortBy, sortOrder
  - `paginationMetaSchema`: page, limit, total, totalPages, hasMore
  - `paginatedResponseSchema`: helper générique
  - `apiErrorSchema`, `messageResponseSchema`, `idResponseSchema`

- ✅ `resources/schemas/onboarding/onboarding.schema.ts`
  - Ajout `onboardingListParamsSchema` (extends paginationParams + status, search)
  - `onboardingListResponseSchema` → format `{ data, meta }` au lieu de `{ onboardings, total }`

- ✅ `resources/schemas/support/support.schema.ts`
  - Ajout `ticketListParamsSchema` (extends paginationParams + status[], priority[], search)
  - `ticketListResponseSchema` → format `{ data, meta }` au lieu de `{ tickets, total }`

#### Hooks React Query
- ✅ `src/hooks/queries/useOnboardings.ts`
  - Ajout `onboardingKeys.listWithParams(params)`
  - `useOnboardingsList(params?)` supporte les paramètres de pagination

- ✅ `src/hooks/queries/useTickets.ts`
  - Ajout `ticketKeys.listWithParams(params)`
  - `useTicketsList(params?)` supporte les paramètres de pagination

#### Edge Functions
- ✅ `supabase/functions/onboardings-list/index.ts`
  - Parse le body pour les params de pagination
  - Applique search, status filter, pagination SQL
  - Retourne format `{ data, meta }`

- ✅ `supabase/functions/tickets-list/index.ts`
  - Parse le body pour les params de pagination
  - Applique search, status[], priority[] filters, pagination SQL
  - Retourne format `{ data, meta }`

#### Pages
- ✅ `src/pages/Onboarding.tsx` - Utilise `data?.data` au lieu de `data?.onboardings`
- ✅ `src/pages/Support.tsx` - Utilise `data?.data` au lieu de `data?.tickets`

### Usage dans les composants

```typescript
// Avant
const { data } = useOnboardingsList();
const onboardings = data?.onboardings ?? [];

// Après
const { data } = useOnboardingsList({ page: 1, limit: 20 });
const onboardings = data?.data ?? [];
const { page, totalPages, hasMore } = data?.meta ?? {};
```
