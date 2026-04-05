// ============================================================
// PDRDSS Cyclone Landing — Cyclone-Focused Logic
// ============================================================

// ---------- STATE ----------
let activeCyclones = [];
let userLat = null;
let userLon = null;
let cycloneMap = null;
let markerLayer = null;
let searchMarker = null;

// ============================================================
// INIT
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    loadCycloneData();
    setInterval(loadCycloneData, 300000); // refresh every 5 min

    // Search
    document.getElementById('searchBtn').addEventListener('click', doSearch);
    document.getElementById('locationSearch').addEventListener('keydown', e => {
        if (e.key === 'Enter') doSearch();
    });
    document.getElementById('myLocationBtn').addEventListener('click', useMyLocation);

    // Region buttons
    document.querySelectorAll('.region-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const lat = parseFloat(btn.dataset.lat);
            const lon = parseFloat(btn.dataset.lon);
            const name = btn.dataset.name;
            document.getElementById('locationSearch').value = name;
            userLat = lat;
            userLon = lon;
            cycloneMap.flyTo([lat, lon], 5, { duration: 1.5 });
            placeSearchMarker(lat, lon, name);
        });
    });
});

// ============================================================
// MAP
// ============================================================
function initMap() {
    cycloneMap = L.map('cycloneMap', {
        center: [15, -60],
        zoom: 3,
        minZoom: 2,
        maxZoom: 18,
        zoomControl: true,
        worldCopyJump: true,
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap · CartoDB',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(cycloneMap);

    markerLayer = L.layerGroup().addTo(cycloneMap);
}

async function loadCycloneData() {
    const statusEl = document.getElementById('mapStatusText');
    statusEl.textContent = 'Fetching active cyclone data from NOAA...';

    try {
        // Fetch from NOAA NHC GeoJSON
        const resp = await fetch('https://www.nhc.noaa.gov/CurrentSurges.json');
        let storms = [];

        // Also try the backend cyclone endpoint for broader data
        try {
            const backendResp = await fetch('/api/cyclone?lat=0&lon=0');
            if (backendResp.ok) {
                const bdata = await backendResp.json();
                if (bdata.storms && bdata.storms.length > 0) {
                    storms = bdata.storms;
                }
            }
        } catch (e) {
            console.log('Backend cyclone fetch fell back');
        }

        // Also fetch the NHC active storms RSS → GeoJSON
        try {
            const nhcResp = await fetch('https://www.nhc.noaa.gov/CurrentSurges.json');
            if (nhcResp.ok) {
                const nhcData = await nhcResp.json();
                if (nhcData.currentSurges) {
                    // Process if available
                }
            }
        } catch (e) {
            // NHC may not be available
        }

        activeCyclones = storms;
        markerLayer.clearLayers();

        if (storms.length > 0) {
            storms.forEach(storm => {
                if (!storm.lat || !storm.lon) return;
                const windKt = parseInt(storm.intensity_kt) || 0;
                const color = getCycloneColor(windKt);
                const radius = getCycloneRadius(windKt);

                const marker = L.circleMarker([storm.lat, storm.lon], {
                    radius: radius,
                    fillColor: color,
                    color: color,
                    weight: 2,
                    opacity: 0.9,
                    fillOpacity: 0.6,
                });

                const catInfo = getSaffirCategory(windKt);
                marker.bindPopup(`
                    <div class="popup-inner">
                        <div class="popup-mag" style="background:${color}">${catInfo.emoji}</div>
                        <div class="popup-info">
                            <div class="popup-title">${esc(storm.name || 'Active Storm')}</div>
                            <div class="popup-meta">${catInfo.cat} · ${windKt} kt (${Math.round(windKt * 1.852)} km/h)</div>
                            <div class="popup-date">${storm.basin || ''}</div>
                            <div class="popup-actions">
                                <a href="javascript:void(0)" onclick="navigateToDashboard(${storm.lat}, ${storm.lon}, 'cyclone', '${esc(storm.name || 'Active Cyclone')}')" class="popup-analyze-btn">🔍 Analyze in Dashboard</a>
                            </div>
                        </div>
                    </div>
                `, { maxWidth: 320, className: 'eq-popup' });

                marker.on('mouseover', function () { this.setStyle({ fillOpacity: 1, weight: 3 }); });
                marker.on('mouseout', function () { this.setStyle({ fillOpacity: 0.6, weight: 2 }); });

                markerLayer.addLayer(marker);
            });
            statusEl.textContent = `${storms.length} active storm(s) shown — Updated ${new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })}`;
        } else {
            statusEl.textContent = `No active tropical cyclones at this time — Updated ${new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })}`;
        }

        updateCycloneStats(storms);

    } catch (err) {
        console.error('Cyclone load error:', err);
        statusEl.textContent = 'Checking for active cyclones...';
        updateCycloneStats([]);
    }
}

function getCycloneColor(windKt) {
    if (windKt >= 137) return '#7c3aed';  // Cat 5
    if (windKt >= 113) return '#dc2626';  // Cat 4
    if (windKt >= 96) return '#ea580c';   // Cat 3
    if (windKt >= 83) return '#f97316';   // Cat 2
    if (windKt >= 64) return '#eab308';   // Cat 1
    if (windKt >= 34) return '#3b82f6';   // Tropical Storm
    return '#22c55e';                      // Depression
}

function getCycloneRadius(windKt) {
    if (windKt >= 137) return 18;
    if (windKt >= 96) return 15;
    if (windKt >= 64) return 12;
    if (windKt >= 34) return 9;
    return 6;
}

function getSaffirCategory(windKt) {
    if (windKt >= 137) return { cat: 'Category 5', emoji: '🌪️' };
    if (windKt >= 113) return { cat: 'Category 4', emoji: '🌪️' };
    if (windKt >= 96) return { cat: 'Category 3', emoji: '🌀' };
    if (windKt >= 83) return { cat: 'Category 2', emoji: '🌀' };
    if (windKt >= 64) return { cat: 'Category 1', emoji: '🌀' };
    if (windKt >= 34) return { cat: 'Tropical Storm', emoji: '🌧️' };
    return { cat: 'Tropical Depression', emoji: '🌬️' };
}

function updateCycloneStats(storms) {
    const totalEl = document.getElementById('statActive');
    const catEl = document.getElementById('statHurricane');
    const tsEl = document.getElementById('statTropical');
    const maxEl = document.getElementById('statMaxWind');

    if (totalEl) totalEl.textContent = storms.length;

    const hurricanes = storms.filter(s => (parseInt(s.intensity_kt) || 0) >= 64);
    const tropStorms = storms.filter(s => {
        const w = parseInt(s.intensity_kt) || 0;
        return w >= 34 && w < 64;
    });

    if (catEl) catEl.textContent = hurricanes.length;
    if (tsEl) tsEl.textContent = tropStorms.length;

    let maxWind = 0;
    storms.forEach(s => {
        const w = parseInt(s.intensity_kt) || 0;
        if (w > maxWind) maxWind = w;
    });
    if (maxEl) maxEl.textContent = maxWind > 0 ? `${maxWind} kt` : '—';
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
        const coordMatch = query.match(/^(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)$/);
        if (coordMatch) {
            userLat = parseFloat(coordMatch[1]);
            userLon = parseFloat(coordMatch[2]);
            cycloneMap.flyTo([userLat, userLon], 6, { duration: 1.5 });
            placeSearchMarker(userLat, userLon, `${userLat.toFixed(4)}, ${userLon.toFixed(4)}`);
            return;
        }

        const resp = await fetch(`/api/geocode?location=${encodeURIComponent(query)}`);
        if (!resp.ok) throw new Error('Location not found');
        const geo = await resp.json();

        userLat = geo.lat;
        userLon = geo.lon;
        cycloneMap.flyTo([userLat, userLon], 6, { duration: 1.5 });
        placeSearchMarker(userLat, userLon, geo.display_name);

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
        cycloneMap.flyTo([userLat, userLon], 6, { duration: 1.5 });
        placeSearchMarker(userLat, userLon, 'Your Location');
    }, () => {
        alert('Unable to retrieve your location.');
    });
}

function placeSearchMarker(lat, lon, label) {
    if (searchMarker) cycloneMap.removeLayer(searchMarker);
    searchMarker = L.marker([lat, lon], {
        icon: L.divIcon({
            className: 'search-pin-icon',
            html: `<div class="search-pin">📍</div>`,
            iconSize: [30, 30],
            iconAnchor: [15, 30],
        })
    }).addTo(cycloneMap);
    searchMarker.bindPopup(`<b>${esc(label)}</b><br>Searched location`).openPopup();
}

// ============================================================
// UTILITIES
// ============================================================
function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

function navigateToDashboard(lat, lon, type, location) {
    const params = new URLSearchParams({
        lat: lat,
        lon: lon,
        type: type,
        location: location
    });
    window.location.href = `/cyclone/dashboard?${params.toString()}`;
}
