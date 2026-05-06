
document.addEventListener('DOMContentLoaded', async () => {
    requireAuth();

    // Elements
    const totalEl = document.getElementById('totalAnalyses');
    const highEl = document.getElementById('highPriority');
    const rateEl = document.getElementById('criticalRate');
    const ctx = document.getElementById('severityChart').getContext('2d');

    try {
        const response = await fetch('/api/stats', {
            headers: getAuthHeaders()
        });

        if (!response.ok) throw new Error("Failed to load stats");

        const data = await response.json();

        // Update Key Metrics
        totalEl.textContent = data.total_analyses;
        highEl.textContent = data.high_priority;

        const rate = data.total_analyses > 0
            ? Math.round((data.high_priority / data.total_analyses) * 100)
            : 0;
        rateEl.textContent = `${rate}%`;

        // Prepare Chart Data
        const severities = data.severity_distribution || {};
        const labels = Object.keys(severities);
        const values = Object.values(severities);

        // Map common severities to colors
        const colors = labels.map(l => {
            if (l === 'SEVERE' || l === 'CATASTROPHIC') return '#ef4444'; // Red
            if (l === 'MODERATE') return '#f97316'; // Orange
            if (l === 'MINOR' || l === 'NONE') return '#22c55e'; // Green
            return '#cbd5e1'; // Gray
        });

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors,
                    borderColor: '#1e293b',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#94a3b8' }
                    },
                    title: {
                        display: true,
                        text: 'Alert Severity Distribution',
                        color: '#f8fafc',
                        font: { size: 16 }
                    }
                }
            }
        });
        // --- New: Real-Time Live Feed Chart ---
        const liveFeedCtx = document.getElementById('liveFeedChart').getContext('2d');
        try {
            const feedResponse = await fetch('/api/live-feed');
            if (feedResponse.ok) {
                const feedData = await feedResponse.json();
                const eqCount = feedData.earthquakes ? feedData.earthquakes.length : 0;
                const cyCount = feedData.cyclones ? feedData.cyclones.length : 0;

                new Chart(liveFeedCtx, {
                    type: 'bar',
                    data: {
                        labels: ['Earthquakes (24h)', 'Active Cyclones'],
                        datasets: [{
                            label: 'Global Threats',
                            data: [eqCount, cyCount],
                            backgroundColor: ['#38bdf8', '#fbbf24'],
                            borderWidth: 0,
                            borderRadius: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            title: {
                                display: true,
                                text: 'Real-Time Global Disasters',
                                color: '#f8fafc',
                                font: { size: 16 }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                grid: { color: '#334155' },
                                ticks: { color: '#94a3b8', stepSize: 5 }
                            },
                            x: {
                                grid: { display: false },
                                ticks: { color: '#94a3b8' }
                            }
                        }
                    }
                });
            }
        } catch (feedErr) {
            console.error("Failed to load live feed chart:", feedErr);
        }

    } catch (err) {
        console.error(err);
        totalEl.textContent = "Err";
    }
});
