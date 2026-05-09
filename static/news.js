let newsAllArticles = [];
let newsActiveIndex = null;

function initNews() {
    loadNews();
    setInterval(loadNews, 5 * 60 * 1000);

    document.getElementById("modal-close")
        ?.addEventListener("click", closeModal);
    document.querySelector(".modal__backdrop")
        ?.addEventListener("click", closeModal);
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") closeModal();
    });
}

async function loadNews() {
    const token = localStorage.getItem("token");
    if (!token) return;

    const loadingEl = document.getElementById("headlines-loading");
    const emptyEl   = document.getElementById("headlines-empty");

    if (loadingEl) loadingEl.style.display = "flex";

    try {
        const category = document.getElementById("nav-filter")?.value || "all";

        const res = await fetch(`/api/news?category=${category}&limit=50`, {
            headers: { Authorization: "Bearer " + token }
        });
        if (res.status === 401) {
            localStorage.removeItem("token");
            window.location.href = "/login";
            return;
        }
        if (!res.ok) throw new Error("API Fehler");

        const data = await res.json();
        newsAllArticles = data.articles || [];

        if (loadingEl) loadingEl.style.display = "none";

        if (newsAllArticles.length === 0) {
            if (emptyEl) emptyEl.style.display = "flex";
            return;
        }

        if (emptyEl) emptyEl.style.display = "none";
        renderHeadlines(newsAllArticles);

        if (newsActiveIndex === null) showArticle(0);

    } catch (err) {
        console.error("News-Fehler:", err);
        if (loadingEl) loadingEl.style.display = "none";
    }
}

function renderHeadlines(articles) {
    const list = document.getElementById("headlines-list");
    const countEl = document.getElementById("headlines-count");
    if (!list) return;

    if (countEl) countEl.textContent = articles.length;

    list.innerHTML = articles.map((article, i) => {
        const time = article.published
            ? new Date(article.published).toLocaleTimeString("de-DE", {
                hour: "2-digit", minute: "2-digit"
              })
            : "";

        const categoryClass = `cat--${article.category || "default"}`;

        return `
            <div class="headline-item ${i === newsActiveIndex ? "headline-item--active" : ""}"
                 data-index="${i}"
                 onclick="showArticle(${i})">
                <span class="headline-cat ${categoryClass}"></span>
                <span class="headline-title">${escapeHtml(article.title)}</span>
                <span class="headline-meta">
                    <span class="headline-source">${escapeHtml(article.source)}</span>
                    <span class="headline-time">${time}</span>
                </span>
            </div>
        `;
    }).join("");
}

function showArticle(index) {
    const article = newsAllArticles[index];
    if (!article) return;

    newsActiveIndex = index;

    document.querySelectorAll(".headline-item").forEach((el, i) => {
        el.classList.toggle("headline-item--active", i === index);
    });

    const moduleTitle = document.getElementById("article-module-title");
    if (moduleTitle) moduleTitle.textContent = article.source;

    const viewer = document.getElementById("article-viewer");
    if (!viewer) return;

    const published = article.published
        ? new Date(article.published).toLocaleString("de-DE", {
            day: "2-digit", month: "2-digit", year: "numeric",
            hour: "2-digit", minute: "2-digit"
          })
        : "";

    viewer.innerHTML = `
        <div class="article-card" onclick="openModal(${index})">
            <div class="article-card__category cat--${article.category}">
                ${categoryLabel(article.category)}
            </div>
            <h2 class="article-card__title">${escapeHtml(article.title)}</h2>
            <div class="article-card__meta">
                <span>${escapeHtml(article.source)}</span>
                ${published ? `<span>${published}</span>` : ""}
            </div>
            <p class="article-card__summary">
                ${escapeHtml(stripHtml(article.summary || "Kein Teaser verfügbar."))}
            </p>
            <div class="article-card__hint">🔍 Klicken für Vollansicht</div>
        </div>
        <a href="${article.link}" target="_blank" rel="noopener noreferrer"
           class="article-external-link"
           onclick="event.stopPropagation()">
            Vollständigen Artikel lesen →
        </a>
    `;
}

function openModal(index) {
    const article = newsAllArticles[index];
    if (!article) return;

    const modal = document.getElementById("article-modal");
    const modalBody = document.getElementById("modal-body");
    if (!modal || !modalBody) return;

    const published = article.published
        ? new Date(article.published).toLocaleString("de-DE", {
            day: "2-digit", month: "2-digit", year: "numeric",
            hour: "2-digit", minute: "2-digit"
          })
        : "";

    modalBody.innerHTML = `
        <div class="modal-article">
            <div class="article-card__category cat--${article.category}">
                ${categoryLabel(article.category)}
            </div>
            <h1 class="modal-article__title">${escapeHtml(article.title)}</h1>
            <div class="article-card__meta">
                <span>${escapeHtml(article.source)}</span>
                ${published ? `<span>${published}</span>` : ""}
            </div>
            <p class="modal-article__summary">
                ${escapeHtml(stripHtml(article.summary || "Kein Teaser verfügbar."))}
            </p>
            <a href="${article.link}" target="_blank" rel="noopener noreferrer"
               class="article-external-link">
                Vollständigen Artikel lesen →
            </a>
        </div>
    `;

    modal.style.display = "flex";
    document.body.style.overflow = "hidden";
}

function closeModal() {
    const modal = document.getElementById("article-modal");
    if (modal) modal.style.display = "none";
    document.body.style.overflow = "";
}

function categoryLabel(cat) {
    const labels = {
        security:    "Security",
        geopolitics: "Geopolitik",
        science:     "Wissenschaft",
        networks:    "Netzwerke",
        local:       "DE/EU"
    };
    return labels[cat] || cat;
}

function escapeHtml(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function stripHtml(str) {
    return str.replace(/<[^>]*>/g, "").trim();
}

document.addEventListener("DOMContentLoaded", () => {
    const filter = document.getElementById("nav-filter");
    if (filter) {
        filter.addEventListener("change", () => {
            newsActiveIndex = null;
            loadNews();
        });
    }
});

window.CyberNews = { init: initNews, reload: loadNews };
window.showArticle = showArticle;
window.openModal = openModal;
