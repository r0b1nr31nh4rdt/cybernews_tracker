const adminToken = localStorage.getItem("token");

async function initAdmin() {
    if (!adminToken) { window.location.href = "/"; return; }

    const res = await fetch("/api/me", {
        headers: { Authorization: "Bearer " + adminToken }
    });
    if (!res.ok) { window.location.href = "/"; return; }
    const me = await res.json();
    if (me.role !== "admin") { window.location.href = "/"; return; }

    initTabs();
    loadSources();
    loadStreams();
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

// ── Quellen ───────────────────────────────────────────

async function loadSources() {
    const res = await fetch("/api/admin/sources", {
        headers: { Authorization: "Bearer " + adminToken }
    });
    const data = await res.json();
    const list = document.getElementById("sources-list");

    list.innerHTML = data.sources.map(s => `
        <div class="admin-row">
            <span class="admin-row__badge cat--${s.category}">${s.category}</span>
            <span class="admin-row__name">${s.name}</span>
            <span class="admin-row__url">${s.rss_url}</span>
            <label class="admin-toggle">
                <input type="checkbox" ${s.active ? "checked" : ""}
                    onchange="toggleSource(${s.id}, this.checked)" />
                <span>${s.active ? "Aktiv" : "Inaktiv"}</span>
            </label>
            <button class="admin-delete-btn"
                onclick="deleteSource(${s.id})">Löschen</button>
        </div>
    `).join("");
}

async function toggleSource(id, active) {
    await fetch(`/api/admin/sources/${id}`, {
        method: "PATCH",
        headers: {
            Authorization: "Bearer " + adminToken,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ active })
    });
    loadSources();
}

async function deleteSource(id) {
    if (!confirm("Quelle wirklich löschen?")) return;
    await fetch(`/api/admin/sources/${id}`, {
        method: "DELETE",
        headers: { Authorization: "Bearer " + adminToken }
    });
    loadSources();
}

document.getElementById("add-source-btn")
    ?.addEventListener("click", () => {
        document.getElementById("add-source-form").style.display = "flex";
    });

document.getElementById("source-cancel-btn")
    ?.addEventListener("click", () => {
        document.getElementById("add-source-form").style.display = "none";
    });

document.getElementById("source-save-btn")
    ?.addEventListener("click", async () => {
        const name     = document.getElementById("source-name").value.trim();
        const rss_url  = document.getElementById("source-url").value.trim();
        const category = document.getElementById("source-category").value;
        if (!name || !rss_url) return;

        await fetch("/api/admin/sources", {
            method: "POST",
            headers: {
                Authorization: "Bearer " + adminToken,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ name, rss_url, category })
        });
        document.getElementById("add-source-form").style.display = "none";
        document.getElementById("source-name").value = "";
        document.getElementById("source-url").value = "";
        loadSources();
    });

// ── Streams ───────────────────────────────────────────

async function loadStreams() {
    const res = await fetch("/api/admin/streams", {
        headers: { Authorization: "Bearer " + adminToken }
    });
    const data = await res.json();
    const list = document.getElementById("streams-list");

    list.innerHTML = data.streams.map(s => `
        <div class="admin-row">
            <span class="admin-row__name">${s.name}</span>
            <span class="admin-row__url">${s.youtube_url}</span>
            <button class="admin-delete-btn"
                onclick="deleteStream(${s.id})">Löschen</button>
        </div>
    `).join("");
}

async function deleteStream(id) {
    if (!confirm("Stream wirklich löschen?")) return;
    await fetch(`/api/admin/streams/${id}`, {
        method: "DELETE",
        headers: { Authorization: "Bearer " + adminToken }
    });
    loadStreams();
}

document.getElementById("add-stream-btn")
    ?.addEventListener("click", () => {
        document.getElementById("add-stream-form").style.display = "flex";
    });

document.getElementById("stream-cancel-btn")
    ?.addEventListener("click", () => {
        document.getElementById("add-stream-form").style.display = "none";
    });

document.getElementById("stream-save-btn")
    ?.addEventListener("click", async () => {
        const name = document.getElementById("stream-name").value.trim();
        const url  = document.getElementById("stream-url").value.trim();
        if (!name || !url) return;

        await fetch("/api/admin/streams", {
            method: "POST",
            headers: {
                Authorization: "Bearer " + adminToken,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ name, youtube_url: url })
        });
        document.getElementById("add-stream-form").style.display = "none";
        document.getElementById("stream-name").value = "";
        document.getElementById("stream-url").value = "";
        loadStreams();
    });

window.toggleSource = toggleSource;
window.deleteSource = deleteSource;
window.deleteStream = deleteStream;

document.addEventListener("DOMContentLoaded", initAdmin);
