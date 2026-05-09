document.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem("token");
    let me = null;

    if (token) {
        try {
            const res = await fetch("/api/me", {
                headers: { Authorization: "Bearer " + token }
            });
            if (res.ok) {
                me = await res.json();
            } else {
                localStorage.removeItem("token");
            }
        } catch (err) {
            console.error("Auth-Check Fehler:", err);
        }
    }

    if (window.CyberLogin) window.CyberLogin.updateNav(me);

    for (const [name, mod] of [
        ["CyberGrid",    window.CyberGrid],
        ["CyberMap",     window.CyberMap],
        ["CyberStream",  window.CyberStream],
        ["CyberWeather", window.CyberWeather],
        ["CyberStocks",  window.CyberStocks],
        ["CyberNews",    window.CyberNews],
        ["CyberLogin",   window.CyberLogin],
    ]) {
        try {
            if (mod) mod.init();
        } catch (e) {
            console.error(name + " init fehlgeschlagen:", e);
        }
    }
});
