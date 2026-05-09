let mapInstance;
let mapGeojsonLayer;
let mapSelectedLayer = null;

function initMap() {
    const container = document.getElementById("map-container");
    if (!container) return;

    mapInstance = L.map("map-container", {
        center: [51.1657, 10.4515],
        zoom: 2,
        minZoom: 2,
        maxZoom: 6,
        zoomControl: true,
        attributionControl: false,
        worldCopyJump: true,
        maxBounds: [[-90, -180], [90, 180]],
        maxBoundsViscosity: 1.0,
    });

    container.style.background = "#4a4a4a";

    const ro = new ResizeObserver(() => mapInstance.invalidateSize());
    ro.observe(container);

    fetch("/api/geo/countries")
        .then(res => res.json())
        .then(data => {
            mapGeojsonLayer = L.geoJSON(data, {
                style: countryStyle,
                onEachFeature: onEachCountry
            }).addTo(mapInstance);
        })
        .catch(err => console.error("GeoJSON Ladefehler:", err));
}

function countryStyle() {
    return {
        fillColor: "#2a2a2a",
        fillOpacity: 1,
        color: "#8b949e",
        weight: 0.7,
        opacity: 1
    };
}

function highlightCountry(e) {
    e.target.setStyle({
        fillColor: "#3a3a3a",
        weight: 1.2,
        color: "#c9d1d9"
    });
}

function resetCountry(e) {
    if (e.target === mapSelectedLayer) return;
    mapGeojsonLayer.resetStyle(e.target);
}

function onCountryClick(e) {
    if (mapSelectedLayer) {
        mapGeojsonLayer.resetStyle(mapSelectedLayer);
    }

    e.target.setStyle({
        fillColor: "#c9d1d9",
        fillOpacity: 0.4,
        weight: 1.2,
        color: "#c9d1d9"
    });

    mapSelectedLayer = e.target;

    const props = e.target.feature.properties;
    console.log("Land angeklickt:", props.NAME || props.name, props.ISO_A2 || props.iso_a2);
}

function onEachCountry(feature, layer) {
    layer.on({
        mouseover: highlightCountry,
        mouseout:  resetCountry,
        click:     onCountryClick
    });

    const name = feature.properties.NAME || feature.properties.name || "";
    if (name) layer.bindTooltip(name, { sticky: true, className: "map-tooltip" });
}

function resizeMap() {
    if (!mapInstance) return;
    mapInstance.invalidateSize();
}

window.CyberMap = { init: initMap, resize: resizeMap };
