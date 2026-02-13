import React, { createContext, useContext, useEffect, useState } from "react";

export type ThemeMode = "classic" | "premium" | "light";

interface ThemeContextType {
    theme: ThemeMode;
    setTheme: (theme: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const THEME_STORAGE_KEY = "fintech-theme-mode";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
    const [theme, setThemeState] = useState<ThemeMode>(() => {
        if (typeof window !== "undefined") {
            const stored = localStorage.getItem(THEME_STORAGE_KEY);
            if (stored === "classic" || stored === "premium" || stored === "light") {
                return stored;
            }
        }
        return "premium"; // Default to the new premium theme
    });

    useEffect(() => {
        // Save to localStorage
        localStorage.setItem(THEME_STORAGE_KEY, theme);

        // Apply theme class to document
        const root = document.documentElement;
        root.classList.remove("theme-classic", "theme-premium", "theme-light");
        root.classList.add(`theme-${theme}`);
    }, [theme]);

    const setTheme = (newTheme: ThemeMode) => {
        setThemeState(newTheme);
    };

    return (
        <ThemeContext.Provider value={{ theme, setTheme }}>
            {children}
        </ThemeContext.Provider>
    );
}

export function useTheme() {
    const context = useContext(ThemeContext);
    if (context === undefined) {
        throw new Error("useTheme must be used within a ThemeProvider");
    }
    return context;
}
