// ── Hilfsfunktionen ──────────────────────────────────

function authHeader() {
    return { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
}

const TYPE_ICONS = {
    video: '🎬', artikel: '📰', tool: '🔧',
    dokument: '📄', 'präsentation': '📊'
}

function escHtml(str) {
    if (!str) return ''
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
}

function relativeTime(isoString) {
    if (!isoString) return ''
    const diff    = Date.now() - new Date(isoString).getTime()
    const minutes = Math.floor(diff / 60000)
    if (minutes < 1)  return 'gerade eben'
    if (minutes < 60) return `vor ${minutes} Minute${minutes === 1 ? '' : 'n'}`
    const hours = Math.floor(minutes / 60)
    if (hours < 24)   return `vor ${hours} Stunde${hours === 1 ? '' : 'n'}`
    const days = Math.floor(hours / 24)
    return `vor ${days} Tag${days === 1 ? '' : 'en'}`
}

function extractDomain(url) {
    try { return new URL(url).hostname } catch { return url }
}

function snoozeDate(days) {
    const d = new Date()
    d.setDate(d.getDate() + days)
    return d.toISOString()
}

function debounce(fn, ms) {
    let timer
    return (...args) => {
        clearTimeout(timer)
        timer = setTimeout(() => fn(...args), ms)
    }
}

// ── Karte bauen ───────────────────────────────────────

function buildCardHTML(link) {
    const title = link.title || link.url
    const icon  = TYPE_ICONS[link.content_type] || '📰'

    const thumbnail = link.image_url
        ? `<img class="inbox-card__thumbnail" src="${escHtml(link.image_url)}" alt="" loading="lazy" />`
        : `<div class="inbox-card__thumbnail inbox-card__thumbnail--icon">${icon}</div>`

    const tags = (link.tags || [])
        .map(t => `<span class="inbox-tag">${escHtml(t)}</span>`)
        .join('')

    const statusClass = link.status === 'neu' ? 'inbox-status--neu' : 'inbox-status--gesehen'

    return `
        ${thumbnail}
        <div class="inbox-card__body">
            <a class="inbox-card__title" href="#" data-url="${escHtml(link.url)}">${escHtml(title)}</a>
            <div class="inbox-card__meta">
                <span class="inbox-domain">${escHtml(extractDomain(link.url))}</span>
                <span class="inbox-time">${relativeTime(link.created_at)}</span>
                <span class="inbox-status ${statusClass}">${escHtml(link.status)}</span>
            </div>
            <div class="inbox-card__tags">${tags}</div>
            <div class="inbox-card__actions">
                <button class="inbox-btn inbox-btn--open">Öffnen</button>
                <div class="inbox-snooze-wrap">
                    <button class="inbox-btn inbox-btn--snooze">Snooze ▾</button>
                    <div class="inbox-snooze-menu" style="display:none">
                        <button class="inbox-snooze-opt" data-days="1">Morgen (+1 Tag)</button>
                        <button class="inbox-snooze-opt" data-days="3">In 3 Tagen</button>
                        <button class="inbox-snooze-opt" data-days="7">Nächste Woche</button>
                    </div>
                </div>
                <button class="inbox-btn inbox-btn--archive">Archivieren</button>
            </div>
        </div>
    `
}

// ── Link öffnen + als gesehen markieren ──────────────

async function openLink(id, url) {
    await fetch(`/api/links/${id}`, {
        method:  'PATCH',
        headers: { ...authHeader(), 'Content-Type': 'application/json' },
        body:    JSON.stringify({ status: 'gesehen' })
    })
    if (url) window.open(url, '_blank')
    loadInbox()
}

// ── Inbox rendern ─────────────────────────────────────

function renderLinks(links) {
    const list  = document.getElementById('inbox-list')
    const empty = document.getElementById('inbox-empty')
    list.innerHTML = ''

    if (links.length === 0) {
        empty.style.display = 'block'
        return
    }
    empty.style.display = 'none'

    links.forEach(link => {
        const card = document.createElement('div')
        card.className  = 'inbox-card'
        card.dataset.id = link.id
        card.innerHTML  = buildCardHTML(link)
        list.appendChild(card)

        const id        = link.id
        const titleLink = card.querySelector('.inbox-card__title')

        titleLink?.addEventListener('click', e => {
            e.preventDefault()
            openLink(id, titleLink.dataset.url)
        })

        card.querySelector('.inbox-btn--open')?.addEventListener('click', () => {
            openLink(id, titleLink?.dataset.url)
        })

        card.querySelector('.inbox-btn--snooze')?.addEventListener('click', e => {
            e.stopPropagation()
            const menu = card.querySelector('.inbox-snooze-menu')
            if (menu) menu.style.display = menu.style.display === 'none' ? 'block' : 'none'
        })

        card.querySelectorAll('.inbox-snooze-opt').forEach(btn => {
            btn.addEventListener('click', async () => {
                const days = parseInt(btn.dataset.days, 10)
                await fetch(`/api/links/${id}`, {
                    method:  'PATCH',
                    headers: { ...authHeader(), 'Content-Type': 'application/json' },
                    body:    JSON.stringify({ snooze_until: snoozeDate(days) })
                })
                loadInbox()
            })
        })

        card.querySelector('.inbox-btn--archive')?.addEventListener('click', async () => {
            await fetch(`/api/links/${id}`, {
                method:  'PATCH',
                headers: { ...authHeader(), 'Content-Type': 'application/json' },
                body:    JSON.stringify({ status: 'archiviert' })
            })
            loadInbox()
        })
    })
}

// ── Inbox laden ───────────────────────────────────────

async function loadInbox() {
    const search = document.getElementById('inbox-search').value
    const type   = document.getElementById('inbox-filter-type').value
    const status = document.getElementById('inbox-filter-status').value

    const params = new URLSearchParams()
    if (search) params.set('q', search)
    if (type)   params.set('type', type)
    if (status) params.set('status', status)

    const res  = await fetch(`/api/links?${params}`, { headers: authHeader() })
    const data = await res.json()
    renderLinks(data.links || [])
}

// ── AI-Settings ───────────────────────────────────────

async function loadAiSettings() {
    const res  = await fetch('/api/settings/ai', { headers: authHeader() })
    const data = await res.json()
    const el   = document.getElementById('ai-status')
    if (el) el.textContent = data.configured
        ? `✓ Konfiguriert (${data.provider} / ${data.model})`
        : 'Nicht konfiguriert'
}

async function saveAiSettings() {
    const key   = document.getElementById('ai-api-key').value.trim()
    const model = document.getElementById('ai-model').value
    const status = document.getElementById('ai-save-status')
    if (!key) return

    const res  = await fetch('/api/settings/ai', {
        method:  'POST',
        headers: { ...authHeader(), 'Content-Type': 'application/json' },
        body:    JSON.stringify({ provider: 'claude', model, api_key: key })
    })
    const data = await res.json()
    if (status) status.textContent = data.success ? '✓ Gespeichert' : '✗ Fehler'
    loadAiSettings()
}

// ── Bookmarklet ───────────────────────────────────────

function buildBookmarklet() {
    const base = window.location.origin
    const code = `javascript:(function(){fetch('${base}/api/links',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+localStorage.getItem('token')},body:JSON.stringify({url:location.href})}).then(r=>r.json()).then(d=>alert(d.title?'✓ '+d.title:'✓ Gespeichert')).catch(()=>alert('✗ Fehler'));})();`
    const link = document.getElementById('bookmarklet-link')
    if (link) link.href = code
}

// ── Init ──────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    if (!localStorage.getItem('token')) {
        window.location.href = '/'
        return
    }

    if (window.CyberLogin) window.CyberLogin.init()

    // Nav-State wiederherstellen
    fetch('/api/me', { headers: authHeader() })
        .then(r => r.ok ? r.json() : null)
        .then(me => { if (me && window.CyberLogin) window.CyberLogin.updateNav(me) })
        .catch(() => {})

    loadInbox()
    loadAiSettings()
    buildBookmarklet()

    document.getElementById('inbox-search')
        ?.addEventListener('input', debounce(loadInbox, 300))
    document.getElementById('inbox-filter-type')
        ?.addEventListener('change', loadInbox)
    document.getElementById('inbox-filter-status')
        ?.addEventListener('change', loadInbox)
    document.getElementById('ai-save-btn')
        ?.addEventListener('click', saveAiSettings)

    // Snooze-Menus schließen bei Klick außerhalb
    document.addEventListener('click', e => {
        if (!e.target.closest('.inbox-snooze-wrap')) {
            document.querySelectorAll('.inbox-snooze-menu')
                .forEach(m => m.style.display = 'none')
        }
    })
})
