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

function saveGridOrder() {
    const topOrder = [...document.querySelectorAll("#grid-top .module")]
        .map(el => el.dataset.id);
    const bottomOrder = [...document.querySelectorAll("#grid-bottom .module")]
        .map(el => el.dataset.id);
    localStorage.setItem("grid-top", JSON.stringify(topOrder));
    localStorage.setItem("grid-bottom", JSON.stringify(bottomOrder));
}

function restoreGridOrder() {
    ["grid-top", "grid-bottom"].forEach(gridId => {
        const saved = localStorage.getItem(gridId);
        if (!saved) return;
        const order = JSON.parse(saved);
        const grid = document.getElementById(gridId);
        order.forEach(id => {
            const el = grid.querySelector(`[data-id="${id}"]`);
            if (el) grid.appendChild(el);
        });
    });
}

document.addEventListener("DOMContentLoaded", async () => {
    const me = await apiFetch("/api/me");
    console.log("Eingeloggt als:", me.username, "| Rolle:", me.role);

    restoreGridOrder();

    document.querySelectorAll(".sortable-grid").forEach(grid => {
        Sortable.create(grid, {
            animation: 150,
            handle: ".module__header",
            ghostClass: "sortable-ghost",
            dragClass: "sortable-drag",
            onEnd: () => {
                saveGridOrder();
                if (window.CyberMap) window.CyberMap.resize();
            }
        });
    });

    if (window.CyberMap) window.CyberMap.init();
    if (window.CyberStream) window.CyberStream.init();
    if (window.CyberWeather) window.CyberWeather.init();
    if (window.CyberStocks) window.CyberStocks.init();
});
