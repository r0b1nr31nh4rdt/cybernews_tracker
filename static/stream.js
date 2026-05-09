const STREAM_SOURCES = [
    { name: "Sky News",   url: "https://linear901-oo-hls0-prd-gtm.delivery.skycdp.com/17501/sde-fast-skynews/master.m3u8" },
    { name: "Euronews",   url: "https://dash4.antik.sk/live/test_euronews/playlist.m3u8" },
    { name: "DW News",    url: "https://dwamdstream103.akamaized.net/hls/live/2015526/dwstream103/master.m3u8" },
    { name: "France 24",  url: "https://amg00106-france24-france24-samsunguk-qvpp8.amagi.tv/playlist/amg00106-france24-france24-samsunguk/playlist.m3u8" },
    { name: "Al Arabiya", url: "https://live.alarabiya.net/alarabiapublish/alarabiya.smil/playlist.m3u8" },
    { name: "Al Jazeera", url: "https://live-hls-apps-aje-fa.getaj.net/AJE/index.m3u8" },
];

let streamHls = null;
let streamActiveIndex = parseInt(localStorage.getItem("stream-index") || "0");

function initStream() {
    const container = document.getElementById("stream-buttons");
    if (!container) return;

    STREAM_SOURCES.forEach((stream, i) => {
        const btn = document.createElement("button");
        btn.textContent = stream.name;
        btn.className = "stream-btn";
        btn.dataset.index = i;
        btn.addEventListener("click", () => loadStream(i));
        container.appendChild(btn);
    });

    loadStream(streamActiveIndex);
}

function loadStream(index) {
    const stream = STREAM_SOURCES[index];
    if (!stream) return;

    streamActiveIndex = index;
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
                if (video) video.style.display = "none";
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
