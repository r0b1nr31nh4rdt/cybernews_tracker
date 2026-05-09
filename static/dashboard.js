if (!localStorage.getItem("token")) window.location.href = "/login";

async function apiFetch(path) {
    const token = localStorage.getItem("token");
    const response = await fetch(path, {
        headers: { Authorization: "Bearer " + token }
    });
    if (response.status === 401) {
        localStorage.removeItem("token");
        window.location.href = "/login";
    }
    return response.json();
}

document.addEventListener("DOMContentLoaded", async () => {
    const me = await apiFetch("/api/me");
    console.log("Eingeloggt als:", me.username, "| Rolle:", me.role);

    for (const [name, mod] of [
        ["CyberGrid",    window.CyberGrid],
        ["CyberMap",     window.CyberMap],
        ["CyberStream",  window.CyberStream],
        ["CyberWeather", window.CyberWeather],
        ["CyberStocks",  window.CyberStocks],
        ["CyberNews",    window.CyberNews],
    ]) {
        try {
            if (mod) mod.init();
        } catch (e) {
            console.error(name + " init fehlgeschlagen:", e);
        }
    }
});
