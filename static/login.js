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

    // Tab-Switcher
    document.getElementById("tab-login-btn")?.addEventListener("click", () => {
        document.getElementById("login-form-wrapper").style.display = "block";
        document.getElementById("register-form-wrapper").style.display = "none";
        document.getElementById("tab-login-btn").classList.add("auth-tab--active");
        document.getElementById("tab-register-btn").classList.remove("auth-tab--active");
    });

    document.getElementById("tab-register-btn")?.addEventListener("click", () => {
        document.getElementById("login-form-wrapper").style.display = "none";
        document.getElementById("register-form-wrapper").style.display = "block";
        document.getElementById("tab-register-btn").classList.add("auth-tab--active");
        document.getElementById("tab-login-btn").classList.remove("auth-tab--active");
    });

    // Registrierung
    document.getElementById("register-form")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const username  = document.getElementById("reg-username").value.trim();
        const password  = document.getElementById("reg-password").value;
        const password2 = document.getElementById("reg-password2").value;
        const errorEl   = document.getElementById("register-error");
        const successEl = document.getElementById("register-success");

        errorEl.textContent  = "";
        successEl.textContent = "";

        if (password !== password2) {
            errorEl.textContent = "Passwörter stimmen nicht überein.";
            return;
        }

        const res = await fetch("/api/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();
        if (res.ok) {
            successEl.textContent = "Account erstellt — du kannst dich jetzt einloggen.";
            document.getElementById("reg-username").value  = "";
            document.getElementById("reg-password").value  = "";
            document.getElementById("reg-password2").value = "";
        } else {
            errorEl.textContent = data.error || "Fehler bei der Registrierung.";
        }
    });
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
    const loginBtn   = document.getElementById("login-btn");
    const logoutLink = document.getElementById("logout-link");
    const adminLink  = document.getElementById("admin-link");

    if (me) {
        if (loginBtn)   loginBtn.style.display   = "none";
        if (logoutLink) logoutLink.style.display  = "inline";
        if (adminLink)  adminLink.style.display   =
            me.role === "admin" ? "inline" : "none";
    } else {
        if (loginBtn)   loginBtn.style.display   = "inline";
        if (logoutLink) logoutLink.style.display  = "none";
        if (adminLink)  adminLink.style.display   = "none";
    }
}

window.CyberLogin = { init: initLoginModal, openModal: openLoginModal, updateNav };
