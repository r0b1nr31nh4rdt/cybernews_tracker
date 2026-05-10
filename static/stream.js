let streamSources = [];

let hls = null;
let activeIndex = parseInt(localStorage.getItem("stream-index") || "0");

async function initStream() {
    const container = document.getElementById("stream-buttons");
    if (!container) return;

    const lang = window.i18n?.getLang() || "de";
    try {
        const res  = await fetch(`/api/streams?lang=${lang}`);
        const data = await res.json();
        streamSources = data.streams || [];
    } catch (err) {
        console.error("Streams laden Fehler:", err);
        streamSources = [];
    }

    if (streamSources.length === 0) {
        const errorEl = document.getElementById("stream-error");
        if (errorEl) errorEl.style.display = "flex";
        return;
    }

    container.innerHTML = "";
    streamSources.forEach((stream, i) => {
        const btn = document.createElement("button");
        btn.className     = "stream-btn";
        btn.dataset.index = i;
        btn.title         = stream.name;

        if (stream.logo) {
            const img = document.createElement("img");
            img.src   = stream.logo;
            img.alt   = stream.name;
            btn.appendChild(img);
        } else {
            btn.textContent = stream.name;
        }

        btn.addEventListener("click", () => loadStream(i));
        container.appendChild(btn);
    });

    const savedIndex = parseInt(localStorage.getItem("stream-index") || "0");
    loadStream(Math.min(savedIndex, streamSources.length - 1));
}

function loadStream(index) {
    const stream = streamSources[index];
    if (!stream) return;

    activeIndex = index;
    localStorage.setItem("stream-index", index);

    const video = document.getElementById("stream-player");
    const errorEl = document.getElementById("stream-error");
    const titleEl = document.getElementById("stream-title");

    document.querySelectorAll(".stream-btn").forEach((btn, i) => {
        btn.classList.toggle("stream-btn--active", i === index);
    });

    if (titleEl) titleEl.textContent = stream.name;
    if (errorEl) errorEl.style.display = "none";
    if (video) video.style.display = "block";

    if (hls) {
        hls.destroy();
        hls = null;
    }

    if (Hls.isSupported()) {
        hls = new Hls({
            enableWorker: true,
            lowLatencyMode: true,
        });
        hls.loadSource(proxyUrl(stream.url));
        hls.attachMedia(video);

        hls.on(Hls.Events.ERROR, (event, data) => {
            if (data.fatal) {
                console.warn("Stream Fehler:", stream.name, data);
                if (errorEl) errorEl.style.display = "flex";
                if (video) video.style.display = "none";
            }
        });

        hls.on(Hls.Events.MANIFEST_PARSED, () => {
            video.play().catch(() => {});
        });

    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
        video.src = stream.url;
        video.play().catch(() => {});
    } else {
        console.error("HLS wird nicht unterstützt");
    }
}

function proxyUrl(url) {
    return `/api/stream-proxy?url=${encodeURIComponent(url)}`;
}

window.CyberStream = { init: initStream, reload: initStream };
