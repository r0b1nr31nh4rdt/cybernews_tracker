const DEFAULT_STATE = {
    hidden: [],
    order: {
        "grid-top":    ["map", "stream", "weather-stocks"],
        "grid-bottom": ["headlines", "article"]
    },
    sizes: {}
};

let gridState = JSON.parse(JSON.stringify(DEFAULT_STATE));

// ── Laden ─────────────────────────────────────────────

async function loadGridState() {
    const token = localStorage.getItem("token");

    if (token) {
        try {
            const res = await fetch("/api/profile/grid", {
                headers: { Authorization: "Bearer " + token }
            });
            if (res.ok) {
                const data = await res.json();
                if (data.grid) {
                    gridState = data.grid;
                    return;
                }
            }
        } catch (err) {
            console.error("Grid-State laden Fehler:", err);
        }
    }

    gridState = JSON.parse(JSON.stringify(DEFAULT_STATE));
}

// ── Speichern ─────────────────────────────────────────

async function persistGridState() {
    const token = localStorage.getItem("token");

    if (token) {
        try {
            await fetch("/api/profile/grid", {
                method: "POST",
                headers: {
                    Authorization: "Bearer " + token,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ grid: gridState })
            });
        } catch (err) {
            console.error("Grid-State speichern Fehler:", err);
        }
    }
}

// ── Anwenden ──────────────────────────────────────────

function applyGridState() {
    // 1. Reihenfolge wiederherstellen
    Object.entries(gridState.order || {}).forEach(([rowId, order]) => {
        const row = document.getElementById(rowId);
        if (!row) return;
        order.forEach(id => {
            const el = row.querySelector(`[data-id="${id}"]`);
            if (el) row.appendChild(el);
        });
    });

    // 2. Größen wiederherstellen
    Object.entries(gridState.sizes || {}).forEach(([id, size]) => {
        const el = document.querySelector(`[data-id="${id}"]`);
        if (!el) return;
        if (size.width) {
            el.style.flexBasis  = size.width;
            el.style.flexGrow   = "0";
            el.style.flexShrink = "0";
        }
        if (size.height) el.style.height = size.height;
    });

    // 3. Ausgeblendete Module verstecken
    (gridState.hidden || []).forEach(id => {
        const el = document.querySelector(`[data-id="${id}"]`);
        if (el) el.style.display = "none";
    });

    // 4. Checkboxen im Settings-Panel synchronisieren
    document.querySelectorAll("#module-checklist input[type=checkbox]")
        .forEach(cb => {
            cb.checked = !(gridState.hidden || []).includes(cb.dataset.module);
        });
}

// ── Modul aus/einblenden ──────────────────────────────

function hideModule(moduleId) {
    const el = document.querySelector(`[data-id="${moduleId}"]`);
    if (el) el.style.display = "none";

    if (!gridState.hidden.includes(moduleId)) {
        gridState.hidden.push(moduleId);
    }

    const cb = document.querySelector(`#module-checklist input[data-module="${moduleId}"]`);
    if (cb) cb.checked = false;

    persistGridState();
}

function showModule(moduleId) {
    const el = document.querySelector(`[data-id="${moduleId}"]`);
    if (el) el.style.display = "";

    gridState.hidden = gridState.hidden.filter(id => id !== moduleId);

    const cb = document.querySelector(`#module-checklist input[data-module="${moduleId}"]`);
    if (cb) cb.checked = true;

    if (moduleId === "map" && window.CyberMap) {
        setTimeout(() => window.CyberMap.resize(), 100);
    }

    persistGridState();
}

// ── Grid-Reihenfolge + Größen speichern ───────────────

function saveCurrentOrder() {
    gridState.order = {};
    document.querySelectorAll(".grid-row").forEach(row => {
        gridState.order[row.id] = [...row.querySelectorAll(".module")]
            .map(el => el.dataset.id);
    });
    persistGridState();
}

function saveCurrentSizes() {
    gridState.sizes = {};
    document.querySelectorAll(".module[data-id]").forEach(el => {
        if (el.style.flexBasis || el.style.height) {
            gridState.sizes[el.dataset.id] = {
                width:  el.style.flexBasis || "",
                height: el.style.height || ""
            };
        }
    });
    persistGridState();
}

// ── Grid zurücksetzen ─────────────────────────────────

async function resetGridState() {
    gridState = JSON.parse(JSON.stringify(DEFAULT_STATE));

    document.querySelectorAll(".module[data-id]").forEach(el => {
        el.style.display    = "";
        el.style.flexBasis  = "";
        el.style.flexGrow   = "";
        el.style.flexShrink = "";
        el.style.height     = "";
    });

    applyGridState();
    await persistGridState();
}

window.GridState = {
    load:      loadGridState,
    apply:     applyGridState,
    hide:      hideModule,
    show:      showModule,
    saveOrder: saveCurrentOrder,
    saveSizes: saveCurrentSizes,
    reset:     resetGridState
};
