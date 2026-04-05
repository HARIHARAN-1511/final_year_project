// ============================================================
// PDRDSS Landing — EarthquakeTrack-Style Logic
// ============================================================

// ---------- STATE ----------
let allEarthquakes = [];       // full USGS data
let filteredEarthquakes = [];  // after table filters
let displayedCount = 0;
const PAGE_SIZE = 10;
let eqMap = null;
let markerLayer = null;
let searchMarker = null;
let userLat = null;
let userLon = null;

// USGS feed URLs
const USGS_FEEDS = {
    hour: {
        all: 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson',
        '1.0': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/1.0_hour.geojson',
        '2.5': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_hour.geojson',
        '4.5': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_hour.geojson',
        '6.0': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_hour.geojson',
    },
    day: {
        all: 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson',
        '1.0': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/1.0_day.geojson',
        '2.5': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson',
        '4.5': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson',
        '6.0': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_day.geojson',
    },
    week: {
        all: 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson',
        '1.0': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/1.0_week.geojson',
        '2.5': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojson',
        '4.5': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson',
        '6.0': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson',
    },
    month: {
        all: 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson',
        '1.0': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/1.0_month.geojson',
        '2.5': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_month.geojson',
        '4.5': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_month.geojson',
        '6.0': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson',
    },
};

// ============================================================
// INIT
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    loadMapEarthquakes();
    loadAllStats();

    setInterval(loadMapEarthquakes, 120000);   // refresh map every 2 min

    // Search
    document.getElementById('searchBtn').addEventListener('click', doSearch);
    document.getElementById('locationSearch').addEventListener('keydown', e => {
        if (e.key === 'Enter') doSearch();
    });
    document.getElementById('myLocationBtn').addEventListener('click', useMyLocation);

    // Map controls
    document.getElementById('mapTimeFilter').addEventListener('change', loadMapEarthquakes);
    document.getElementById('mapMagFilter').addEventListener('change', loadMapEarthquakes);
    document.getElementById('mapRefreshBtn').addEventListener('click', loadMapEarthquakes);

    // Table controls
    document.getElementById('tableSortBy').addEventListener('change', applyTableFilters);
    document.getElementById('tableMinMag').addEventListener('change', applyTableFilters);
    document.getElementById('loadMoreBtn').addEventListener('click', loadMoreRows);

    // Region buttons
    document.querySelectorAll('.region-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const lat = parseFloat(btn.dataset.lat);
            const lon = parseFloat(btn.dataset.lon);
            const name = btn.dataset.name;
            document.getElementById('locationSearch').value = name;
            userLat = lat;
            userLon = lon;
            eqMap.flyTo([lat, lon], 5, { duration: 1.5 });
            placeSearchMarker(lat, lon, name);
            applyTableFilters(); // recalc distances
        });
    });


});

// ============================================================
// MAP
// ============================================================
function initMap() {
    eqMap = L.map('earthquakeMap', {
        center: [20, 0],
        zoom: 2,
        minZoom: 2,
        maxZoom: 18,
        zoomControl: true,
        worldCopyJump: true,
    });

    // Dark tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap · CartoDB',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(eqMap);

    markerLayer = L.layerGroup().addTo(eqMap);
}

