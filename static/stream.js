let streamHls = null;

async function initStream() {
    const container = document.getElementById("stream-buttons");
    if (!container) return;

    let streams = [];
    try {
        const res = await fetch("/api/streams");
        const data = await res.json();
        streams = data.streams || [];
    } catch (err) {
        console.error("Streams laden Fehler:", err);
    }

    if (streams.length === 0) {
        const errorEl = document.getElementById("stream-error");
        if (errorEl) errorEl.style.display = "flex";
        return;
    }

    streams.forEach((stream, i) => {
        const btn = document.createElement("button");
        btn.textContent = stream.name;
        btn.className = "stream-btn";
        btn.dataset.index = i;
        btn.addEventListener("click", () => loadStream(i, streams));
        container.appendChild(btn);
    });

    const savedIndex = parseInt(localStorage.getItem("stream-index") || "0");
    loadStream(Math.min(savedIndex, streams.length - 1), streams);
}

function loadStream(index, streams) {
    const stream = streams[index];
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
        streamHls = new Hls({
            enableWorker: true,
            lowLatencyMode: true,
        });
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

window.CyberStream = { init: initStream };
