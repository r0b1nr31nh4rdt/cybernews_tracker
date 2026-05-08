let map;
let geojsonLayer;

function initMap() {
    const container = document.getElementById("map-container");
    if (!container) return;

    map = L.map("map-container", {
        center: [20, 10],
        zoom: 2,
        minZoom: 2,
        maxZoom: 6,
        zoomControl: true,
        attributionControl: false,
        worldCopyJump: false,
    });

    container.style.background = "#4a4a4a";

    fetch("/api/geo/countries")
        .then(res => res.json())
        .then(data => {
            geojsonLayer = L.geoJSON(data, {
                style: countryStyle,
                onEachFeature: onEachCountry
            }).addTo(map);
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
    geojsonLayer.resetStyle(e.target);
}

function onCountryClick(e) {
    const props = e.target.feature.properties;
    const countryName = props.NAME || props.name || "Unbekannt";
    const countryCode = props.ISO_A2 || props.iso_a2 || "";

    console.log("Land angeklickt:", countryName, countryCode);

    // TODO Briefing 09: Headlines nach Land filtern
    // filterNewsByCountry(countryCode);
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
    if (map) map.invalidateSize();
}

window.CyberMap = { init: initMap, resize: resizeMap };
