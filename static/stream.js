let streamHls  = null;
let streamList = [];

async function initStream() {
    const container = document.getElementById("stream-buttons");
    if (!container) return;

    const lang = window.i18n?.getLang() || "de";

    try {
        const res  = await fetch(`/api/streams?lang=${lang}`);
        const data = await res.json();
        streamList = data.streams || [];
    } catch (err) {
        console.error("Streams laden Fehler:", err);
    }

    if (streamList.length === 0) {
        const errorEl = document.getElementById("stream-error");
        if (errorEl) errorEl.style.display = "flex";
        return;
    }

    renderStreamButtons(streamList);

    const savedIndex = parseInt(localStorage.getItem("stream-index") || "0");
    loadStream(Math.min(savedIndex, streamList.length - 1));
}

function renderStreamButtons(streams) {
    const container = document.getElementById("stream-buttons");
    if (!container) return;
    container.innerHTML = "";

    streams.forEach((stream, i) => {
        const btn = document.createElement("button");
        btn.className     = "stream-btn";
        btn.dataset.index = i;
        btn.title         = stream.name;

        if (stream.logo) {
            const img   = document.createElement("img");
            img.src     = stream.logo;
            img.alt     = stream.name;
            img.onerror = () => { img.style.display = "none"; btn.textContent = stream.name; };
            btn.appendChild(img);
        } else {
            btn.textContent = stream.name;
        }

        btn.addEventListener("click", () => loadStream(i));
        container.appendChild(btn);
    });
}

function loadStream(index) {
    const stream = streamList[index];
    if (!stream) return;

    localStorage.setItem("stream-index", index);

    const video   = document.getElementById("stream-player");
    const errorEl = document.getElementById("stream-error");
    const titleEl = document.getElementById("stream-title");

    document.querySelectorAll(".stream-btn").forEach((btn, i) => {
        btn.classList.toggle("stream-btn--active", i === index);
    });

    if (titleEl) titleEl.textContent = stream.name;
    if (errorEl) errorEl.style.display = "none";
    if (video)   video.style.display = "block";

    if (streamHls) {
        streamHls.destroy();
        streamHls = null;
    }

    if (Hls.isSupported()) {
        streamHls = new Hls({ enableWorker: true, lowLatencyMode: true });
        streamHls.loadSource(stream.url);
        streamHls.attachMedia(video);

        streamHls.on(Hls.Events.ERROR, (event, data) => {
            if (data.fatal) {
                console.warn("Stream Fehler:", stream.name, data);
                if (errorEl) errorEl.style.display = "flex";
                if (video)   video.style.display = "none";
            }
        });

        streamHls.on(Hls.Events.MANIFEST_PARSED, () => {
            video.play().catch(() => {});
        });

    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
        video.src = stream.url;
        video.play().catch(() => {});
    } else {
        console.error("HLS wird nicht unterstützt");
    }
}

window.CyberStream = { init: initStream, reload: initStream };
