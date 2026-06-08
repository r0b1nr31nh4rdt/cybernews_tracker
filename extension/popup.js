const API = 'https://cybernewstracker-staging.up.railway.app'

// ── Hilfsfunktionen ───────────────────────────────────

function showStatus(msg, type = 'success') {
    document.querySelectorAll('#status').forEach(el => {
        el.textContent = msg
        el.className   = type
    })
}

async function getTokens() {
    return new Promise(resolve => {
        chrome.storage.local.get(['access_token', 'refresh_token'], resolve)
    })
}

async function saveTokens(access_token, refresh_token = null) {
    const data = { access_token }
    if (refresh_token) data.refresh_token = refresh_token
    return new Promise(resolve => chrome.storage.local.set(data, resolve))
}

async function clearTokens() {
    return new Promise(resolve => {
        chrome.storage.local.remove(['access_token', 'refresh_token'], resolve)
    })
}

// ── Token erneuern ────────────────────────────────────

async function refreshAccessToken() {
    const { refresh_token } = await getTokens()
    if (!refresh_token) return null

    const res = await fetch(`${API}/api/refresh`, {
        method:  'POST',
        headers: { 'Authorization': `Bearer ${refresh_token}` }
    })
    if (!res.ok) return null

    const data = await res.json()
    await saveTokens(data.access_token)
    return data.access_token
}

// ── API-Call mit automatischem Token-Refresh ──────────

async function fetchWithRefresh(url, options = {}) {
    const { access_token } = await getTokens()

    options.headers = {
        ...options.headers,
        'Authorization': `Bearer ${access_token}`
    }

    let res = await fetch(url, options)

    // Access Token abgelaufen → erneuern und nochmal
    if (res.status === 401) {
        const newToken = await refreshAccessToken()
        if (!newToken) return null  // Refresh Token auch abgelaufen

        options.headers['Authorization'] = `Bearer ${newToken}`
        res = await fetch(url, options)
    }

    return res
}

// ── Login ─────────────────────────────────────────────

async function login() {
    const username = document.getElementById('username').value.trim()
    const password = document.getElementById('password').value

    if (!username || !password) {
        showStatus('Bitte alle Felder ausfüllen', 'error')
        return
    }

    showStatus('Einloggen...', '')

    const res = await fetch(`${API}/api/login`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ username, password })
    })

    const data = await res.json()

    if (!res.ok) {
        showStatus('Login fehlgeschlagen', 'error')
        return
    }

    await saveTokens(data.access_token, data.refresh_token)
    showLoggedIn()
}

// ── Link speichern ────────────────────────────────────

async function saveCurrentTab() {
    showStatus('Speichern...', '')

    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })

    const res = await fetchWithRefresh(`${API}/api/links`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ url: tab.url })
    })

    if (!res) {
        showStatus('Sitzung abgelaufen — bitte neu einloggen', 'error')
        await clearTokens()
        showLoginForm()
        return
    }

    const data = await res.json()

    if (res.ok) {
        showStatus(data.title ? `✓ ${data.title}` : '✓ Gespeichert', 'success')
    } else {
        showStatus(`✗ Fehler: ${data.error || 'Unbekannt'}`, 'error')
    }
}

// ── UI-Zustände ───────────────────────────────────────

function showLoginForm() {
    document.getElementById('login-section').style.display = 'block'
    document.getElementById('main-section').style.display  = 'none'
}

function showLoggedIn() {
    document.getElementById('login-section').style.display = 'none'
    document.getElementById('main-section').style.display  = 'block'
    showStatus('', '')
}

// ── Init ──────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
    const { access_token } = await getTokens()
    if (access_token) {
        showLoggedIn()
    } else {
        showLoginForm()
    }

    document.getElementById('login-btn')
        ?.addEventListener('click', login)

    document.getElementById('save-btn')
        ?.addEventListener('click', saveCurrentTab)

    document.getElementById('logout-btn')
        ?.addEventListener('click', async () => {
            await clearTokens()
            showLoginForm()
        })

    // Enter im Login-Formular
    document.getElementById('password')
        ?.addEventListener('keydown', e => {
            if (e.key === 'Enter') login()
        })
})
