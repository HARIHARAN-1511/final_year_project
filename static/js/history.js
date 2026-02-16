
document.addEventListener('DOMContentLoaded', async () => {
    requireAuth(); // Check if logged in

    const tableBody = document.querySelector('#historyTable tbody');
    const loadingDiv = document.getElementById('loading');

    try {
        const response = await fetch('/api/history', {
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }
            throw new Error('Failed to fetch history');
        }

        const logs = await response.json();
        loadingDiv.style.display = 'none';

        if (logs.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5" style="text-align:center">No analysis logs found.</td></tr>';
            return;
        }

        logs.forEach(log => {
            const row = document.createElement('tr');

            // Determine label based on score (since API returns basic log)
            // Ideally backend returns label or we re-calc. 
            // Let's use simple logic matching frontend
            let label = "LOW";
            if (log.priority_score >= 85) label = "CRITICAL";
            else if (log.priority_score >= 60) label = "HIGH";
            else if (log.priority_score >= 30) label = "MEDIUM";

            const date = new Date(log.timestamp).toLocaleString();

            row.innerHTML = `
                <td>${date}</td>
                <td>${log.location_name}</td>
                <td>${log.severity}</td>
                <td>${log.priority_score}</td>
                <td><span class="badge badge-${label}">${label}</span></td>
            `;
            tableBody.appendChild(row);
        });

    } catch (err) {
        console.error(err);
        loadingDiv.textContent = 'Error loading history logs.';
    }
});
