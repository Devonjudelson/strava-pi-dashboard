async function loadTodayRuns() {
    const container = document.getElementById("run-container");

    try {
        const response = await fetch("/api/today");
        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Could not load runs.");
        }

        if (data.run_count === 0) {
            container.innerHTML = `
                <h2>Today's Runs</h2>
                <p>No runs recorded today.</p>
            `;
            return;
        }

        const run = data.runs[0];

        container.innerHTML = `
            <h2>Today's Runs</h2>
            <h3>${run.name}</h3>

            <p><strong>Distance:</strong> ${run.distance_miles} miles</p>
            <p><strong>Pace:</strong> ${run.pace_per_mile || "Unavailable"} /mi</p>
            <p><strong>Average HR:</strong> ${
                run.average_heart_rate
                    ? `${run.average_heart_rate} bpm`
                    : "Unavailable"
            }</p>
        `;
    } catch (error) {
        container.innerHTML = `
            <h2>Today's Runs</h2>
            <p>Unable to load run data.</p>
            <p>${error.message}</p>
        `;

        console.error(error);
    }
}

loadTodayRuns();