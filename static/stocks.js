let watchlist = [];
let refreshInterval = null;

function initStocks() {
    const addBtn = document.getElementById("stocks-add-btn");
    const input = document.getElementById("stocks-input");
    if (!addBtn || !input) return;

    addBtn.addEventListener("click", addSymbol);
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") addSymbol();
    });

    loadWatchlist();
    refreshInterval = setInterval(refreshQuotes, 60000);
}

async function loadWatchlist() {
    const token = localStorage.getItem("token");
    try {
        const res = await fetch("/api/watchlist", {
            headers: { Authorization: "Bearer " + token }
        });
        if (!res.ok) return;
        const data = await res.json();
        watchlist = data.watchlist || [];
        renderList();
        if (watchlist.length > 0) refreshQuotes();
    } catch (err) {
        console.error("Watchlist Ladefehler:", err);
    }
}

async function saveWatchlist() {
    const token = localStorage.getItem("token");
    try {
        await fetch("/api/watchlist", {
            method: "POST",
            headers: {
                Authorization: "Bearer " + token,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ watchlist })
        });
    } catch (err) {
        console.error("Watchlist Speicherfehler:", err);
    }
}

async function addSymbol() {
    const input = document.getElementById("stocks-input");
    const symbol = input.value.trim().toUpperCase();
    if (!symbol || watchlist.includes(symbol)) return;
    if (watchlist.length >= 8) {
        alert("Maximal 8 Symbole");
        return;
    }
    watchlist.push(symbol);
    input.value = "";
    renderList();
    await saveWatchlist();
    refreshQuotes();
}

async function removeSymbol(symbol) {
    watchlist = watchlist.filter(s => s !== symbol);
    renderList();
    await saveWatchlist();
}

async function refreshQuotes() {
    if (watchlist.length === 0) return;
    const token = localStorage.getItem("token");
    try {
        const res = await fetch(
            `/api/quotes?symbols=${watchlist.join(",")}`,
            { headers: { Authorization: "Bearer " + token } }
        );
        if (!res.ok) return;
        const data = await res.json();
        renderQuotes(data.quotes);
    } catch (err) {
        console.error("Kursdaten Fehler:", err);
    }
}

function renderList() {
    const listEl = document.getElementById("stocks-list");
    const emptyEl = document.getElementById("stocks-empty");
    if (!listEl) return;

    if (watchlist.length === 0) {
        listEl.innerHTML = "";
        if (emptyEl) emptyEl.style.display = "block";
        return;
    }

    if (emptyEl) emptyEl.style.display = "none";

    listEl.innerHTML = watchlist.map(symbol => `
        <div class="stock-row" data-symbol="${symbol}">
            <span class="stock-symbol">${symbol}</span>
            <span class="stock-price">—</span>
            <span class="stock-change">—</span>
            <button class="stock-remove" onclick="removeSymbol('${symbol}')">×</button>
        </div>
    `).join("");
}

function renderQuotes(quotes) {
    quotes.forEach(q => {
        const row = document.querySelector(`.stock-row[data-symbol="${q.symbol}"]`);
        if (!row) return;

        if (q.error) {
            row.querySelector(".stock-price").textContent = "N/A";
            row.querySelector(".stock-change").textContent = "—";
            return;
        }

        const isPositive = q.change >= 0;
        row.querySelector(".stock-price").textContent =
            `${parseFloat(q.price).toFixed(2)} ${q.currency}`;

        const changeEl = row.querySelector(".stock-change");
        changeEl.textContent = `${isPositive ? "+" : ""}${q.percent.toFixed(2)}%`;
        changeEl.className = "stock-change " +
            (isPositive ? "stock-change--up" : "stock-change--down");
    });
}

window.CyberStocks = { init: initStocks };
