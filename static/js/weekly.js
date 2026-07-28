let weeklyChart = null;
let weeklyHistory = [];
Chart.register(ChartDataLabels);

const chartCanvas = document.getElementById(
    "weekly-mileage-chart"
);

const titleElement = document.getElementById(
    "weekly-chart-title"
);

const subtitleElement = document.getElementById(
    "weekly-chart-subtitle"
);

const eyebrowElement = document.getElementById(
    "chart-eyebrow"
);

const summaryElement = document.getElementById(
    "weekly-summary"
);

const statusElement = document.getElementById(
    "weekly-status"
);

const backButton = document.getElementById(
    "back-to-weeks"
);


/*
    Loads the last 10 weeks when the page first opens.
*/
async function loadWeeklyHistory() {
    statusElement.textContent =
        "Loading weekly mileage...";

    try {
        const response = await fetch(
            "/api/weekly-history"
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.error ||
                "Unable to load weekly mileage."
            );
        }

        weeklyHistory = data.weeks;

        renderWeeklyHistory(data.weeks);

        statusElement.textContent = "";
    } catch (error) {
        statusElement.textContent = error.message;
    }
}


/*
    Displays one column for each week.
*/
function renderWeeklyHistory(weeks) {
    destroyCurrentChart();

    eyebrowElement.textContent = "Training history";
    titleElement.textContent = "Last 10 Weeks";
    subtitleElement.textContent =
        "Select a week to see its daily breakdown.";

    backButton.hidden = true;

    const totalMiles = weeks.reduce(
        (total, week) => total + week.miles,
        0
    );

    const averageMiles = (
        totalMiles / weeks.length
    );

    const highestWeek = weeks.reduce(
        (highest, week) =>
            week.miles > highest.miles
                ? week
                : highest,
        weeks[0]
    );

    summaryElement.innerHTML = `
        <div>
            <span class="metric-label">
                10-week average
            </span>

            <strong>
                ${averageMiles.toFixed(1)} mi
            </strong>
        </div>

        <div>
            <span class="metric-label">
                Highest week
            </span>

            <strong>
                ${highestWeek.miles.toFixed(1)} mi
            </strong>
        </div>
    `;

    weeklyChart = new Chart(chartCanvas, {
        type: "bar",

        data: {
            labels: weeks.map(
                (week) => week.label
            ),

            datasets: [{
                label: "Weekly mileage",

                data: weeks.map(
                    (week) => week.miles
                ),

                backgroundColor: weeks.map(
                    (week) =>
                        week.current_week
                            ? "#fc4c02"
                            : "rgba(252, 76, 2, 0.55)"
                ),

                hoverBackgroundColor: "#fc4c02",
                borderRadius: 6,
                borderSkipped: false,
                maxBarThickness: 48,
            }],
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
    padding: {
        top: 24,
    },
},

            onHover(event, chartElements) {
                event.native.target.style.cursor =
                    chartElements.length
                        ? "pointer"
                        : "default";
            },

            onClick(event, chartElements) {
                if (!chartElements.length) {
                    return;
                }

                const selectedIndex =
                    chartElements[0].index;

                const selectedWeek =
                    weeks[selectedIndex];

                loadDailyBreakdown(
                    selectedWeek.week_start
                );
            },

            plugins: {
                legend: {
                    display: false,
                },

                datalabels: {
        anchor: "end",
        align: "top",
        offset: 2,
        color: "#ffffff",
        font: {
            weight: "bold",
            size: 11,
        },

        formatter(value) {
            if (value === 0) {
                return "";
            }

            return value.toFixed(1);
        },
    },

                tooltip: {
                    callbacks: {
                        title(context) {
                            const index =
                                context[0].dataIndex;

                            return weeks[index].full_label;
                        },

                        label(context) {
                            const week =
                                weeks[context.dataIndex];

                            return [
                                `${week.miles.toFixed(1)} miles`,
                                `${week.run_count} runs`,
                            ];
                        },

                        afterLabel() {
                            return "Click for daily details";
                        },
                    },
                },
            },

            scales: {
                x: {
                    grid: {
                        display: false,
                    },

                    ticks: {
                        maxRotation: 45,
                        minRotation: 0,
                    },
                },

                y: {
                    beginAtZero: true,

                    ticks: {
                        callback(value) {
                            return `${value} mi`;
                        },
                    },
                },
            },
        },
    });
}


/*
    Requests the Monday-Sunday breakdown
    for the week the user clicked.
*/
async function loadDailyBreakdown(weekStart) {
    statusElement.textContent =
        "Loading daily mileage...";

    try {
        const query = new URLSearchParams({
            week_start: weekStart,
        });

        const response = await fetch(
            `/api/weekly?${query}`
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.error ||
                "Unable to load daily mileage."
            );
        }

        renderDailyBreakdown(data);

        statusElement.textContent = "";
    } catch (error) {
        statusElement.textContent = error.message;
    }
}


/*
    Replaces the 10-week chart with
    a Monday-Sunday chart.
*/
function renderDailyBreakdown(data) {
    destroyCurrentChart();

    eyebrowElement.textContent = "Daily breakdown";
    titleElement.textContent = data.week_label;
    subtitleElement.textContent =
        `${data.run_count} runs during this week`;

    backButton.hidden = false;

    summaryElement.innerHTML = `
        <div>
            <span class="metric-label">
                Weekly mileage
            </span>

            <strong>
                ${data.total_miles.toFixed(1)} mi
            </strong>
        </div>

        <div>
            <span class="metric-label">
                Runs
            </span>

            <strong>
                ${data.run_count}
            </strong>
        </div>
    `;

    weeklyChart = new Chart(chartCanvas, {
        type: "bar",

        data: {
            labels: data.days.map(
                (day) => day.short_day
            ),

            datasets: [{
                label: "Daily mileage",

                data: data.days.map(
                    (day) => day.miles
                ),

                backgroundColor: "#fc4c02",
                hoverBackgroundColor: "#e34402",
                borderRadius: 6,
                borderSkipped: false,
                maxBarThickness: 52,
            }],
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
    padding: {
        top: 24,
    },
},

            plugins: {
                legend: {
                    display: false,
                },

                datalabels: {
        anchor: "end",
        align: "top",
        offset: 2,
        color: "#ffffff",
        font: {
            weight: "bold",
            size: 11,
        },

        formatter(value) {
            if (value === 0) {
                return "";
            }

            return value.toFixed(1);
        },
    },

                tooltip: {
                    callbacks: {
                        label(context) {
                            return (
                                `${Number(context.raw).toFixed(1)} miles`
                            );
                        },
                    },
                },
            },

            scales: {
                x: {
                    grid: {
                        display: false,
                    },
                },

                y: {
                    beginAtZero: true,

                    ticks: {
                        callback(value) {
                            return `${value} mi`;
                        },
                    },
                },
            },
        },
    });
}


/*
    Chart.js requires the old chart
    to be destroyed before drawing another one
    on the same canvas.
*/
function destroyCurrentChart() {
    if (weeklyChart) {
        weeklyChart.destroy();
        weeklyChart = null;
    }
}


/*
    Returns from the daily chart
    to the last-10-weeks chart.
*/
backButton.addEventListener("click", () => {
    renderWeeklyHistory(weeklyHistory);
});


/*
    Runs automatically when weekly.js loads.
*/
loadWeeklyHistory();