const WEATHER_ICONS = {
    0:"☀️", 1:"🌤️", 2:"⛅", 3:"☁️",
    45:"🌫️", 48:"🌫️",
    51:"🌦️", 53:"🌦️", 55:"🌧️",
    61:"🌧️", 63:"🌧️", 65:"🌧️",
    71:"🌨️", 73:"🌨️", 75:"❄️",
    80:"🌦️", 81:"🌧️", 82:"⛈️",
    95:"⛈️", 96:"⛈️", 99:"⛈️"
};

const WEATHER_WIND_DIRECTIONS = ["N","NO","O","SO","S","SW","W","NW"];
const WEATHER_DAYS = ["So","Mo","Di","Mi","Do","Fr","Sa"];

function windDirection(deg) {
    return WEATHER_WIND_DIRECTIONS[Math.round(deg / 45) % 8];
}

function weatherIcon(code) {
    return WEATHER_ICONS[code] || "🌡️";
}

function initWeather() {
    const input = document.getElementById("weather-plz");
    if (!input) return;

    const savedPlz = localStorage.getItem("weather-plz");
    if (savedPlz) {
        input.value = savedPlz;
        loadWeather(savedPlz);
    }

    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            const plz = input.value.trim();
            if (plz.length === 5 && /^\d+$/.test(plz)) {
                localStorage.setItem("weather-plz", plz);
                loadWeather(plz);
            }
        }
    });
}

async function loadWeather(plz) {
    const errorEl = document.getElementById("weather-error");
    if (errorEl) errorEl.style.display = "none";

    try {
        const res = await fetch(`/api/weather?plz=${plz}`);
        if (!res.ok) {
            if (errorEl) errorEl.style.display = "block";
            return;
        }
        const data = await res.json();
        renderWeather(data);
    } catch (err) {
        console.error("Wetter-Fehler:", err);
        if (errorEl) errorEl.style.display = "block";
    }
}

function renderWeather(data) {
    const c = data.current;

    document.getElementById("weather-icon").textContent =
        weatherIcon(c.weather_code);
    document.getElementById("weather-temp").textContent =
        `${Math.round(c.temperature_2m)}°C`;
    document.getElementById("weather-location").textContent =
        data.location;
    document.getElementById("weather-feels").textContent =
        `Gefühlt: ${Math.round(c.apparent_temperature)}°C`;
    document.getElementById("weather-wind").textContent =
        `💨 ${Math.round(c.wind_speed_10m)} km/h ${windDirection(c.wind_direction_10m)}`;
    document.getElementById("weather-humidity").textContent =
        `💧 ${c.relative_humidity_2m}%`;

    const forecastEl = document.getElementById("weather-forecast");
    if (!forecastEl) return;
    forecastEl.innerHTML = "";

    const daily = data.daily;
    for (let i = 0; i < 3; i++) {
        const date = new Date(daily.time[i]);
        const day = WEATHER_DAYS[date.getDay()];
        const icon = weatherIcon(daily.weather_code[i]);
        const max = Math.round(daily.temperature_2m_max[i]);
        const min = Math.round(daily.temperature_2m_min[i]);

        const el = document.createElement("div");
        el.className = "forecast-day";
        el.innerHTML = `
            <span class="forecast-day__name">${day}</span>
            <span class="forecast-day__icon">${icon}</span>
            <span class="forecast-day__temp">${max}° <small>${min}°</small></span>
        `;
        forecastEl.appendChild(el);
    }
}

window.CyberWeather = { init: initWeather };
