# cybernews

Einfach (ein paar Zeilen / fertige Bibliothek):

- Drag & Drop Kacheln — SortableJS, 1 Zeile
- Auto-Refresh — setInterval(fetchNews, 60000), 1 Zeile
- Dark Theme — CSS-Variablen, 10 Zeilen
- Kategorie-Filter — JS array filter, ~20 Zeilen
- "Live"-Indikator (pulsierender Punkt) — CSS animation, 5 Zeilen
- Relative Zeitangaben ("vor 5 Minuten") — 10 Zeilen JS


## Userverwaltung mit SQLite (in Python enthalten)
Passwörter werden verschlüsselt mit Bcrypt

## JWT
Zufallsstring für JWT-Secret-Key
```
python -c "import secrets; print(secrets.token_hex(32))"
```

## Bewegliche Kacheln
SortableJS — fertige Bibliothek

Sehr wenig Aufwand, eine Zeile um es zu aktivieren
Sieht sofort professionell aus
```
html<script src="https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js"></script>
<script>
  Sortable.create(document.querySelector('.news-grid'));
</script>
```


## Streams
Einbetten mit `<iframe>` und ein paar Buttons
```
const streams = [
  { name: "Al Jazeera", url: "https://www.youtube.com/embed/live_stream?channel=UCNye-wNBqNL5ZzHSJdpkDEA" },
  { name: "DW News",     url: "https://www.youtube.com/embed/live_stream?channel=UCknLrEdhRCp1aegoMqRaCZg" },
  { name: "BBC News",    url: "https://www.youtube.com/embed/live_stream?channel=UC16niRr50-MSBwiO3YDb3RA" },
  { name: "Euronews",   url: "https://www.youtube.com/embed/live_stream?channel=UCSrZ3UV4jOidv8ppoVuvW9Q" },
  { name: "ABC News",   url: "https://www.youtube.com/embed/live_stream?channel=UCBi2mrWuNuyYy4gbM6fU18Q" },
];
```


## Map - Leaflet
Option 2: Nur Ländergrenzen, keine Tiles (näher an WorldMonitor)

GeoJSON-Datei mit Ländergrenzen laden
Länder in 2 Farben einfärben (z.B. dunkelgrau + highlight für Länder mit News)
Kein Tile-Layer nötig — komplett custom
```
javascriptfetch('countries.geojson')
  .then(r => r.json())
  .then(data => {
    L.geoJSON(data, {
      style: { fillColor: '#1a1a2e', color: '#444', weight: 1 }
    }).addTo(map);
  });
```

Choropleth-Ansatz — kein Pin, sondern das Land selbst wird eingefärbt:
```
javascriptL.geoJSON(data, {
  style: feature => ({
    fillColor: hatNews(feature.properties.name) ? '#e63946' : '#1a1a2e',
    color: '#444',
    weight: 1,
    fillOpacity: 0.8
  })
}).addTo(map);
```
hatNews() prüft einfach ob du für dieses Land einen Artikel hast — wenn ja, rote Farbe, sonst dunkelgrau.


javascript// Beim Hovern aufhellen
```
onEachFeature: (feature, layer) => {
  layer.on('mouseover', () => layer.setStyle({ fillOpacity: 1 }));
  layer.on('click', () => filterNewsByCountry(feature.properties.name));
}
```
Klick auf ein Land → filtert die Newskacheln nach diesem Land