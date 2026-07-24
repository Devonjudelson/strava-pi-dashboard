const WEEKLY_GOAL = 70;

let weeklyChart = null;


async function loadWeeklyMileage() {
    const container =
        document.getElementById("weekly-container");

    try {
        const response = await fetch("/api/weekly");
        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.error || "Unable to load weekly mileage."
            );
        }

        renderWeeklyMileage(data);
    } catch (error) {
        container.innerHTML = `
            <div class="status-message error-message">
                <p>Unable to load weekly mileage.</p>
                <p>${escapeHtml(error.message)}</p>
            </div>
        `;
    }
}


function renderWeeklyMileage(data) {
    const container =
        document.getElementById("weekly-container");

    const weekStart =
        document.getElementById("week-start");

    weekStart.textContent =
        `Week of ${data.week_start}`;

    const percentage = Math.min(
        (data.total_miles / WEEKLY_GOAL) * 100,
        100
    );

    container.innerHTML = `
        <section class="weekly-card">
            <div class="weekly-summary">
                <div>
                    <span class="metric-label">
                        Total mileage
                    </span>

                    <span class="weekly-total">
                        ${data.total_miles.toFixed(1)}
                    </span>

                    <span class="metric-unit">
                        miles
                    </span>
                </div>

                <div>
                    <span class="metric-label">
                        Runs
                    </span>

                    <span class="weekly-run-count">
                        ${data.run_count}
                    </span>
                </div>
            </div>

            <div class="weekly-chart-wrapper">
                <canvas id="weekly-mileage-chart"></canvas>
            </div>

            <div class="weekly-goal-heading">
                <span>
                    Weekly goal
                </span>

                <span>
                    ${percentage.toFixed(0)}%
                    · ${data.total_miles.toFixed(1)}
                    of ${WEEKLY_GOAL} miles
                </span>
            </div>

            <div class="progress-track">
                <div
                    class="progress-fill"
                    style="width: ${percentage}%"
                ></div>
            </div>
        </section>
    `;

    createWeeklyChart(data.days);
}


function createWeeklyChart(days) {
    const canvas =
        document.getElementById("weekly-mileage-chart");

    const labels = days.map(
        (day) => day.day.slice(0, 3)
    );

    const mileage = days.map(
        (day) => day.miles
    );

    if (weeklyChart) {
        weeklyChart.destroy();
    }

    weeklyChart = new Chart(canvas, {
        type: "bar",

        data: {
            labels,

            datasets: [
                {
                    label: "Miles",
                    data: mileage,
                    backgroundColor: "#fc4c02",
                    borderRadius: 6,
                    borderSkipped: false,
                    maxBarThickness: 54,
                },
            ],
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,

            plugins: {
                legend: {
                    display: false,
                },

                tooltip: {
                    callbacks: {
                        label(context) {
                            return `${context.raw.toFixed(1)} miles`;
                        },
                    },
                },
            },

            scales: {
                x: {
                    grid: {
                        display: false,
                    },

                    border: {
                        display: false,
                    },

                    ticks: {
                        color: "#94a3b8",
                    },
                },

                y: {
                    beginAtZero: true,

                    grid: {
                        color: "rgba(148, 163, 184, 0.12)",
                    },

                    border: {
                        display: false,
                    },

                    ticks: {
                        color: "#94a3b8",

                        callback(value) {
                            return `${value} mi`;
                        },
                    },
                },
            },
        },
    });
}


function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


loadWeeklyMileage();