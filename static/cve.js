async function initCVE() {
    await loadCVE();

    document.getElementById("cve-refresh")
        ?.addEventListener("click", loadCVE);
}

async function loadCVE() {
    const widget = document.getElementById("cve-widget");
    if (!widget) return;

    widget.innerHTML = '<div class="loading-state"><div class="spinner"></div></div>';

    try {
        const res = await fetch("/api/cve/today");
        if (!res.ok) throw new Error("CVE laden fehlgeschlagen");
        const cve = await res.json();
        renderCVE(cve);
    } catch (err) {
        widget.innerHTML = `
            <div class="empty-state">
                ⚠️ CVE Daten nicht verfügbar
            </div>`;
    }
}

function renderCVE(cve) {
    const widget = document.getElementById("cve-widget");
    if (!widget) return;

    const score     = cve.score ? cve.score.toFixed(1) : "N/A";
    const published = cve.published
        ? new Date(cve.published).toLocaleDateString("de-DE")
        : "";

    const severityClass = {
        "CRITICAL": "cve-severity--critical",
        "HIGH":     "cve-severity--high",
        "MEDIUM":   "cve-severity--medium",
        "LOW":      "cve-severity--low",
    }[cve.severity] || "";

    const attackInfo = [
        cve.attack_vector ? `Attack: ${cve.attack_vector}` : null,
        cve.complexity    ? `Complexity: ${cve.complexity}` : null,
        cve.privileges    ? `Privileges: ${cve.privileges}` : null,
    ].filter(Boolean).join(" · ");

    widget.innerHTML = `
        <div class="cve-card">
            <div class="cve-header">
                <span class="cve-id">${cve.id}</span>
                <span class="cve-severity ${severityClass}">
                    ${cve.severity} ${score}
                </span>
            </div>

            ${published ? `
                <div class="cve-date">Veröffentlicht: ${published}</div>
            ` : ""}

            ${cve.products?.length ? `
                <div class="cve-products">
                    ${cve.products.map(p => `
                        <span class="cve-product-tag">${p}</span>
                    `).join("")}
                </div>
            ` : ""}

            <p class="cve-description">${cve.description}</p>

            ${attackInfo ? `
                <div class="cve-metrics">${attackInfo}</div>
            ` : ""}

            <div class="cve-links">
                <a href="${cve.nvd_url}" target="_blank"
                   rel="noopener noreferrer" class="cve-link cve-link--nvd">
                    NVD Details →
                </a>
                <a href="${cve.exploitdb_url}" target="_blank"
                   rel="noopener noreferrer" class="cve-link cve-link--exploitdb">
                    Exploit-DB →
                </a>
            </div>
        </div>
    `;
}

window.CyberCVE = { init: initCVE };
