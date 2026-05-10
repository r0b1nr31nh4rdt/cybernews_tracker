let newsAllArticles     = [];
let newsFilteredArticles = [];
let newsActiveIndex     = null;
let newsSearchDebounce  = null;

function initNews() {
    loadNews();
    setInterval(loadNews, 5 * 60 * 1000);

    const searchInput = document.getElementById("nav-search");
    if (searchInput) {
        searchInput.addEventListener("input", () => {
            clearTimeout(newsSearchDebounce);
            newsSearchDebounce = setTimeout(applyFilters, 300);
        });
    }

    const filter = document.getElementById("nav-filter");
    if (filter) {
        filter.addEventListener("change", applyFilters);
    }

    document.getElementById("search-clear")?.addEventListener("click", () => {
        const input = document.getElementById("nav-search");
        if (input) {
            input.value = "";
            input.classList.remove("has-results", "no-results");
        }
        document.getElementById("search-clear").style.display = "none";
        applyFilters();
    });

    document.getElementById("modal-close")
        ?.addEventListener("click", closeModal);
    document.querySelector(".modal__backdrop")
        ?.addEventListener("click", closeModal);
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") closeModal();
    });

    const headlinesList = document.getElementById("headlines-list");
    if (headlinesList) {
        headlinesList.addEventListener("click", (e) => {
            const item = e.target.closest(".headline-item");
            if (item) showArticle(parseInt(item.dataset.index));
        });
    }
}

async function loadNews() {
    const loadingEl = document.getElementById("headlines-loading");

    if (loadingEl) loadingEl.style.display = "flex";

    try {
        const category = document.getElementById("nav-filter")?.value || "all";
        const token = localStorage.getItem("token");
        const headers = token ? { Authorization: "Bearer " + token } : {};

        const res = await fetch(`/api/news?category=${category}&limit=100`, { headers });
        if (!res.ok) throw new Error("API Fehler");

        const data = await res.json();
        newsAllArticles = data.articles || [];

        if (loadingEl) loadingEl.style.display = "none";

        applyFilters();

    } catch (err) {
        console.error("News-Fehler:", err);
        if (loadingEl) loadingEl.style.display = "none";
    }
}

function applyFilters() {
    const searchTerm = document.getElementById("nav-search")?.value
        .trim().toLowerCase() || "";
    const category = document.getElementById("nav-filter")?.value || "all";

    newsFilteredArticles = newsAllArticles.filter(article => {
        const categoryMatch = category === "all" || article.category === category;
        const searchMatch = !searchTerm ||
            article.title.toLowerCase().includes(searchTerm) ||
            (article.summary || "").toLowerCase().includes(searchTerm);
        return categoryMatch && searchMatch;
    });

    // Suchfeld einfärben
    const searchInput = document.getElementById("nav-search");
    if (searchInput && searchTerm) {
        searchInput.classList.toggle("has-results", newsFilteredArticles.length > 0);
        searchInput.classList.toggle("no-results", newsFilteredArticles.length === 0);
    } else if (searchInput) {
        searchInput.classList.remove("has-results", "no-results");
    }

    // Clear-Button ein-/ausblenden
    const clearBtn = document.getElementById("search-clear");
    if (clearBtn) clearBtn.style.display = searchTerm ? "block" : "none";

    // Artikel-Count aktualisieren
    const countEl = document.getElementById("headlines-count");
    if (countEl) {
        countEl.textContent = searchTerm || category !== "all"
            ? `${newsFilteredArticles.length} / ${newsAllArticles.length}`
            : newsAllArticles.length;
    }

    const emptyEl = document.getElementById("headlines-empty");

    if (newsFilteredArticles.length === 0) {
        if (emptyEl) {
            emptyEl.textContent = searchTerm
                ? `Keine Treffer für "${searchTerm}"`
                : "Keine Artikel gefunden";
            emptyEl.style.display = "flex";
        }
        document.getElementById("headlines-list").innerHTML = "";
        return;
    }

    if (emptyEl) emptyEl.style.display = "none";

    newsActiveIndex = null;
    renderHeadlines(newsFilteredArticles);
    showArticle(0);
}

function renderHeadlines(articles) {
    const list = document.getElementById("headlines-list");
    if (!list) return;

    list.innerHTML = articles.map((article, i) => {
        const time = article.published
            ? new Date(article.published).toLocaleTimeString("de-DE", {
                hour: "2-digit", minute: "2-digit"
              })
            : "";

        const categoryClass = `cat--${article.category || "default"}`;

        return `
            <div class="headline-item ${i === newsActiveIndex ? "headline-item--active" : ""}"
                 data-index="${i}">
                ${article.image
                    ? `<img class="headline-thumb" src="${article.image}" alt="">`
                    : `<span class="headline-thumb-empty"></span>`}
                <span class="headline-cat ${categoryClass}"></span>
                <div class="headline-content">
                    <span class="headline-title">${escapeHtml(article.title)}</span>
                    <span class="headline-meta">
                        <span class="headline-source">${escapeHtml(article.source)}</span>
                        <span class="headline-time">${time}</span>
                    </span>
                </div>
            </div>
        `;
    }).join("");

    list.querySelectorAll(".headline-thumb").forEach(img => {
        img.addEventListener("error", () => { img.style.display = "none"; });
    });
}

async function showArticle(index) {
    const article = newsFilteredArticles[index];
    if (!article) return;

    newsActiveIndex = index;

    document.querySelectorAll(".headline-item").forEach((el, i) => {
        el.classList.toggle("headline-item--active", i === index);
    });

    const moduleTitle = document.getElementById("article-module-title");
    if (moduleTitle) moduleTitle.textContent = article.source;

    const viewer = document.getElementById("article-viewer");
    if (!viewer) return;

    viewer.innerHTML = '<div class="loading-state"><div class="spinner"></div></div>';
    await new Promise(r => setTimeout(r, 50));

    const published = article.published
        ? new Date(article.published).toLocaleString("de-DE", {
            day: "2-digit", month: "2-digit", year: "numeric",
            hour: "2-digit", minute: "2-digit"
          })
        : "";

    viewer.innerHTML = `
        <div class="article-card">
            <div class="article-card__category cat--${article.category}">
                ${categoryLabel(article.category)}
            </div>
            <div class="article-card__body-wrap">
                ${article.image ? `
                    <div class="article-card__image--side">
                        <img src="${article.image}" alt="" />
                    </div>
                ` : ""}
                <div class="article-card__body">
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
            </div>
        </div>
        <a href="${article.link}" target="_blank" rel="noopener noreferrer"
           class="article-external-link">
            Vollständigen Artikel lesen →
        </a>
    `;

    const card = viewer.querySelector(".article-card");
    if (card) card.addEventListener("click", () => openModal(index));

    const extLink = viewer.querySelector(".article-external-link");
    if (extLink) extLink.addEventListener("click", (e) => e.stopPropagation());

    const sideImg = viewer.querySelector(".article-card__image--side img");
    if (sideImg) sideImg.addEventListener("error", () => {
        sideImg.parentElement.style.display = "none";
    });
}

function openModal(index) {
    const article = newsFilteredArticles[index];
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

window.CyberNews = { init: initNews, reload: loadNews };
