import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { TRANSLATIONS } from './translations';

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    try {
      return localStorage.getItem('bloxy_language') || 'en';
    } catch {
      return 'en';
    }
  });

  const applyLang = useCallback((newLang) => {
    try { localStorage.setItem('bloxy_language', newLang); } catch {}
    document.documentElement.lang = newLang;
    document.documentElement.dir = newLang === 'ar' ? 'rtl' : 'ltr';
    setLangState(newLang);
  }, []);

  const setLang = useCallback((newLang) => {
    applyLang(newLang);
  }, [applyLang]);

  // Called when UserSettings are loaded — syncs language from the database
  const syncFromSettings = useCallback((newLang) => {
    if (newLang && newLang !== lang) {
      applyLang(newLang);
    }
  }, [lang, applyLang]);

  const t = useCallback((key) => {
    const dict = TRANSLATIONS[lang] || TRANSLATIONS.en;
    return dict[key] || TRANSLATIONS.en[key] || key;
  }, [lang]);

  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
  }, [lang]);

  return (
    <LanguageContext.Provider value={{ lang, setLang, syncFromSettings, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}
