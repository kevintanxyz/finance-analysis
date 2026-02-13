import { format, formatDistanceToNow, parseISO, isValid } from "date-fns";
import { fr } from "date-fns/locale";

// ============= DATE FORMATTERS =============

export function formatDate(date: string | Date, pattern = "dd/MM/yyyy"): string {
    const d = typeof date === "string" ? parseISO(date) : date;
    if (!isValid(d)) return "—";
    return format(d, pattern, { locale: fr });
}

export function formatDateTime(date: string | Date): string {
    return formatDate(date, "dd/MM/yyyy HH:mm");
}

export function formatDateRelative(date: string | Date): string {
    const d = typeof date === "string" ? parseISO(date) : date;
    if (!isValid(d)) return "—";
    return formatDistanceToNow(d, { addSuffix: true, locale: fr });
}

export function formatDateISO(date: Date): string {
    return format(date, "yyyy-MM-dd");
}

// ============= CURRENCY FORMATTERS =============

export function formatCurrency(
    amount: number,
    currency = "EUR",
    locale = "fr-FR"
): string {
    return new Intl.NumberFormat(locale, {
        style: "currency",
        currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(amount);
}

export function formatCurrencyCompact(
    amount: number,
    currency = "EUR",
    locale = "fr-FR"
): string {
    return new Intl.NumberFormat(locale, {
        style: "currency",
        currency,
        notation: "compact",
        minimumFractionDigits: 0,
        maximumFractionDigits: 1,
    }).format(amount);
}

// ============= NUMBER FORMATTERS =============

export function formatNumber(
    value: number,
    locale = "fr-FR",
    options?: Intl.NumberFormatOptions
): string {
    return new Intl.NumberFormat(locale, options).format(value);
}

export function formatPercent(
    value: number,
    decimals = 2,
    locale = "fr-FR"
): string {
    return new Intl.NumberFormat(locale, {
        style: "percent",
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    }).format(value / 100);
}

export function formatCompactNumber(value: number, locale = "fr-FR"): string {
    return new Intl.NumberFormat(locale, {
        notation: "compact",
        maximumFractionDigits: 1,
    }).format(value);
}

// ============= STRING FORMATTERS =============

export function formatPhoneNumber(phone: string): string {
    // Swiss format: +41 79 123 45 67
    const cleaned = phone.replace(/\D/g, "");
    if (cleaned.startsWith("41") && cleaned.length === 11) {
        return `+${cleaned.slice(0, 2)} ${cleaned.slice(2, 4)} ${cleaned.slice(4, 7)} ${cleaned.slice(7, 9)} ${cleaned.slice(9)}`;
    }
    return phone;
}

export function truncate(str: string, maxLength: number): string {
    if (str.length <= maxLength) return str;
    return `${str.slice(0, maxLength - 1)}…`;
}

export function capitalize(str: string): string {
    if (!str) return "";
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

export function formatInitials(firstName: string, lastName: string): string {
    return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
}