async function loadMapEarthquakes() {
    const timeRange = document.getElementById('mapTimeFilter').value;
    const minMag = document.getElementById('mapMagFilter').value;
    const statusEl = document.getElementById('mapStatusText');

    statusEl.textContent = 'Fetching earthquake data from USGS...';

    try {
        const feedUrl = USGS_FEEDS[timeRange]?.[minMag] || USGS_FEEDS[timeRange]?.['2.5'] || USGS_FEEDS.day['2.5'];
        const resp = await fetch(feedUrl);
        if (!resp.ok) throw new Error('USGS API error');
        const data = await resp.json();

        allEarthquakes = (data.features || []).map(f => {
            const p = f.properties;
            const c = f.geometry.coordinates;
            return {
                id: f.id,
                magnitude: p.mag,
                place: p.place || 'Unknown',
                time: p.time,
                timeISO: new Date(p.time).toISOString(),
                depth: c[2],
                lat: c[1],
                lon: c[0],
                tsunami: p.tsunami,
                felt: p.felt,
                alert: p.alert,
                mmi: p.mmi,
                url: p.url,
                detailUrl: p.detail,
            };
        });

        // Populate map markers
        markerLayer.clearLayers();
        allEarthquakes.forEach(eq => {
            const color = getMagColor(eq.magnitude);
            const radius = getMagRadius(eq.magnitude);
            const marker = L.circleMarker([eq.lat, eq.lon], {
                radius: radius,
                fillColor: color,
                color: color,
                weight: 1,
                opacity: 0.9,
                fillOpacity: 0.65,
            });

            marker.bindPopup(createPopupContent(eq), {
                maxWidth: 320,
                className: 'eq-popup'
            });

            marker.on('mouseover', function () { this.setStyle({ fillOpacity: 1, weight: 3 }); });
            marker.on('mouseout', function () { this.setStyle({ fillOpacity: 0.65, weight: 1 }); });

            markerLayer.addLayer(marker);
        });

        const timeLabels = { hour: 'past hour', day: 'past 24 hours', week: 'past 7 days', month: 'past 30 days' };
        statusEl.textContent = `${allEarthquakes.length} earthquakes shown — ${timeLabels[timeRange]} — Updated ${new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })}`;

        // Populate table
        applyTableFilters();

    } catch (err) {
        console.error('Map load error:', err);
        statusEl.textContent = 'Failed to load earthquake data — retrying...';
        setTimeout(loadMapEarthquakes, 10000);
    }
}

function getMagColor(mag) {
    if (mag >= 7.0) return '#dc2626';
    if (mag >= 6.0) return '#ef4444';
    if (mag >= 5.0) return '#f97316';
    if (mag >= 4.0) return '#eab308';
    if (mag >= 3.0) return '#a3e635';
    return '#22c55e';
}

function getMagRadius(mag) {
    if (mag >= 7.0) return 16;
    if (mag >= 6.0) return 13;
    if (mag >= 5.0) return 10;
    if (mag >= 4.0) return 8;
    if (mag >= 3.0) return 6;
    return 4;
}

function createPopupContent(eq) {
    const timeAgo = getTimeAgo(eq.timeISO);
    const dateStr = new Date(eq.time).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: true });
    const dist = (userLat != null && userLon != null) ? `${haversine(userLat, userLon, eq.lat, eq.lon).toFixed(1)} km from you` : '';
    const color = getMagColor(eq.magnitude);

    return `
        <div class="popup-inner">
            <div class="popup-mag" style="background:${color}">${eq.magnitude ? eq.magnitude.toFixed(1) : '?'}</div>
            <div class="popup-info">
                <div class="popup-title">${esc(eq.place)}</div>
                <div class="popup-meta">${timeAgo} · Depth: ${eq.depth ? eq.depth.toFixed(1) : '?'} km</div>
                <div class="popup-date">${dateStr} UTC</div>
                ${dist ? `<div class="popup-dist">📍 ${dist}</div>` : ''}
                ${eq.tsunami ? '<div class="popup-tsunami">⚠ Tsunami Warning</div>' : ''}
                ${eq.felt ? `<div class="popup-felt">Felt by ${eq.felt} people</div>` : ''}
                <div class="popup-actions">
                    <a href="javascript:void(0)" onclick="navigateToDashboard(${eq.lat}, ${eq.lon}, 'earthquake', '${esc(eq.place)}')" class="popup-analyze-btn">🔍 Analyze in Dashboard</a>
                </div>
            </div>
        </div>
    `;
}

