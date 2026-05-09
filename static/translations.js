const TRANSLATIONS = {
    de: {
        "nav.search.placeholder": "Suche...",
        "nav.filter.all":         "Alle Themen",
        "nav.filter.security":    "Security",
        "nav.filter.geopolitics": "Geopolitik",
        "nav.filter.science":     "Wissenschaft",
        "nav.filter.networks":    "Netzwerke",
        "nav.filter.local":       "DE/EU",
        "nav.login":              "Login",
        "nav.logout":             "Logout",
        "nav.admin":              "Admin",

        "module.map":             "Karte",
        "module.stream":          "Livestream",
        "module.weather":         "Wetter & Kurse",
        "module.headlines":       "Headlines",
        "module.article":         "Artikel",

        "weather.placeholder":    "PLZ eingeben...",
        "weather.feels":          "Gefühlt",
        "weather.error":          "⚠️ Ort nicht gefunden",

        "stocks.placeholder":     "Symbol (z.B. AAPL, BTC/USD)",
        "stocks.empty":           "Noch keine Symbole — oben hinzufügen",
        "stocks.locked":          "🔒 Login für persönliche Watchlist",
        "stocks.max":             "Maximal 8 Symbole",
        "stocks.currency":        "€",

        "news.loading":           "Lade Nachrichten...",
        "news.empty":             "Keine Artikel gefunden",
        "news.read_more":         "Vollständigen Artikel lesen →",
        "news.hint":              "🔍 Klicken für Vollansicht",
        "news.placeholder":       "← Headline auswählen",

        "cat.security":           "Security",
        "cat.geopolitics":        "Geopolitik",
        "cat.science":            "Wissenschaft",
        "cat.networks":           "Netzwerke",
        "cat.local":              "DE/EU",

        "login.title":            "Anmelden",
        "login.subtitle":         "Für persönliche Features wie Watchlist und Admin-Zugriff.",
        "login.username":         "Benutzername",
        "login.password":         "Passwort",
        "login.submit":           "Einloggen",
        "login.error":            "Ungültige Zugangsdaten",

        "stream.error":           "⚠️ Stream nicht verfügbar",

        "footer.copy":            "CyberNews Tracker",
    },

    en: {
        "nav.search.placeholder": "Search...",
        "nav.filter.all":         "All Topics",
        "nav.filter.security":    "Security",
        "nav.filter.geopolitics": "Geopolitics",
        "nav.filter.science":     "Science",
        "nav.filter.networks":    "Networks",
        "nav.filter.local":       "DE/EU",
        "nav.login":              "Login",
        "nav.logout":             "Logout",
        "nav.admin":              "Admin",

        "module.map":             "Map",
        "module.stream":          "Livestream",
        "module.weather":         "Weather & Markets",
        "module.headlines":       "Headlines",
        "module.article":         "Article",

        "weather.placeholder":    "Enter postal code...",
        "weather.feels":          "Feels like",
        "weather.error":          "⚠️ Location not found",

        "stocks.placeholder":     "Symbol (e.g. AAPL, BTC/USD)",
        "stocks.empty":           "No symbols yet — add above",
        "stocks.locked":          "🔒 Login for personal watchlist",
        "stocks.max":             "Maximum 8 symbols",
        "stocks.currency":        "$",

        "news.loading":           "Loading news...",
        "news.empty":             "No articles found",
        "news.read_more":         "Read full article →",
        "news.hint":              "🔍 Click for full view",
        "news.placeholder":       "← Select a headline",

        "cat.security":           "Security",
        "cat.geopolitics":        "Geopolitics",
        "cat.science":            "Science",
        "cat.networks":           "Networks",
        "cat.local":              "DE/EU",

        "login.title":            "Sign In",
        "login.subtitle":         "For personal features like watchlist and admin access.",
        "login.username":         "Username",
        "login.password":         "Password",
        "login.submit":           "Sign In",
        "login.error":            "Invalid credentials",

        "stream.error":           "⚠️ Stream unavailable",

        "footer.copy":            "CyberNews Tracker",
    }
};

let currentLang = "de";

function t(key) {
    return TRANSLATIONS[currentLang]?.[key] || TRANSLATIONS["de"]?.[key] || key;
}

function setLang(lang) {
    if (!TRANSLATIONS[lang]) return;
    currentLang = lang;
    applyTranslations();
}

function getLang() {
    return currentLang;
}

function applyTranslations() {
    document.querySelectorAll("[data-i18n]").forEach(el => {
        el.textContent = t(el.getAttribute("data-i18n"));
    });

    document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
        el.placeholder = t(el.getAttribute("data-i18n-placeholder"));
    });

    const filter = document.getElementById("nav-filter");
    if (filter) {
        filter.querySelectorAll("option").forEach(opt => {
            opt.textContent = t(`nav.filter.${opt.value}`);
        });
    }

    const langBtn = document.getElementById("lang-toggle");
    if (langBtn) langBtn.textContent = currentLang === "de" ? "🇩🇪" : "🇺🇸";

    if (window.CyberStocks?.rerenderCurrency) {
        window.CyberStocks.rerenderCurrency();
    }
}

window.i18n = { t, setLang, getLang, applyTranslations };
