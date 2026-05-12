document.addEventListener("DOMContentLoaded", async () => {
    if (window.CyberLang) await window.CyberLang.init();

    const token = localStorage.getItem("token");
    let me = null;

    if (token) {
        try {
            const res = await fetch("/api/me", {
                headers: { Authorization: "Bearer " + token }
            });
            if (res.ok) {
                me = await res.json();
            } else if (res.status === 401) {
                localStorage.removeItem("token");
                if (window.CyberLogin) window.CyberLogin.updateNav(null);
            } else {
                localStorage.removeItem("token");
            }
        } catch (err) {
            console.error("Auth-Check Fehler:", err);
        }
    }

    if (window.CyberLogin) window.CyberLogin.updateNav(me);

    // Grid-State laden und anwenden
    if (window.GridState) {
        await window.GridState.load();
        window.GridState.apply();
    }

    for (const [name, mod] of [
        ["CyberGrid",    window.CyberGrid],
        ["CyberMap",     window.CyberMap],
        ["CyberStream",  window.CyberStream],
        ["CyberWeather", window.CyberWeather],
        ["CyberStocks",  window.CyberStocks],
        ["CyberNews",    window.CyberNews],
        ["CyberCVE",     window.CyberCVE],
        ["CyberLogin",   window.CyberLogin],
    ]) {
        try {
            if (mod) mod.init();
        } catch (e) {
            console.error(name + " init fehlgeschlagen:", e);
        }
    }

    // X-Button auf Modulen
    document.querySelectorAll(".module__close").forEach(btn => {
        btn.addEventListener("click", () => {
            if (window.GridState) window.GridState.hide(btn.dataset.module);
        });
    });

    // Settings-Panel
    const settingsBtn      = document.getElementById("settings-btn");
    const settingsPanel    = document.getElementById("settings-panel");
    const settingsClose    = document.getElementById("settings-close");
    const settingsBackdrop = document.getElementById("settings-backdrop");

    settingsBtn?.addEventListener("click", () => {
        if (settingsPanel) settingsPanel.style.display = "flex";
    });

    settingsClose?.addEventListener("click", () => {
        if (settingsPanel) settingsPanel.style.display = "none";
    });

    settingsBackdrop?.addEventListener("click", () => {
        if (settingsPanel) settingsPanel.style.display = "none";
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && settingsPanel?.style.display !== "none") {
            settingsPanel.style.display = "none";
        }
    });

    document.querySelectorAll("#module-checklist input[type=checkbox]")
        .forEach(cb => {
            cb.addEventListener("change", () => {
                const moduleId = cb.dataset.module;
                if (cb.checked) {
                    window.GridState?.show(moduleId);
                } else {
                    window.GridState?.hide(moduleId);
                }
            });
        });

    document.getElementById("grid-reset-btn")?.addEventListener("click", async () => {
        if (window.GridState) await window.GridState.reset();
        if (settingsPanel) settingsPanel.style.display = "none";
    });
});
