import { createContext, useEffect, useState, useCallback, useMemo } from "react";
import { translations } from "@/i18n/translations";

export const LanguageContext = createContext(null);

const getInitial = () => {
  try {
    return localStorage.getItem("lang") || "fr";
  } catch {
    return "fr";
  }
};

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState(getInitial);

  useEffect(() => {
    document.documentElement.lang = lang;
    try {
      localStorage.setItem("lang", lang);
    } catch {
      /* stockage indisponible */
    }
  }, [lang]);

  const toggleLang = useCallback(
    () => setLang((l) => (l === "fr" ? "en" : "fr")),
    [],
  );

  // t("hero.title1") → texte dans la langue courante
  const t = useCallback(
    (key) =>
      key.split(".").reduce((obj, k) => (obj ? obj[k] : undefined), translations[lang]) ?? key,
    [lang],
  );

  const value = useMemo(() => ({ lang, toggleLang, t }), [lang, toggleLang, t]);
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}