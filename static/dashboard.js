const token = localStorage.getItem("token");
if (!token) window.location.href = "/login";

async function apiFetch(path) {
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

    if (window.CyberGrid) window.CyberGrid.init();
    if (window.CyberMap) window.CyberMap.init();
    if (window.CyberStream) window.CyberStream.init();
    if (window.CyberWeather) window.CyberWeather.init();
    if (window.CyberStocks) window.CyberStocks.init();
});
