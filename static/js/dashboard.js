let runs = [];
let currentRunIndex = 0;
let map = null;
let routeLayer = null;


async function loadTodayRuns() {
    const container = document.getElementById("run-container");

    try {
        const response = await fetch("/api/today");
        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Could not load runs.");
        }

        document.getElementById("run-date").textContent =
            formatDate(data.date);

        runs = data.runs;

        if (runs.length === 0) {
            container.innerHTML = `
                <p class="status-message">
                    No runs recorded today.
                </p>
            `;
            return;
        }

        renderCurrentRun();
    } catch (error) {
        container.innerHTML = `
            <div class="status-message error-message">
                <p>Unable to load today's runs.</p>
                <p>${escapeHtml(error.message)}</p>
            </div>
        `;

        console.error(error);
    }
}


container.innerHTML = `
    <div class="run-top-row">
        <div>
            <p class="run-label">Today's activity</p>
            <h2 class="run-name">
                ${escapeHtml(run.name || "Run")}
            </h2>
        </div>

        <div class="run-position">
            ${currentRunIndex + 1} of ${runs.length}
        </div>
    </div>

    <div class="run-dashboard-layout">
        <div class="run-map-panel">
            ${
                run.route_polyline
                    ? '<div id="route-map"></div>'
                    : `
                        <div class="no-map">
                            No route map is available for this run.
                        </div>
                    `
            }
        </div>

        <div class="run-stats-panel">
            <div class="dashboard-stat">
                <span class="metric-label">Distance</span>
                <span class="dashboard-stat-value">
                    ${formatValue(run.distance_miles)}
                </span>
                <span class="metric-unit">mi</span>
            </div>

            <div class="dashboard-stat">
                <span class="metric-label">Average pace</span>
                <span class="dashboard-stat-value">
                    ${escapeHtml(run.pace_per_mile || "—")}
                </span>
                <span class="metric-unit">/mi</span>
            </div>

            <div class="dashboard-stat">
                <span class="metric-label">Average HR</span>
                <span class="dashboard-stat-value">
                    ${run.average_heart_rate ?? "—"}
                </span>
                <span class="metric-unit">
                    ${run.average_heart_rate ? "bpm" : ""}
                </span>
            </div>
        </div>
    </div>

    ${
        runs.length > 1
            ? `
                <div class="run-navigation">
                    <button
                        id="previous-run"
                        class="navigation-button"
                        type="button"
                    >
                        ← Previous
                    </button>

                    <button
                        id="next-run"
                        class="navigation-button"
                        type="button"
                    >
                        Next →
                    </button>
                </div>
            `
            : ""
    }
`;


function connectNavigationButtons() {
    const previousButton =
        document.getElementById("previous-run");

    const nextButton =
        document.getElementById("next-run");

    if (!previousButton || !nextButton) {
        return;
    }

    previousButton.addEventListener("click", () => {
        currentRunIndex =
            (currentRunIndex - 1 + runs.length) % runs.length;

        renderCurrentRun();
    });

    nextButton.addEventListener("click", () => {
        currentRunIndex =
            (currentRunIndex + 1) % runs.length;

        renderCurrentRun();
    });
}


function renderMap(encodedPolyline) {
    destroyMap();

    const routeCoordinates = decodePolyline(encodedPolyline);

    if (routeCoordinates.length === 0) {
        return;
    }

    map = L.map("route-map", {
        zoomControl: true,
        attributionControl: true
    });

    L.tileLayer(
        "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 19,
            attribution:
                '&copy; <a href="https://www.openstreetmap.org/copyright">' +
                "OpenStreetMap</a> contributors"
        }
    ).addTo(map);

    routeLayer = L.polyline(routeCoordinates, {
        color: "#fc4c02",
        weight: 5,
        opacity: 0.95,
        lineCap: "round",
        lineJoin: "round"
    }).addTo(map);

    map.fitBounds(routeLayer.getBounds(), {
        padding: [28, 28],
        maxZoom: 16
    });

    const startPoint = routeCoordinates[0];
    const endPoint =
        routeCoordinates[routeCoordinates.length - 1];

    L.circleMarker(startPoint, {
        radius: 7,
        color: "#ffffff",
        weight: 2,
        fillColor: "#22c55e",
        fillOpacity: 1
    })
        .addTo(map)
        .bindPopup("Start");

    L.circleMarker(endPoint, {
        radius: 7,
        color: "#ffffff",
        weight: 2,
        fillColor: "#ef4444",
        fillOpacity: 1
    })
        .addTo(map)
        .bindPopup("Finish");

    window.setTimeout(() => {
        map.invalidateSize();
    }, 100);
}


function destroyMap() {
    if (map) {
        map.remove();
        map = null;
        routeLayer = null;
    }
}


/*
 * Decodes a Google encoded polyline into:
 * [
 *   [latitude, longitude],
 *   ...
 * ]
 */
function decodePolyline(encoded) {
    const coordinates = [];

    let index = 0;
    let latitude = 0;
    let longitude = 0;

    while (index < encoded.length) {
        const latitudeResult =
            decodePolylineValue(encoded, index);

        latitude += latitudeResult.value;
        index = latitudeResult.nextIndex;

        const longitudeResult =
            decodePolylineValue(encoded, index);

        longitude += longitudeResult.value;
        index = longitudeResult.nextIndex;

        coordinates.push([
            latitude / 100000,
            longitude / 100000
        ]);
    }

    return coordinates;
}


function decodePolylineValue(encoded, startIndex) {
    let result = 0;
    let shift = 0;
    let index = startIndex;
    let byte;

    do {
        byte = encoded.charCodeAt(index) - 63;
        index += 1;

        result |= (byte & 0x1f) << shift;
        shift += 5;
    } while (byte >= 0x20 && index < encoded.length);

    const value =
        result & 1
            ? ~(result >> 1)
            : result >> 1;

    return {
        value,
        nextIndex: index
    };
}


function formatDate(dateString) {
    if (!dateString) {
        return "";
    }

    const date = new Date(`${dateString}T12:00:00`);

    return date.toLocaleDateString("en-US", {
        weekday: "long",
        month: "long",
        day: "numeric"
    });
}


function formatValue(value) {
    if (value === null || value === undefined) {
        return "—";
    }

    return Number(value).toFixed(2);
}


function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


loadTodayRuns();