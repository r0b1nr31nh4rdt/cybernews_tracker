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

    if (me.role !== "admin") {
        document.querySelector("main").textContent = "Zugriff verweigert.";
        return;
    }

    console.log("Admin-Panel geladen für:", me.username);
    // TODO: Briefing 03 füllt das Admin-Panel mit Inhalt
});
