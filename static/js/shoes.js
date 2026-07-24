const RETIREMENT_MILES = 400;


async function loadShoes() {
    const container =
        document.getElementById("shoe-container");

    try {
        const response = await fetch("/api/shoes");
        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.error || "Could not load shoes."
            );
        }

        if (data.shoe_count === 0) {
            container.innerHTML = `
                <p class="status-message">
                    No shoes were found in your Strava account.
                </p>
            `;
            return;
        }

        container.innerHTML = data.shoes
            .map(createShoeCard)
            .join("");
    } catch (error) {
        container.innerHTML = `
            <div class="status-message error-message">
                <p>Unable to load shoe data.</p>
                <p>${escapeHtml(error.message)}</p>
            </div>
        `;

        console.error(error);
    }
}

function createShoeCard(shoe) {
    const mileage = Number(shoe.distance_miles) || 0;

    const percentage = Math.min(
        (mileage / RETIREMENT_MILES) * 100,
        100
    );

    const remainingMiles = Math.max(
        RETIREMENT_MILES - mileage,
        0
    );

    return `
        <article class="shoe-card">
            <div class="shoe-card-header">
                <div>
                    <p class="run-label">
                        ${shoe.primary ? "Primary shoe" : "Running shoe"}
                    </p>

                    <h2 class="shoe-name">
                        ${escapeHtml(shoe.name)}
                    </h2>
                </div>

                ${
                    shoe.primary
                        ? '<span class="primary-badge">Primary</span>'
                        : ""
                }
            </div>

            <div class="shoe-mileage">
                <span class="shoe-mileage-value">
                    ${mileage.toFixed(1)}
                </span>

                <span class="metric-unit">miles</span>
            </div>

            <div class="progress-information">
                <span>
                    ${percentage.toFixed(0)}%
                </span>

                <span>
                </span>
            </div>

            <div
                class="progress-track"
                role="progressbar"
                aria-label="${escapeHtml(shoe.name)} mileage"
                aria-valuemin="0"
                aria-valuemax="${RETIREMENT_MILES}"
                aria-valuenow="${mileage}"
            >
                <div
                    class="progress-fill"
                    style="width: ${percentage}%"
                ></div>
            </div>

            <p class="retirement-target">
            </p>
        </article>
    `;
}


function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


loadShoes();