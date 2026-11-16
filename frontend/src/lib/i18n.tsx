"use client";

import { createContext, useContext, useEffect, useMemo, useState, ReactNode } from "react";
import { API, api, getStoredLang, setStoredLang } from "./api";
import { dictionaries, Lang, TKey } from "../i18n/dictionaries";

interface LangContextValue {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: TKey) => string;
}

const LangContext = createContext<LangContextValue | null>(null);

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");
  const [systemDefault, setSystemDefault] = useState<Lang>("en");
  const [userPref, setUserPref] = useState<string | null>(null);

  // Resolve language: stored choice -> user preference -> system default -> en.
  useEffect(() => {
    (async () => {
      try {
        const sys = await api<{ default: { code: string } | null }>(
          API.systemAdmin, "/languages/public", { auth: false });
        if (sys.default?.code) setSystemDefault(sys.default.code as Lang);
      } catch { /* keep fallback */ }
      const stored = getStoredLang();
      if (stored) setLangState(stored as Lang);
      else setLangState(systemDefault);
    })();
  }, [systemDefault]);

  // Load the user's language preference once we have a token (best effort).
  useEffect(() => {
    (async () => {
      try {
        const pref = await api<{ language: string | null }>(API.personalAdmin, "/preferences");
        setUserPref(pref.language);
      } catch { /* not logged in */ }
    })();
  }, []);

  const effective = useMemo(() => {
    return (userPref as Lang) || lang || systemDefault || "en";
  }, [userPref, lang, systemDefault]);

  const setLang = (next: Lang) => {
    setLangState(next);
    setStoredLang(next);
  };

  const t = (key: TKey) => dictionaries[effective]?.[key] ?? dictionaries.en[key] ?? key;

  return <LangContext.Provider value={{ lang: effective, setLang, t }}>{children}</LangContext.Provider>;
}

export function useLang() {
  const ctx = useContext(LangContext);
  if (!ctx) throw new Error("useLang must be used inside LangProvider");
  return ctx;
}