// ============================================================
// SEARCH
// ============================================================
async function doSearch() {
    const query = document.getElementById('locationSearch').value.trim();
    if (!query) return;

    const searchBtn = document.getElementById('searchBtn');
    searchBtn.textContent = '...';
    searchBtn.disabled = true;

    try {
        // Try coordinates first
        const coordMatch = query.match(/^(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)$/);
        if (coordMatch) {
            userLat = parseFloat(coordMatch[1]);
            userLon = parseFloat(coordMatch[2]);
            eqMap.flyTo([userLat, userLon], 6, { duration: 1.5 });
            placeSearchMarker(userLat, userLon, `${userLat.toFixed(4)}, ${userLon.toFixed(4)}`);
            applyTableFilters();
            return;
        }

        // Geocode via backend
        const resp = await fetch(`/api/geocode?location=${encodeURIComponent(query)}`);
        if (!resp.ok) throw new Error('Location not found');
        const geo = await resp.json();

        userLat = geo.lat;
        userLon = geo.lon;
        eqMap.flyTo([userLat, userLon], 6, { duration: 1.5 });
        placeSearchMarker(userLat, userLon, geo.display_name);
        applyTableFilters();

    } catch (err) {
        console.error('Search failed:', err);
        alert('Location not found. Try a different search or use coordinates (lat, lon).');
    } finally {
        searchBtn.textContent = 'Search';
        searchBtn.disabled = false;
    }
}

function useMyLocation() {
    if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser.');
        return;
    }
    navigator.geolocation.getCurrentPosition(pos => {
        userLat = pos.coords.latitude;
        userLon = pos.coords.longitude;
        document.getElementById('locationSearch').value = `${userLat.toFixed(4)}, ${userLon.toFixed(4)}`;
        eqMap.flyTo([userLat, userLon], 8, { duration: 1.5 });
        placeSearchMarker(userLat, userLon, 'Your Location');
        applyTableFilters();
    }, () => {
        alert('Unable to retrieve your location.');
    });
}

function placeSearchMarker(lat, lon, label) {
    if (searchMarker) eqMap.removeLayer(searchMarker);
    searchMarker = L.marker([lat, lon], {
        icon: L.divIcon({
            className: 'search-pin-icon',
            html: `<div class="search-pin">📍</div>`,
            iconSize: [30, 30],
            iconAnchor: [15, 30],
        })
    }).addTo(eqMap);
    searchMarker.bindPopup(`<b>${esc(label)}</b><br>Searched location`).openPopup();
}

// ============================================================
// STATISTICS
// ============================================================
async function loadAllStats() {
    try {
        // 24h
        const resp24 = await fetch(USGS_FEEDS.day['2.5']);
        const data24 = await resp24.json();
        const count24 = data24.metadata?.count || data24.features?.length || 0;
        animateCounter('statEq24h', count24);

        // Find biggest today
        const features24 = data24.features || [];
        let maxMag = 0;
        features24.forEach(f => {
            if (f.properties.mag > maxMag) maxMag = f.properties.mag;
        });
        document.getElementById('statMaxMag').textContent = maxMag ? `M${maxMag.toFixed(1)}` : '—';

        // 7d
        const resp7d = await fetch(USGS_FEEDS.week['2.5']);
        const data7d = await resp7d.json();
        animateCounter('statEq7d', data7d.metadata?.count || data7d.features?.length || 0);

        // 30d
        const resp30d = await fetch(USGS_FEEDS.month['2.5']);
        const data30d = await resp30d.json();
        animateCounter('statEq30d', data30d.metadata?.count || data30d.features?.length || 0);

    } catch (err) {
        console.error('Stats error:', err);
    }
}

function animateCounter(elementId, target) {
    const el = document.getElementById(elementId);
    const duration = 1200;
    const steps = 40;
    const stepTime = duration / steps;
    let current = 0;
    const increment = target / steps;
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        el.textContent = Math.round(current).toLocaleString();
    }, stepTime);
}

// ============================================================
// TABLE
// ============================================================
function applyTableFilters() {
    const sortBy = document.getElementById('tableSortBy').value;
    const minMag = parseFloat(document.getElementById('tableMinMag').value) || 0;

    filteredEarthquakes = allEarthquakes.filter(eq => (eq.magnitude || 0) >= minMag);

    // Sort
    if (sortBy === 'time') {
        filteredEarthquakes.sort((a, b) => b.time - a.time);
    } else if (sortBy === 'magnitude') {
        filteredEarthquakes.sort((a, b) => (b.magnitude || 0) - (a.magnitude || 0));
    } else if (sortBy === 'depth') {
        filteredEarthquakes.sort((a, b) => (a.depth || 999) - (b.depth || 999));
    }

    // Update stats
    updateTrackerStats(filteredEarthquakes);

    // Reset pagination
    displayedCount = 0;
    document.getElementById('eqTableBody').innerHTML = '';
    loadMoreRows();
}

