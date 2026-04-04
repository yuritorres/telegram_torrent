import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import ptBR from './locales/pt-br.json';
import en from './locales/en.json';

i18n
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
        resources: {
            'pt-BR': { translation: ptBR },
            'en': { translation: en }
        },
        fallbackLng: 'pt-BR',
        interpolation: {
            escapeValue: false
        }
    });

export default i18n;
