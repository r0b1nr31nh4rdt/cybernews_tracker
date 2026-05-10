async function initLang() {
    const token = localStorage.getItem("token");
    let lang = "de";

    if (token) {
        try {
            const res = await fetch("/api/profile/language", {
                headers: { Authorization: "Bearer " + token }
            });
            if (res.ok) {
                const data = await res.json();
                lang = data.language || "de";
            }
        } catch (err) {
            console.error("Sprache laden Fehler:", err);
        }
    } else {
        lang = localStorage.getItem("lang") || "de";
    }

    window.i18n.setLang(lang);

    const langBtn = document.getElementById("lang-toggle");
    if (langBtn) {
        langBtn.addEventListener("click", () => toggleLang());
    }
}

async function toggleLang() {
    const newLang = window.i18n.getLang() === "de" ? "en" : "de";
    window.i18n.setLang(newLang);
    if (window.CyberStream) window.CyberStream.reload();

    const token = localStorage.getItem("token");

    if (token) {
        try {
            await fetch("/api/profile/language", {
                method: "POST",
                headers: {
                    Authorization: "Bearer " + token,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ language: newLang })
            });
        } catch (err) {
            console.error("Sprache speichern Fehler:", err);
        }
    } else {
        localStorage.setItem("lang", newLang);
    }
}

window.CyberLang = { init: initLang };