function loadMoreRows() {
    const tbody = document.getElementById('eqTableBody');
    const batch = filteredEarthquakes.slice(displayedCount, displayedCount + PAGE_SIZE);

    batch.forEach(eq => {
        const tr = document.createElement('tr');
        tr.className = 'eq-row';
        tr.setAttribute('data-lat', eq.lat);
        tr.setAttribute('data-lon', eq.lon);
        const color = getMagColor(eq.magnitude);
        const timeAgo = getTimeAgo(eq.timeISO);
        const dateStr = new Date(eq.time).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: true });
        const dist = (userLat != null && userLon != null)
            ? `${haversine(userLat, userLon, eq.lat, eq.lon).toFixed(0)} km`
            : '—';

        tr.innerHTML = `
            <td>
                <span class="eq-mag-badge" style="background:${color}">${eq.magnitude ? eq.magnitude.toFixed(1) : '?'}</span>
            </td>
            <td>
                <div class="eq-place">${esc(eq.place)}</div>
                <div class="eq-coords">${eq.lat.toFixed(3)}, ${eq.lon.toFixed(3)}</div>
            </td>
            <td class="eq-depth">${eq.depth ? eq.depth.toFixed(1) : '?'} km</td>
            <td>
                <div class="eq-timeago">${timeAgo}</div>
                <div class="eq-date">${dateStr}</div>
            </td>
            <td class="eq-dist">${dist}</td>
            <td>
                <button class="eq-analyze-btn" onclick="event.stopPropagation();navigateToDashboard(${eq.lat}, ${eq.lon}, 'earthquake', '${esc(eq.place)}')">Analyze</button>
            </td>
        `;

        // Click to fly to location on map
        tr.addEventListener('click', () => {
            eqMap.flyTo([eq.lat, eq.lon], 8, { duration: 1 });
            // find and open popup
            markerLayer.eachLayer(layer => {
                if (layer.getLatLng &&
                    Math.abs(layer.getLatLng().lat - eq.lat) < 0.001 &&
                    Math.abs(layer.getLatLng().lng - eq.lon) < 0.001) {
                    layer.openPopup();
                }
            });
        });

        tbody.appendChild(tr);
    });

    displayedCount += batch.length;

    // Update footer
    document.getElementById('eqTableCount').textContent = `${displayedCount} of ${filteredEarthquakes.length} earthquakes shown`;
    document.getElementById('eqTableUpdated').textContent = `Updated: ${new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })}`;

    // Show/hide load more
    const loadMoreDiv = document.getElementById('eqLoadMore');
    if (displayedCount < filteredEarthquakes.length) {
        loadMoreDiv.style.display = 'block';
    } else {
        loadMoreDiv.style.display = 'none';
    }
}

function updateTrackerStats(eqs) {
    document.getElementById('tstatTotal').textContent = eqs.length;
    document.getElementById('tstatMajor').textContent = eqs.filter(e => (e.magnitude || 0) >= 6.0).length;
    document.getElementById('tstatStrong').textContent = eqs.filter(e => (e.magnitude || 0) >= 5.0 && (e.magnitude || 0) < 6.0).length;
    document.getElementById('tstatModerate').textContent = eqs.filter(e => (e.magnitude || 0) >= 4.0 && (e.magnitude || 0) < 5.0).length;
    document.getElementById('tstatLight').textContent = eqs.filter(e => (e.magnitude || 0) < 4.0).length;
}



// ============================================================
// UTILITIES
// ============================================================
function getTimeAgo(timeVal) {
    if (!timeVal) return '';
    const ts = typeof timeVal === 'number' ? timeVal : new Date(timeVal).getTime();
    const diff = Date.now() - ts;
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
}

function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

function haversine(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function navigateToDashboard(lat, lon, type, location) {
    const params = new URLSearchParams({
        lat: lat,
        lon: lon,
        type: type,
        location: location
    });
    window.location.href = `/earthquake/dashboard?${params.toString()}`;
}
