const token = localStorage.getItem("token");
let hiddenSourceIds = [];

async function initProfile() {
    if (!token) {
        window.location.href = "/?login=1";
        return;
    }

    const res = await fetch("/api/me", {
        headers: { Authorization: "Bearer " + token }
    });
    if (!res.ok) {
        window.location.href = "/?login=1";
        return;
    }

    const me = await res.json();
    if (window.CyberLogin) window.CyberLogin.updateNav(me);

    initTabs();
    loadSources();
}

// ── Tabs ──────────────────────────────────────────────

function initTabs() {
    document.querySelectorAll(".admin-tab").forEach(tab => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".admin-tab")
                .forEach(t => t.classList.remove("admin-tab--active"));
            document.querySelectorAll(".admin-content")
                .forEach(c => c.style.display = "none");
            tab.classList.add("admin-tab--active");
            document.getElementById("tab-" + tab.dataset.tab).style.display = "block";
        });
    });
}

// ── Quellen laden ─────────────────────────────────────

async function loadSources() {
    const res = await fetch("/api/profile/sources", {
        headers: { Authorization: "Bearer " + token }
    });
    const data = await res.json();

    hiddenSourceIds = data.global_sources
        .filter(s => !s.enabled)
        .map(s => s.id);

    renderGlobalSources(data.global_sources);
    renderUserSources(data.user_sources);
}

// ── Globale Quellen ───────────────────────────────────

function renderGlobalSources(sources) {
    const list = document.getElementById("global-sources-list");
    if (!list) return;

    const categories = {};
    sources.forEach(s => {
        if (!categories[s.category]) categories[s.category] = [];
        categories[s.category].push(s);
    });

    const catLabels = {
        security:    "Security",
        geopolitics: "Geopolitik",
        science:     "Wissenschaft",
        networks:    "Netzwerke",
        local:       "DE/EU"
    };

    list.innerHTML = Object.entries(categories).map(([cat, srcs]) => `
        <div class="source-category-group">
            <h4 class="source-category-label cat--${cat}">
                ${catLabels[cat] || cat}
            </h4>
            ${srcs.map(s => `
                <label class="settings-check source-check">
                    <input type="checkbox"
                        data-source-id="${s.id}"
                        ${s.enabled ? "checked" : ""}
                        onchange="toggleGlobalSource(${s.id}, this.checked)" />
                    <span>${s.name}</span>
                </label>
            `).join("")}
        </div>
    `).join("");
}

function toggleGlobalSource(sourceId, enabled) {
    if (enabled) {
        hiddenSourceIds = hiddenSourceIds.filter(id => id !== sourceId);
    } else {
        if (!hiddenSourceIds.includes(sourceId)) {
            hiddenSourceIds.push(sourceId);
        }
    }
}

document.getElementById("save-hidden-btn")
    ?.addEventListener("click", async () => {
        const res = await fetch("/api/profile/sources/hidden", {
            method: "POST",
            headers: {
                Authorization: "Bearer " + token,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ hidden_source_ids: hiddenSourceIds })
        });
        if (res.ok) {
            const btn = document.getElementById("save-hidden-btn");
            btn.textContent = "✅ Gespeichert";
            setTimeout(() => btn.textContent = "Auswahl speichern", 2000);
        }
    });

// ── Eigene Quellen ────────────────────────────────────

function renderUserSources(sources) {
    const list = document.getElementById("user-sources-list");
    if (!list) return;

    if (sources.length === 0) {
        list.innerHTML = `
            <div style="padding:16px; color:var(--text-muted); font-size:13px">
                Noch keine eigenen Quellen hinzugefügt.
            </div>`;
        return;
    }

    list.innerHTML = sources.map(s => `
        <div class="admin-row">
            <span class="admin-row__badge cat--${s.category}">${s.category}</span>
            <span class="admin-row__name">${s.name}</span>
            <span class="admin-row__url">${s.rss_url}</span>
            <button class="admin-delete-btn"
                onclick="deleteUserSource(${s.id})">Löschen</button>
        </div>
    `).join("");
}

async function deleteUserSource(sourceId) {
    if (!confirm("Eigene Quelle wirklich löschen?")) return;
    await fetch(`/api/profile/sources/user/${sourceId}`, {
        method: "DELETE",
        headers: { Authorization: "Bearer " + token }
    });
    loadSources();
}

document.getElementById("add-user-source-btn")
    ?.addEventListener("click", () => {
        document.getElementById("add-user-source-form").style.display = "flex";
    });

document.getElementById("user-source-cancel-btn")
    ?.addEventListener("click", () => {
        document.getElementById("add-user-source-form").style.display = "none";
    });

document.getElementById("user-source-save-btn")
    ?.addEventListener("click", async () => {
        const name     = document.getElementById("user-source-name").value.trim();
        const rss_url  = document.getElementById("user-source-url").value.trim();
        const category = document.getElementById("user-source-category").value;

        if (!name || !rss_url) return;

        const res = await fetch("/api/profile/sources/user", {
            method: "POST",
            headers: {
                Authorization: "Bearer " + token,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ name, rss_url, category })
        });

        if (res.ok) {
            document.getElementById("add-user-source-form").style.display = "none";
            document.getElementById("user-source-name").value = "";
            document.getElementById("user-source-url").value = "";
            loadSources();
        }
    });

window.toggleGlobalSource = toggleGlobalSource;
window.deleteUserSource   = deleteUserSource;

document.addEventListener("DOMContentLoaded", initProfile);
