function initLoginModal() {
    const loginBtn  = document.getElementById("login-btn");
    const modal     = document.getElementById("login-modal");
    const closeBtn  = document.getElementById("login-modal-close");
    const backdrop  = document.getElementById("login-backdrop");
    const form      = document.getElementById("login-form");
    const errorEl   = document.getElementById("login-error");

    loginBtn?.addEventListener("click", () => openLoginModal());

    closeBtn?.addEventListener("click", closeLoginModal);
    backdrop?.addEventListener("click", closeLoginModal);
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") closeLoginModal();
    });

    form?.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (errorEl) errorEl.textContent = "";

        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;

        const res = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        if (res.ok) {
            const data = await res.json();
            localStorage.setItem("token", data.access_token);
            closeLoginModal();
            onLoginSuccess();
        } else {
            if (errorEl) errorEl.textContent = "Ungültige Zugangsdaten";
        }
    });

    const logoutLink = document.getElementById("logout-link");
    if (logoutLink) {
        logoutLink.addEventListener("click", async (e) => {
            e.preventDefault();
            await fetch("/api/logout", { method: "POST" });
            localStorage.removeItem("token");
            updateNav(null);
            if (window.CyberStocks) window.CyberStocks.reload();
        });
    }

    // ?login=1 → Modal automatisch öffnen
    if (new URLSearchParams(window.location.search).get("login") === "1") {
        openLoginModal();
    }
}

function openLoginModal() {
    const modal = document.getElementById("login-modal");
    if (modal) modal.style.display = "flex";
    document.getElementById("username")?.focus();
}

function closeLoginModal() {
    const modal = document.getElementById("login-modal");
    if (modal) modal.style.display = "none";
    const errorEl = document.getElementById("login-error");
    if (errorEl) errorEl.textContent = "";
}

async function onLoginSuccess() {
    const token = localStorage.getItem("token");
    try {
        const res = await fetch("/api/me", {
            headers: { Authorization: "Bearer " + token }
        });
        if (!res.ok) return;
        const me = await res.json();

        updateNav(me);

        if (window.CyberStocks) window.CyberStocks.reload();

    } catch (err) {
        console.error("Login-Fehler:", err);
    }
}

function updateNav(me) {
    const loginBtn    = document.getElementById("login-btn");
    const logoutLink  = document.getElementById("logout-link");
    const adminLink   = document.getElementById("admin-link");
    const profileLink = document.getElementById("profile-link");

    if (me) {
        if (loginBtn)    loginBtn.style.display    = "none";
        if (logoutLink)  logoutLink.style.display   = "inline";
        if (profileLink) {
            profileLink.style.display = "inline";
            profileLink.textContent   = `👤 ${me.username}`;
        }
        if (adminLink) adminLink.style.display =
            me.role === "admin" ? "inline" : "none";
    } else {
        if (loginBtn)    loginBtn.style.display    = "inline";
        if (logoutLink)  logoutLink.style.display   = "none";
        if (profileLink) profileLink.style.display  = "none";
        if (adminLink)   adminLink.style.display    = "none";
    }
}

window.CyberLogin = { init: initLoginModal, openModal: openLoginModal, updateNav };
