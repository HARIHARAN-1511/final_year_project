/**
 * PDRDSS — Post-Disaster Rescue Decision Support System
 * Frontend Application Logic (v2.0)
 * 
 * ⚠ ACADEMIC PROTOTYPE — Decision support only.
 */

// ============================================================================
// Configuration
// ============================================================================
const MAPILLARY_CLIENT_TOKEN = '';

// ============================================================================
// State
// ============================================================================
const state = {
    map: null,
    center: [20, 0],
    zoom: 3,
    disasterCenter: null,
    layers: {
        damage: null,
        news: null,
        resources: null,
    },
    baseLayers: {},
    activeBaseLayer: 'satellite',
    labelsLayer: null,
    cache: {},
    lastAnalysis: null,
};

// ============================================================================
// Initialization
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    initEventListeners();

    // Check if navigated from live feed with exact coordinates
    const params = new URLSearchParams(window.location.search);
    const paramLat = params.get('lat');
    const paramLon = params.get('lon');
    const paramType = params.get('type');
    const paramLocation = params.get('location');

    if (paramLat && paramLon && paramType) {
        // Pre-fill the inputs
        const locationInput = document.getElementById('locationInput');
        const disasterTypeSelect = document.getElementById('disasterType');
        if (locationInput) locationInput.value = paramLocation || `${paramLat}, ${paramLon}`;
        if (disasterTypeSelect) disasterTypeSelect.value = paramType;

        // Run analysis with exact coordinates (skip geocoding)
        runDirectAnalysis(parseFloat(paramLat), parseFloat(paramLon), paramType, paramLocation || `${paramLat}, ${paramLon}`);

        // Clean the URL so refreshing doesn't re-trigger
        window.history.replaceState({}, '', '/dashboard');
    }
});

// ============================================================================
// Analysis Pipeline
// ============================================================================

/**
 * Run analysis with exact lat/lon — skips geocoding.
 * Used when navigating from the live feed with known coordinates.
 */
async function runDirectAnalysis(lat, lon, disasterType, locationName) {
    setLoading(true);
    showSkeletons();

    try {
        const geo = {
            lat: lat,
            lon: lon,
            display_name: locationName,
            confidence: 'HIGH',
            importance: 1.0,
            source: 'live_feed'
        };

        updateTopBarGeo(geo, disasterType);
        state.disasterCenter = [lat, lon];
        state.map.flyTo(state.disasterCenter, 10, { duration: 1.2 });

        const analyzeResp = await fetch(`/api/analyze?lat=${lat}&lon=${lon}&disaster_type=${disasterType}&location_name=${encodeURIComponent(locationName)}`, {
            headers: getAuthHeaders()
        });

        if (analyzeResp.status === 401) {
            window.location.href = '/login';
            return;
        }

        if (!analyzeResp.ok) throw new Error('Analysis failed');
        const data = await analyzeResp.json();
        data.geo = geo;

        const cacheKey = `${locationName}|${disasterType}`;
        state.cache[cacheKey] = { data, time: Date.now() };
        state.lastAnalysis = data;

        renderAnalysis(data);
        document.getElementById('downloadPdfBtn').disabled = false;

    } catch (err) {
        console.error('Direct analysis error:', err);
        showErrorState(err.message);
    } finally {
        setLoading(false);
    }
}

async function runAnalysis() {
    const locationVal = document.getElementById('locationInput').value.trim();
    const disasterType = document.getElementById('disasterType').value;

    if (!locationVal) {
        showNotification('Please enter a location', 'warning');
        return;
    }

    const cacheKey = `${locationVal}|${disasterType}`;
    const cached = state.cache[cacheKey];
    if (cached && (Date.now() - cached.time < 5 * 60 * 1000)) {
        renderAnalysis(cached.data);
        return;
    }

    setLoading(true);
    showSkeletons();

    try {
        const geoResp = await fetch(`/api/geocode?location=${encodeURIComponent(locationVal)}`);
        if (!geoResp.ok) throw new Error((await geoResp.json()).detail || 'Geocoding failed');
        const geo = await geoResp.json();

        updateTopBarGeo(geo, disasterType);
        state.disasterCenter = [geo.lat, geo.lon];
        state.map.flyTo(state.disasterCenter, 10, { duration: 1.2 });

        const analyzeResp = await fetch(`/api/analyze?lat=${geo.lat}&lon=${geo.lon}&disaster_type=${disasterType}&location_name=${encodeURIComponent(geo.display_name)}`, {
            headers: getAuthHeaders()
        });

        if (analyzeResp.status === 401) {
            window.location.href = '/login';
            return;
        }

        if (!analyzeResp.ok) throw new Error('Analysis failed');
        const data = await analyzeResp.json();
        data.geo = geo;

        state.cache[cacheKey] = { data, time: Date.now() };
        state.lastAnalysis = data;

        renderAnalysis(data);
        document.getElementById('downloadPdfBtn').disabled = false;

    } catch (err) {
        console.error('Analysis error:', err);
        showErrorState(err.message);
    } finally {
        setLoading(false);
    }
}

function initMap() {
    state.map = L.map('map', {
        center: state.center,
        zoom: state.zoom,
        zoomControl: true,
        attributionControl: true,
    });

    // --- Base Layers ---
    state.baseLayers.satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Imagery &copy; Esri &mdash; Esri, Maxar, Earthstar Geographics',
        maxZoom: 19,
    });

    state.baseLayers.street = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
    });

    state.baseLayers.grid = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        maxZoom: 19,
        subdomains: 'abcd',
    });

    state.baseLayers.satellite.addTo(state.map);

    state.labelsLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19,
        pane: 'overlayPane',
    });
    state.labelsLayer.addTo(state.map);

    // Layer groups
    state.layers.damage = L.layerGroup().addTo(state.map);
    state.layers.news = L.layerGroup().addTo(state.map);
    state.layers.resources = L.layerGroup().addTo(state.map);

    state.map.on('click', onMapClick);
}

function initEventListeners() {
    document.getElementById('analyzeBtn').addEventListener('click', runAnalysis);
    document.getElementById('recenterBtn').addEventListener('click', recenterMap);
    document.getElementById('downloadPdfBtn').addEventListener('click', downloadPdfReport);

    document.getElementById('locationInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') runAnalysis();
    });

    // Layer toggles
    document.getElementById('layerDamage').addEventListener('change', (e) => toggleLayer('damage', e.target.checked));
    document.getElementById('layerNews').addEventListener('change', (e) => toggleLayer('news', e.target.checked));
    document.getElementById('layerResources').addEventListener('change', (e) => toggleLayer('resources', e.target.checked));

    // Map view toggle
    document.querySelectorAll('.map-view-btn').forEach(btn => {
        btn.addEventListener('click', () => switchBaseLayer(btn.dataset.view));
    });

    document.getElementById('svCloseBtn').addEventListener('click', closeStreetView);
}

// ============================================================================
// Map View Toggle
// ============================================================================
function switchBaseLayer(viewName) {
    if (!state.baseLayers[viewName] || state.activeBaseLayer === viewName) return;

    state.map.removeLayer(state.baseLayers[state.activeBaseLayer]);
    if (state.labelsLayer) state.map.removeLayer(state.labelsLayer);

    state.baseLayers[viewName].addTo(state.map);
    state.activeBaseLayer = viewName;

    if (viewName === 'satellite' && state.labelsLayer) state.labelsLayer.addTo(state.map);

    document.querySelectorAll('.map-view-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === viewName);
    });

    const note = document.querySelector('.imagery-note');
    if (note) {
        const msgs = {
            satellite: '📡 Base imagery is pre-disaster (not real-time capture) — Source: Esri, Maxar, Earthstar Geographics',
            street: '🗺️ OpenStreetMap street view — useful for road accessibility analysis',
            grid: '🏙️ Urban grid layout (CARTO Positron) — useful for block-level rescue planning',
        };
        note.textContent = msgs[viewName] || '';
    }
}

function toggleLayer(name, visible) {
    if (!state.layers[name]) return;
    visible ? state.map.addLayer(state.layers[name]) : state.map.removeLayer(state.layers[name]);
}

function recenterMap() {
    if (state.disasterCenter) state.map.flyTo(state.disasterCenter, 10, { duration: 1.5 });
}

// ============================================================================
// Street View Panel
// ============================================================================
function onMapClick(e) {
    openStreetView(e.latlng.lat, e.latlng.lng);
}

function openStreetView(lat, lon) {
    const panel = document.getElementById('streetViewPanel');
    const body = document.getElementById('svBody');
    panel.classList.remove('hidden');

    body.innerHTML = `<div class="sv-loading"><div class="spinner"></div><span>Looking for street imagery at ${lat.toFixed(4)}, ${lon.toFixed(4)}...</span></div>`;

    if (MAPILLARY_CLIENT_TOKEN) {
        const bbox = `${lon - 0.001},${lat - 0.001},${lon + 0.001},${lat + 0.001}`;
        fetch(`https://graph.mapillary.com/images?access_token=${MAPILLARY_CLIENT_TOKEN}&fields=id,thumb_2048_url,captured_at&bbox=${bbox}&limit=1`)
            .then(r => r.json())
            .then(data => {
                if (data.data && data.data.length > 0) {
                    const img = data.data[0];
                    body.innerHTML = `
                        <div class="sv-image-container">
                            <img src="${img.thumb_2048_url}" alt="Street view" class="sv-image" />
                            <div class="sv-meta">
                                <span>📍 ${lat.toFixed(4)}, ${lon.toFixed(4)}</span>
                                <span>📅 ${img.captured_at ? new Date(img.captured_at).toLocaleDateString() : 'Unknown'}</span>
                                <span>Source: Mapillary</span>
                            </div>
                        </div>`;
                } else {
                    showStreetViewUnavailable(body, lat, lon);
                }
            })
            .catch(() => showStreetViewUnavailable(body, lat, lon));
    } else {
        body.innerHTML = `
            <div class="sv-fallback">
                <iframe src="https://www.openstreetmap.org/export/embed.html?bbox=${lon - 0.005},${lat - 0.005},${lon + 0.005},${lat + 0.005}&layer=mapnik&marker=${lat},${lon}" class="sv-iframe" loading="lazy"></iframe>
                <div class="sv-meta">
                    <span>📍 ${lat.toFixed(4)}, ${lon.toFixed(4)}</span>
                    <span>Source: OpenStreetMap (no Mapillary API key)</span>
                </div>
            </div>`;
    }
}

function showStreetViewUnavailable(body, lat, lon) {
    body.innerHTML = `
        <div class="sv-unavailable">
            <div class="sv-unavail-icon">📷</div>
            <div class="sv-unavail-text">Street imagery not available for this area</div>
            <div class="sv-unavail-coords">📍 ${lat.toFixed(4)}, ${lon.toFixed(4)}</div>
            <div class="sv-unavail-hint">Try clicking closer to roads or urban areas</div>
        </div>`;
}

function closeStreetView() {
    document.getElementById('streetViewPanel').classList.add('hidden');
}



// ============================================================================
// Rendering
// ============================================================================
function renderAnalysis(data) {
    updateTopBar(data);
    updateDataFreshness(data);
    renderMapOverlays(data);
    renderDisasterInfo(data);
    renderPopulationExposure(data);
    renderTeams(data);
    renderConcerns(data);
    renderResources(data);
    renderAllocatedResources(data);
    renderNearbyCities(data);
    renderWeather(data);
    renderRecentEvents(data);
    renderNews(data);
    renderAiAnalysis(data);
    updateFreshnessBadges(data);
}

function updateTopBarGeo(geo, disasterType) {
    document.getElementById('infoDisasterType').textContent = disasterType.toUpperCase();
    document.getElementById('infoLocation').textContent = truncate(geo.display_name, 40);
    document.getElementById('infoCoords').textContent = `${geo.lat.toFixed(4)}, ${geo.lon.toFixed(4)}`;

    const confEl = document.getElementById('infoConfidence');
    confEl.textContent = (geo.confidence === 'HIGH' ? '🎯' : geo.confidence === 'MEDIUM' ? '📍' : '⚠') + ' ' + geo.confidence;
    confEl.className = 'info-value confidence-' + geo.confidence.toLowerCase();
}

function updateTopBar(data) {
    const badge = document.getElementById('priorityBadge');
    badge.className = 'priority-badge priority-' + (data.priority || 'none').toLowerCase();
    document.getElementById('priorityText').textContent = data.priority || 'STANDBY';

    if (data.timestamp) {
        document.getElementById('infoUpdated').textContent = new Date(data.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }) + ' UTC';
    }
}

function updateDataFreshness(data) {
    const strip = document.getElementById('dataFreshnessStrip');
    strip.classList.remove('hidden');
    const sources = data.data_sources || {};

    if (sources.disaster) {
        document.getElementById('freshTs_disaster').textContent = sources.disaster.status === 'ok' ? fmtTs(sources.disaster.timestamp) : 'Error';
    }
    document.getElementById('freshTs_cyclone').textContent = data.disaster_type === 'cyclone' && sources.disaster?.status === 'ok' ? fmtTs(sources.disaster.timestamp) : '—';
    if (sources.news) {
        document.getElementById('freshTs_news').textContent = sources.news.status === 'ok' ? fmtTs(sources.news.timestamp) : 'Error';
    }
    if (sources.imagery) {
        document.getElementById('freshTs_imagery').textContent = sources.imagery.status === 'pre-disaster' ? 'Pre-disaster' : fmtTs(sources.imagery.timestamp);
    }
}

function fmtTs(ts) {
    try { return new Date(ts).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }) + ' UTC'; } catch { return '—'; }
}

// --- Map Overlays ---
function renderMapOverlays(data) {
    state.layers.damage.clearLayers();
    state.layers.news.clearLayers();
    state.layers.resources.clearLayers();

    if (state.map.hasLayer(state.layers.damage)) {
        if (data.shakemap && data.shakemap.features) renderShakeMap(data.shakemap);
        else if (data.disaster_type === 'cyclone' && data.storms_wind_radii) renderWindRadii(data.storms_wind_radii);
    }
    if (data.disaster_info && data.disaster_info.magnitude) renderEpicenter(data);
    if (state.map.hasLayer(state.layers.resources) && data.resources?.data) renderResourceMarkers(data.resources.data);
}

function renderShakeMap(shakemap) {
    try {
        const geoLayer = L.geoJSON(shakemap, {
            style: (feature) => {
                const val = parseFloat(feature.properties?.value || feature.properties?.MMI || 0);
                let color = '#22c55e', opacity = 0.15;
                if (val >= 8) { color = '#dc2626'; opacity = 0.35; }
                else if (val >= 6) { color = '#ef4444'; opacity = 0.3; }
                else if (val >= 4) { color = '#f97316'; opacity = 0.25; }
                else if (val >= 2) { color = '#eab308'; opacity = 0.2; }
                return { color, weight: 2, opacity: 0.7, fillColor: color, fillOpacity: opacity };
            },
            onEachFeature: (f, layer) => {
                layer.bindPopup(`<div class="popup-title">Shaking Intensity</div><div class="popup-detail"><strong>MMI:</strong> ${f.properties?.value || f.properties?.MMI || 'N/A'}</div>`);
            }
        });
        state.layers.damage.addLayer(geoLayer);
    } catch (e) { console.warn('ShakeMap render failed:', e); }
}

function renderWindRadii(geojson) {
    try {
        const geoLayer = L.geoJSON(geojson, {
            style: (f) => ({
                color: f.properties?.stroke_color || '#f97316', weight: 2, opacity: 0.8,
                fillColor: f.properties?.fill_color || '#f97316', fillOpacity: f.properties?.fill_opacity || 0.15,
            }),
            onEachFeature: (f, layer) => layer.bindPopup(`<div class="popup-title">${f.properties?.label || 'Wind Zone'}</div>`),
        });
        state.layers.damage.addLayer(geoLayer);
    } catch (e) { console.warn('Wind radii render failed:', e); }
}

function renderEpicenter(data) {
    const info = data.disaster_info;
    const lat = data.coordinates?.lat, lon = data.coordinates?.lon;
    if (!lat || !lon) return;
    const mag = info.magnitude || 0;

    // Geographic radius in meters — scales with magnitude
    const baseRadius = Math.pow(10, mag * 0.4) * 500;

    // Outer impact zone (minor damage / felt area)
    state.layers.damage.addLayer(L.circle([lat, lon], {
        radius: baseRadius * 2.5,
        color: '#eab308', fillColor: '#eab308', fillOpacity: 0.08,
        weight: 1.5, opacity: 0.5, dashArray: '8,6',
    }).bindPopup(`<div class="popup-title">⚠️ Minor Impact Zone</div><div class="popup-detail">Radius: ${(baseRadius * 2.5 / 1000).toFixed(1)} km</div>`));

    // Mid impact zone (moderate damage)
    state.layers.damage.addLayer(L.circle([lat, lon], {
        radius: baseRadius * 1.5,
        color: '#f97316', fillColor: '#f97316', fillOpacity: 0.12,
        weight: 2, opacity: 0.6, dashArray: '6,4',
    }).bindPopup(`<div class="popup-title">🟠 Moderate Impact Zone</div><div class="popup-detail">Radius: ${(baseRadius * 1.5 / 1000).toFixed(1)} km</div>`));

    // Inner impact zone (severe damage)
    state.layers.damage.addLayer(L.circle([lat, lon], {
        radius: baseRadius,
        color: '#ef4444', fillColor: '#dc2626', fillOpacity: 0.18,
        weight: 2.5, opacity: 0.7,
    }).bindPopup(`<div class="popup-title">🔴 Severe Impact Zone</div><div class="popup-detail">Radius: ${(baseRadius / 1000).toFixed(1)} km</div>`));

    // Distance rings: 10km, 50km, 100km
    [10, 50, 100].forEach(r => {
        state.layers.damage.addLayer(L.circle([lat, lon], {
            radius: r * 1000, color: '#64748b', fillOpacity: 0, weight: 1, opacity: 0.4, dashArray: '4,8',
        }).bindTooltip(`${r} km`, { permanent: true, direction: 'right', className: 'distance-label' }));
    });

    // Pulsing epicenter marker
    const epicenterIcon = L.divIcon({
        html: `<div class="epicenter-pulse"><div class="pulse-ring"></div><div class="pulse-dot">⭐</div></div>`,
        className: 'epicenter-marker-wrapper', iconSize: [40, 40], iconAnchor: [20, 20],
    });
    state.layers.damage.addLayer(
        L.marker([lat, lon], { icon: epicenterIcon })
            .bindPopup(`<div class="popup-title">⭐ Epicenter — M${mag}</div><div class="popup-detail">${info.where || 'Unknown'}</div><div class="popup-detail">Depth: ${info.depth_km ? info.depth_km.toFixed(1) + ' km' : '—'}</div><div class="popup-detail">Felt: ${info.felt ? info.felt.toLocaleString() + ' reports' : 'N/A'}</div>`)
    );

    // Plot ALL recent earthquake events as circle markers
    if (data.recent_events && data.recent_events.length > 1) {
        data.recent_events.slice(1).forEach(ev => {
            if (!ev.lat || !ev.lon) return;
            const m = ev.magnitude || 0;
            const r = Math.max(3, m * 2.5) * 1000; // radius in meters
            const col = getMagColor(m);
            state.layers.damage.addLayer(
                L.circleMarker([ev.lat, ev.lon], {
                    radius: Math.max(4, m * 1.8), color: col, fillColor: col,
                    fillOpacity: 0.6, weight: 1.5, opacity: 0.8,
                }).bindPopup(`<div class="popup-title">M${m.toFixed(1)}</div><div class="popup-detail">${ev.place || 'Unknown'}</div><div class="popup-detail">Depth: ${ev.depth_km ? ev.depth_km.toFixed(1) + ' km' : '—'}</div><div class="popup-detail">${ev.time ? new Date(ev.time).toLocaleString() : ''}</div>`)
            );
        });
    }

    // Plot nearby cities as labeled markers
    if (data.nearby_cities && data.nearby_cities.length > 0) {
        data.nearby_cities.forEach(city => {
            if (!city.latitude || !city.longitude) return;
            const cityIcon = L.divIcon({
                html: `<div style="font-size:0.7rem;color:#f8fafc;background:#334155;padding:2px 6px;border-radius:4px;white-space:nowrap;border:1px solid #64748b;font-weight:600;">${city.name || 'City'}</div>`,
                className: 'city-label-marker', iconSize: [80, 20], iconAnchor: [40, 10],
            });
            state.layers.damage.addLayer(
                L.marker([city.latitude, city.longitude], { icon: cityIcon })
                    .bindPopup(`<div class="popup-title">🏙️ ${city.name}</div><div class="popup-detail">${city.distance} km ${city.direction} of epicenter</div>${city.population ? `<div class="popup-detail">Pop: ${city.population.toLocaleString()}</div>` : ''}`)
            );
        });
    }
}

function renderResourceMarkers(resources) {
    const icons = { hospital: { e: '🏥', c: '#3b82f6' }, fire_station: { e: '🚒', c: '#ef4444' }, police: { e: '🚔', c: '#8b5cf6' } };
    const all = [
        ...resources.hospitals.map(r => ({ ...r, type: 'hospital' })),
        ...resources.fire_stations.map(r => ({ ...r, type: 'fire_station' })),
        ...resources.police.map(r => ({ ...r, type: 'police' })),
    ];

    all.forEach(r => {
        if (!r.lat || !r.lon) return;
        const cfg = icons[r.type] || { e: '📍', c: '#60a5fa' };
        const icon = L.divIcon({
            html: `<div style="font-size:1.5rem;text-align:center;filter:drop-shadow(0 2px 4px rgba(0,0,0,0.5));">${cfg.e}</div>`,
            className: 'resource-marker', iconSize: [30, 30], iconAnchor: [15, 15],
        });
        state.layers.resources.addLayer(
            L.marker([r.lat, r.lon], { icon }).bindPopup(`<div class="popup-title">${cfg.e} ${r.name}</div><div class="popup-detail">Type: ${r.type.replace('_', ' ')}</div>`)
        );
    });
}


// --- Disaster Info Panel ---
function renderDisasterInfo(data) {
    const body = document.getElementById('panelInfoBody');
    const info = data.disaster_info;

    if (!info || info.message) {
        body.innerHTML = `<div class="empty-state-enhanced"><span class="empty-icon">${data.disaster_type === 'cyclone' ? '🌤️' : '📊'}</span><span>${info?.message || 'No disaster data available'}</span></div>`;
        return;
    }

    let html = '';

    // --- Helper for time ago ---
    const timeAgo = (sec) => {
        if (!sec) return '';
        const m = Math.floor(sec / 60);
        if (m < 1) return 'Just now';
        if (m < 60) return `${m} minute${m !== 1 ? 's' : ''} ago`;
        const h = Math.floor(m / 60);
        if (h < 24) return `${h} hour${h !== 1 ? 's' : ''} ago`;
        const d = Math.floor(h / 24);
        return `${d} day${d !== 1 ? 's' : ''} ago`;
    };

    if (data.disaster_type === 'earthquake') {
        const dist = info.distance_km !== undefined ? info.distance_km : '—';
        const ago = info.time_ago ? timeAgo(info.time_ago) : '';
        const userLoc = data.location || 'Search Location';
        const sigPct = Math.min(100, Math.round((info.significance || 0) / 10));

        html = `
            <div style="text-align:center; margin-bottom:1.2rem; padding-bottom:1.2rem; border-bottom:1px solid #e5e7eb;">
                <div style="font-size:1.6rem; font-weight:800; color:#1e293b; line-height:1.2; margin-bottom:0.4rem;">
                    <span style="color:${getMagColor(info.magnitude)};">M${info.magnitude}</span> Earthquake
                </div>
                <div style="font-size:1.05rem; color:#4b5563; margin-bottom:0.2rem;">
                    <strong>${dist} km</strong> from <span style="text-decoration:underline; text-decoration-color:#9ca3af;">${userLoc}</span>
                </div>
                <div style="font-size:0.9rem; color:#6b7280; font-weight:500;">${ago}</div>
                ${info.event_url ? `<a href="https://earthquake.usgs.gov${info.event_url}" target="_blank" rel="noopener" style="font-size:0.8rem;color:#3b82f6;text-decoration:none;font-weight:600;">🔗 View on USGS →</a>` : ''}
            </div>

            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:0.75rem; margin-bottom:1rem;">
                <div class="info-row" style="flex-direction:column; align-items:flex-start; gap:0.2rem;">
                    <span class="info-row-label">UTC Time</span>
                    <span class="info-row-value mono" style="font-size:0.85rem;">${info.when ? new Date(info.when).toUTCString().replace('GMT', '').trim() : '—'}</span>
                </div>
                <div class="info-row" style="flex-direction:column; align-items:flex-start; gap:0.2rem;">
                    <span class="info-row-label">Local Time</span>
                    <span class="info-row-value mono" style="font-size:0.85rem;">${info.when ? new Date(info.when).toLocaleString() : '—'}</span>
                </div>
            </div>

            <div class="info-row"><span class="info-row-label">Epicenter</span><span class="info-row-value" style="font-size:0.9rem;">${info.where || '—'}</span></div>
            <div class="info-row"><span class="info-row-label">Depth</span><span class="info-row-value mono">${info.depth_km ? info.depth_km.toFixed(1) + ' km' : '—'} <span style="color:#94a3b8;font-size:0.8rem;">${info.depth_class || ''}</span></span></div>
            <div class="info-row"><span class="info-row-label">Intensity (MMI)</span><span class="info-row-value mono">${info.mmi ? info.mmi.toFixed(1) : '—'} <span style="font-weight:700; color:${getMagColor(info.mmi || 0)};">${info.mmi_description || ''}</span></span></div>
            <div class="info-row"><span class="info-row-label">PAGER Alert</span><span class="info-row-value">${info.alert_level ? alertBadge(info.alert_level) : '—'}</span></div>
            <div class="info-row"><span class="info-row-label">Felt Reports</span><span class="info-row-value mono" style="font-weight:700;">${info.felt ? info.felt.toLocaleString() : '0'}</span></div>
            <div class="info-row"><span class="info-row-label">Tsunami</span><span class="info-row-value">${info.tsunami ? '<span style="color:#dc2626;font-weight:700;">⚠ WARNING</span>' : '<span style="color:#22c55e;">None</span>'}</span></div>
            <div class="info-row"><span class="info-row-label">Events in Region</span><span class="info-row-value mono" style="font-weight:700;">${info.total_events || 0}</span></div>
            <div class="info-row"><span class="info-row-label">Severity</span><span class="info-row-value">${severityBadge(data.severity)}</span></div>
            <div class="info-row"><span class="info-row-label">Status</span><span class="info-row-value">${info.status || '—'}</span></div>

            <div style="margin-top:1rem; padding-top:0.75rem; border-top:1px solid #e5e7eb;">
                <div style="font-size:0.8rem; color:#64748b; font-weight:600; margin-bottom:0.4rem;">SIGNIFICANCE SCORE</div>
                <div style="display:flex; align-items:center; gap:0.75rem;">
                    <div style="flex:1; background:#e2e8f0; border-radius:6px; height:10px; overflow:hidden;">
                        <div style="width:${sigPct}%; height:100%; background: linear-gradient(90deg, #22c55e, #eab308, #ef4444); border-radius:6px; transition:width 0.6s;"></div>
                    </div>
                    <span class="mono" style="font-weight:700; font-size:0.9rem; color:#1e293b;">${info.significance || 0}</span>
                </div>
            </div>

            ${data.tectonic_summary ? `
            <div style="margin-top:1rem; padding-top:0.75rem; border-top:1px solid #e5e7eb;">
                <div style="font-size:0.8rem; color:#64748b; font-weight:600; margin-bottom:0.4rem;">🌍 TECTONIC CONTEXT</div>
                <div style="font-size:0.85rem; color:#475569; line-height:1.5;">${data.tectonic_summary.substring(0, 500)}${data.tectonic_summary.length > 500 ? '...' : ''}</div>
            </div>` : ''}

            ${data.pager_data ? `
            <div style="margin-top:1rem; padding:0.75rem; background:#fef2f2; border-radius:8px; border-left:3px solid ${data.pager_data.alert_level === 'red' ? '#dc2626' : data.pager_data.alert_level === 'orange' ? '#f97316' : data.pager_data.alert_level === 'yellow' ? '#eab308' : '#22c55e'};">
                <div style="font-size:0.8rem; color:#64748b; font-weight:600; margin-bottom:0.3rem;">🚨 PAGER ALERT: ${(data.pager_data.alert_level || '').toUpperCase()}</div>
                <div style="font-size:0.85rem; color:#374151;">Max MMI: ${data.pager_data.max_mmi || '—'}</div>
            </div>` : ''}
        `;
    } else {
        // Rich cyclone panel — mirrors earthquake panel detail level
        const windKt = parseInt(info.intensity_kt) || 0;
        const windKph = Math.round(windKt * 1.852);
        const windMph = Math.round(windKt * 1.151);

        // Saffir-Simpson category helper
        const getSaffirCategory = (kt) => {
            if (kt >= 137) return { cat: 'Category 5', color: '#7c3aed', emoji: '🌪️' };
            if (kt >= 113) return { cat: 'Category 4', color: '#dc2626', emoji: '🌪️' };
            if (kt >= 96) return { cat: 'Category 3', color: '#ea580c', emoji: '🌀' };
            if (kt >= 83) return { cat: 'Category 2', color: '#f97316', emoji: '🌀' };
            if (kt >= 64) return { cat: 'Category 1', color: '#eab308', emoji: '🌀' };
            if (kt >= 34) return { cat: 'Tropical Storm', color: '#3b82f6', emoji: '🌧️' };
            if (kt > 0) return { cat: 'Tropical Depression', color: '#22c55e', emoji: '🌬️' };
            return { cat: 'Extratropical / Remnant', color: '#94a3b8', emoji: '☁️' };
        };

        const catInfo = getSaffirCategory(windKt);
        const intensPct = Math.min(100, Math.round((windKt / 200) * 100));
        const pressure = info.pressure ? `${info.pressure} hPa` : '—';

        html = `
            <div style="text-align:center; margin-bottom:1.2rem; padding-bottom:1.2rem; border-bottom:1px solid #e5e7eb;">
                <div style="font-size:2rem; margin-bottom:0.3rem;">${catInfo.emoji}</div>
                <div style="font-size:1.5rem; font-weight:800; color:${catInfo.color}; line-height:1.2; margin-bottom:0.3rem;">${catInfo.cat}</div>
                <div style="font-size:1rem; font-weight:700; color:#334155; margin-bottom:0.15rem;">${info.what || 'Active Cyclone'}</div>
                <div style="font-size:0.85rem; color:#64748b;">${info.where || '—'}</div>
            </div>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.75rem; margin-bottom:1rem;">
                <div class="info-row" style="flex-direction:column; align-items:flex-start; gap:0.2rem;">
                    <span class="info-row-label">Wind Speed</span>
                    <span class="info-row-value mono" style="font-size:1.05rem; font-weight:800; color:${catInfo.color};">${windKt} kt</span>
                    <span style="font-size:0.75rem; color:#94a3b8;">${windKph} km/h · ${windMph} mph</span>
                </div>
                <div class="info-row" style="flex-direction:column; align-items:flex-start; gap:0.2rem;">
                    <span class="info-row-label">Central Pressure</span>
                    <span class="info-row-value mono" style="font-size:1.05rem; font-weight:700;">${pressure}</span>
                    <span style="font-size:0.75rem; color:#94a3b8;">Lower = more intense</span>
                </div>
            </div>

            <div class="info-row"><span class="info-row-label">Severity (ML)</span>
                <span class="info-row-value">${severityBadge(data.severity)}
                    <span style="margin-left:6px;font-size:0.7rem;background:#f0fdf4;color:#166534;border:1px solid #bbf7d0;border-radius:4px;padding:1px 5px;">RandomForest</span>
                </span>
            </div>
            <div class="info-row"><span class="info-row-label">Classification</span><span class="info-row-value">${info.classification || catInfo.cat}</span></div>
            <div class="info-row"><span class="info-row-label">Active Storms</span><span class="info-row-value mono" style="font-weight:700;">${info.total_active || 0}</span></div>

            <div style="margin-top:1rem; padding-top:0.75rem; border-top:1px solid #e5e7eb;">
                <div style="font-size:0.8rem; color:#64748b; font-weight:600; margin-bottom:0.4rem;">WIND INTENSITY SCALE (SAFFIR-SIMPSON)</div>
                <div style="display:flex; align-items:center; gap:0.75rem;">
                    <div style="flex:1; background:#e2e8f0; border-radius:6px; height:10px; overflow:hidden;">
                        <div style="width:${intensPct}%; height:100%; background: linear-gradient(90deg, #22c55e, #eab308, #f97316, #dc2626, #7c3aed); border-radius:6px; transition:width 0.6s;"></div>
                    </div>
                    <span class="mono" style="font-weight:700; font-size:0.9rem; color:${catInfo.color};">${windKt} kt</span>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:0.65rem; color:#94a3b8; margin-top:4px;">
                    <span>TD ≤33</span><span>TS 34–63</span><span>Cat1–2 64–95</span><span>Cat3–5 ≥96</span>
                </div>
            </div>

            <div style="margin-top:1rem; padding:0.75rem; background:#eff6ff; border-radius:8px; border-left:3px solid #3b82f6;">
                <div style="font-size:0.8rem; color:#1e40af; font-weight:600; margin-bottom:0.3rem;">🤖 ML MODEL</div>
                <div style="font-size:0.8rem; color:#374151; line-height:1.5;">
                    Severity assessed by <strong>RandomForest classifier</strong> using wind (${windKt} kt), pressure (${pressure}), and intensification rate as features.
                </div>
            </div>`;
    }
    body.innerHTML = html;
}


// --- Population Exposure Panel ---
function renderPopulationExposure(data) {
    const body = document.getElementById('panelPopulationBody');
    const pop = data.population_exposure;
    if (!pop || data.severity === 'NONE') {
        body.innerHTML = '<div class="empty-state-enhanced"><span class="empty-icon">👥</span><span>No impact zone detected</span></div>';
        return;
    }
    const confColor = pop.confidence === 'High' ? 'var(--color-low)' : pop.confidence === 'Medium' ? 'var(--color-medium)' : 'var(--color-high)';

    // Multi-zone breakdown
    let zonesHtml = '';
    if (data.population_zones && data.population_zones.length > 0) {
        zonesHtml = `<div style="margin-top:0.75rem; border-top:1px solid #e5e7eb; padding-top:0.75rem;">
            <div style="font-size:0.8rem; color:#64748b; font-weight:600; margin-bottom:0.5rem;">IMPACT ZONE BREAKDOWN</div>
            ${data.population_zones.map(z => `
                <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.4rem;">
                    <div style="width:12px;height:12px;border-radius:50%;background:${z.color};flex-shrink:0;"></div>
                    <span style="flex:1;font-size:0.85rem;color:#374151;">${z.name} (${z.radius_km} km)</span>
                    <span class="mono" style="font-weight:700;font-size:0.85rem;">${z.population.toLocaleString()}</span>
                </div>
            `).join('')}
        </div>`;
    }

    body.innerHTML = `
        <div class="pop-exposure-card">
            <div class="pop-main">
                <div class="pop-number">${pop.estimated_population.toLocaleString()}</div>
                <div class="pop-label">Estimated Population Affected</div>
            </div>
            <div class="info-row"><span class="info-row-label">Impact Area</span><span class="info-row-value mono">${pop.area_km2} km²</span></div>
            <div class="info-row"><span class="info-row-label">Density</span><span class="info-row-value mono">${pop.density_per_km2} /km²</span></div>
            <div class="info-row"><span class="info-row-label">Data Source</span><span class="info-row-value">${pop.data_source}</span></div>
            <div class="info-row"><span class="info-row-label">Confidence</span><span class="info-row-value" style="color:${confColor};font-weight:700;">${pop.confidence}</span></div>
            ${zonesHtml}
            <div class="pop-disclaimer">${pop.disclaimer}</div>
        </div>`;
}

// --- Teams Panel ---
function renderTeams(data) {
    const body = document.getElementById('panelTeamsBody');
    if (!data.teams || data.teams.length === 0) {
        body.innerHTML = '<div class="empty-state-enhanced"><span class="empty-icon">👥</span><span>No team recommendations</span></div>';
        return;
    }
    body.innerHTML = data.teams.map(t => `
        <div class="team-card priority-${t.priority.toLowerCase()}">
            <div class="team-name">${t.name}</div>
            <span class="team-priority-tag ${t.priority.toLowerCase()}">${t.priority}</span>
            <div class="team-reason">${t.reason}</div>
        </div>`).join('');
}

// --- Concerns Panel ---
function renderConcerns(data) {
    const body = document.getElementById('panelConcernsBody');
    if (!data.concerns || data.concerns.length === 0) {
        body.innerHTML = '<div class="empty-state-enhanced"><span class="empty-icon">✅</span><span>No key concerns identified</span></div>';
        return;
    }
    body.innerHTML = data.concerns.map(c => {
        const icon = c.includes('TSUNAMI') ? '🌊' : c.includes('collapse') ? '🏚️' : c.includes('road') ? '🚧' : c.includes('aftershock') ? '📡' : c.includes('flood') ? '🌊' : c.includes('wind') ? '💨' : c.includes('power') || c.includes('utilities') ? '⚡' : '⚠️';
        return `<div class="concern-item"><span class="concern-icon">${icon}</span><span>${c}</span></div>`;
    }).join('');
}

// --- Resources Panel ---
function renderResources(data) {
    const body = document.getElementById('panelResourcesBody');
    const res = data.resources;
    if (!res || res.message) {
        body.innerHTML = `<div class="empty-state-enhanced"><span class="empty-icon">🏥</span><span>${res?.message || 'No emergency facilities found'}</span></div>`;
        return;
    }
    const rd = res.data;
    let html = '';
    if (rd.hospitals?.length) html += renderResourceGroup('🏥 Hospitals', rd.hospitals, '🏥');
    if (rd.fire_stations?.length) html += renderResourceGroup('🚒 Fire Stations', rd.fire_stations, '🚒');
    if (rd.police?.length) html += renderResourceGroup('🚔 Police Stations', rd.police, '🚔');
    body.innerHTML = html || '<div class="empty-state-enhanced"><span class="empty-icon">🏥</span><span>No emergency facilities found</span></div>';
}

function renderResourceGroup(title, items, icon) {
    return `<div class="resource-group"><div class="resource-group-title">${title}</div>${items.slice(0, 6).map(h => `
        <div class="resource-item"><span class="resource-icon">${icon}</span><span class="resource-name">${h.name}</span></div>`).join('')}${items.length > 6 ? `<div class="resource-count">+${items.length - 6} more</div>` : ''}</div>`;
}

// --- Allocated Resources Panel ---
function renderAllocatedResources(data) {
    const body = document.getElementById('panelAllocationBody');
    const alloc = data.allocated_resources;
    if (!alloc || !alloc.items?.length) {
        body.innerHTML = '<div class="empty-state-enhanced"><span class="empty-icon">📦</span><span>No resource allocation for current severity</span></div>';
        return;
    }
    body.innerHTML = `<div class="alloc-grid">${alloc.items.map(i => `
        <div class="alloc-item">
            <span class="alloc-icon">${i.icon}</span>
            <div class="alloc-detail"><div class="alloc-name">${i.name}</div><div class="alloc-qty">${i.quantity} ${i.unit}</div></div>
        </div>`).join('')}</div><div class="alloc-disclaimer">🎓 ${alloc.disclaimer}</div>`;
}

// --- Nearby Cities Panel ---
function renderNearbyCities(data) {
    const body = document.getElementById('panelCitiesBody');
    if (!body) return;
    const cities = data.nearby_cities;
    if (!cities || cities.length === 0) {
        body.innerHTML = '<div class="empty-state-enhanced"><span class="empty-icon">🏙️</span><span>No nearby city data available</span></div>';
        return;
    }
    const dirEmoji = (d) => {
        const map = { N: '⬆️', S: '⬇️', E: '➡️', W: '⬅️', NE: '↗️', NW: '↖️', SE: '↘️', SW: '↙️', NNE: '↗️', NNW: '↖️', SSE: '↘️', SSW: '↙️', ENE: '↗️', ESE: '↘️', WNW: '↖️', WSW: '↙️' };
        return map[d] || '📍';
    };
    body.innerHTML = cities.map(c => `
        <div style="display:flex;align-items:center;gap:0.6rem;padding:0.5rem 0;border-bottom:1px solid #f1f5f9;">
            <span style="font-size:1.1rem;">${dirEmoji(c.direction)}</span>
            <div style="flex:1;">
                <div style="font-weight:600;font-size:0.9rem;color:#1e293b;">${c.name || 'Unknown'}</div>
                ${c.population ? `<div style="font-size:0.75rem;color:#94a3b8;">Pop: ${c.population.toLocaleString()}</div>` : ''}
            </div>
            <div style="text-align:right;">
                <div class="mono" style="font-weight:700;font-size:0.85rem;color:#334155;">${c.distance} km</div>
                <div style="font-size:0.75rem;color:#94a3b8;">${c.direction}</div>
            </div>
        </div>
    `).join('');
}

// --- Weather Panel ---
function renderWeather(data) {
    const body = document.getElementById('panelWeatherBody');
    if (!body) return;
    const w = data.weather;
    if (!w || !w.available) {
        body.innerHTML = '<div class="empty-state-enhanced"><span class="empty-icon">🌡️</span><span>Weather data unavailable</span></div>';
        return;
    }
    const weatherIcon = w.is_day ?
        (w.weather_code <= 1 ? '☀️' : w.weather_code <= 3 ? '⛅' : w.weather_code <= 48 ? '🌫️' : w.weather_code <= 65 ? '🌧️' : w.weather_code <= 77 ? '❄️' : w.weather_code <= 82 ? '🌧️' : '⛈️') :
        (w.weather_code <= 1 ? '🌙' : w.weather_code <= 3 ? '☁️' : '🌧️');
    const tempF = w.temperature_c !== null ? Math.round(w.temperature_c * 9 / 5 + 32) : null;

    body.innerHTML = `
        <div style="text-align:center;margin-bottom:1rem;">
            <div style="font-size:2.5rem;">${weatherIcon}</div>
            <div style="font-size:1.3rem;font-weight:800;color:#1e293b;">${w.temperature_c !== null ? w.temperature_c + '°C' : '—'}</div>
            ${tempF !== null ? `<div style="font-size:0.85rem;color:#64748b;">${tempF}°F</div>` : ''}
            <div style="font-size:0.9rem;color:#475569;font-weight:600;">${w.weather_desc || 'Unknown'}</div>
        </div>
        <div class="info-row"><span class="info-row-label">💨 Wind</span><span class="info-row-value mono">${w.windspeed_kmh || '—'} km/h (${w.wind_direction || '—'}°)</span></div>
        <div class="info-row"><span class="info-row-label">💧 Humidity</span><span class="info-row-value mono">${w.humidity_pct !== null ? w.humidity_pct + '%' : '—'}</span></div>
        <div class="info-row"><span class="info-row-label">👁️ Visibility</span><span class="info-row-value mono">${w.visibility_m !== null ? (w.visibility_m / 1000).toFixed(1) + ' km' : '—'}</span></div>
        <div style="margin-top:0.5rem;font-size:0.7rem;color:#94a3b8;text-align:right;">Source: ${w.source || 'Open-Meteo'}</div>
    `;
}

// --- Recent Events Panel ---
function renderRecentEvents(data) {
    const body = document.getElementById('panelRecentEventsBody');
    if (!body) return;
    const events = data.recent_events;
    if (!events || events.length === 0) {
        body.innerHTML = '<div class="empty-state-enhanced"><span class="empty-icon">📈</span><span>No seismic events detected</span></div>';
        return;
    }
    const timeAgo = (iso) => {
        if (!iso) return '';
        const sec = (Date.now() - new Date(iso).getTime()) / 1000;
        if (sec < 60) return 'Just now';
        if (sec < 3600) return Math.floor(sec / 60) + 'm ago';
        if (sec < 86400) return Math.floor(sec / 3600) + 'h ago';
        return Math.floor(sec / 86400) + 'd ago';
    };
    body.innerHTML = `
        <table style="width:100%;border-collapse:collapse;font-size:0.85rem;">
            <thead>
                <tr style="background:#f8fafc;color:#64748b;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.5px;">
                    <th style="padding:0.5rem;text-align:left;">Mag</th>
                    <th style="padding:0.5rem;text-align:left;">Location</th>
                    <th style="padding:0.5rem;text-align:right;">Depth</th>
                    <th style="padding:0.5rem;text-align:right;">Time</th>
                    <th style="padding:0.5rem;text-align:right;">Felt</th>
                </tr>
            </thead>
            <tbody>
                ${events.map((ev, i) => `
                    <tr style="border-bottom:1px solid #f1f5f9;${i === 0 ? 'background:#fffbeb;font-weight:600;' : ''}">
                        <td style="padding:0.4rem 0.5rem;">
                            <span style="display:inline-block;padding:2px 8px;border-radius:4px;background:${getMagColor(ev.magnitude)};color:#fff;font-weight:700;font-size:0.8rem;min-width:40px;text-align:center;">
                                M${(ev.magnitude || 0).toFixed(1)}
                            </span>
                            ${ev.is_anomaly ? `<span title="${ev.anomaly_note || 'Unusual event'}" style="margin-left:4px;font-size:0.75rem;background:#fef3c7;color:#92400e;border:1px solid #fbbf24;border-radius:4px;padding:1px 5px;font-weight:700;">⚠ UNUSUAL</span>` : ''}
                        </td>
                        <td style="padding:0.4rem 0.5rem;color:#334155;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${ev.place || ''}">${ev.place || 'Unknown'}</td>
                        <td style="padding:0.4rem 0.5rem;text-align:right;color:#64748b;" class="mono">${ev.depth_km ? ev.depth_km.toFixed(1) + ' km' : '—'}</td>
                        <td style="padding:0.4rem 0.5rem;text-align:right;color:#64748b;" title="${ev.time ? new Date(ev.time).toLocaleString() : ''}">${timeAgo(ev.time)}</td>
                        <td style="padding:0.4rem 0.5rem;text-align:right;color:#64748b;" class="mono">${ev.felt || '—'}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
        <div style="font-size:0.75rem;color:#94a3b8;text-align:right;margin-top:0.5rem;">Showing ${events.length} events • Source: USGS</div>
    `;
}

// --- AI Analysis Panel (Grok LLM Situation Report) ---
function renderAiAnalysis(data) {
    // Find or create the AI panel container
    let container = document.getElementById('aiAnalysisPanel');
    if (!container) {
        // Insert after news section
        const newsSection = document.querySelector('.news-section') || document.querySelector('#newsBody')?.closest('.panel-section');
        if (!newsSection) return;
        container = document.createElement('div');
        container.id = 'aiAnalysisPanel';
        container.className = 'panel-section ai-analysis-section';
        newsSection.insertAdjacentElement('afterend', container);
    }

    const ai = data.ai_analysis;
    if (!ai || !ai.available) {
        container.innerHTML = `
            <div class="panel-header" style="display:flex;align-items:center;gap:0.5rem;">
                <span style="font-size:1.1rem;">🤖</span>
                <span>AI Situation Report</span>
            </div>
            <div style="padding:1rem;color:#94a3b8;font-size:0.85rem;font-style:italic;text-align:center;">
                ${ai?.summary || 'AI analysis not available'}
            </div>`;
        return;
    }

    container.innerHTML = `
        <div class="panel-header" style="display:flex;align-items:center;gap:0.5rem;">
            <span style="font-size:1.1rem;">🤖</span>
            <span>AI Situation Report</span>
            <span style="margin-left:auto;font-size:0.7rem;background:#0f172a;color:#38bdf8;padding:2px 8px;border-radius:4px;font-weight:600;">Grok ${ai.model || ''}</span>
        </div>
        <div style="padding:1rem;">
            <div style="font-size:0.9rem;color:#334155;line-height:1.7;white-space:pre-wrap;">${esc(ai.summary)}</div>
            <div style="font-size:0.7rem;color:#94a3b8;margin-top:0.75rem;text-align:right;">
                ⚠️ AI-generated assessment — for decision support only, not authoritative guidance
            </div>
        </div>`;
}

// --- News Panel ---
function renderNews(data) {
    const body = document.getElementById('newsBody');
    const news = data.news;
    if (!news || news.message || !news.articles?.length) {
        body.innerHTML = `<div class="empty-state-enhanced"><span class="empty-icon">📰</span><span>${news?.message || 'No recent news coverage found'}</span></div>`;
        return;
    }
    body.innerHTML = news.articles.map(a => `
        <a href="${esc(a.url)}" target="_blank" rel="noopener" class="news-card">
            ${a.image ? `<img class="news-card-img" src="${esc(a.image)}" alt="" onerror="this.style.display='none'" loading="lazy">` : ''}
            <div class="news-card-body">
                <div class="news-card-title">${esc(a.title)}</div>
                <div class="news-card-meta"><span class="news-source">${esc(a.source)}</span>${a.date ? `<span>• ${fmtNewsDate(a.date)}</span>` : ''}</div>
            </div>
        </a>`).join('');
}

// --- Freshness Badges ---
function updateFreshnessBadges(data) {
    const s = data.data_sources || {};
    updateBadge('freshInfo', s.disaster);
    updateBadge('freshResources', s.resources);
    updateBadge('freshNews', s.news);
}

function updateBadge(id, source) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!source || source.status === 'error') { el.textContent = '⚪ N/A'; el.className = 'freshness-badge freshness-na'; return; }
    const age = (Date.now() - new Date(source.timestamp).getTime()) / 60000;
    if (age < 5) { el.textContent = '🟢 LIVE'; el.className = 'freshness-badge freshness-live'; }
    else if (age < 30) { el.textContent = '🟡 RECENT'; el.className = 'freshness-badge freshness-recent'; }
    else { el.textContent = '🔴 STALE'; el.className = 'freshness-badge freshness-stale'; }
    el.title = `${source.source} data as of ${new Date(source.timestamp).toLocaleTimeString()} UTC`;
}

// ============================================================================
// PDF Report Generation
// ============================================================================
function downloadPdfReport() {
    const data = state.lastAnalysis;
    if (!data) { showNotification('Run analysis first', 'warning'); return; }

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

    const pageW = doc.internal.pageSize.getWidth();
    const margin = 15;
    const contentW = pageW - margin * 2;
    let y = margin;

    // --- Helper functions ---
    function addPageCheck(needed) {
        if (y + needed > doc.internal.pageSize.getHeight() - margin) {
            doc.addPage();
            y = margin;
        }
    }

    function addTitle(text, fontSize = 18) {
        addPageCheck(15);
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(fontSize);
        doc.setTextColor(30, 58, 138);
        doc.text(text, margin, y);
        y += fontSize * 0.5 + 2;
    }

    function addSubtitle(text) {
        addPageCheck(10);
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(12);
        doc.setTextColor(55, 65, 81);
        doc.text(text, margin, y);
        y += 7;
    }

    function addText(text, size = 10, color = [55, 65, 81]) {
        addPageCheck(8);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(size);
        doc.setTextColor(...color);
        const lines = doc.splitTextToSize(text, contentW);
        doc.text(lines, margin, y);
        y += lines.length * (size * 0.4) + 3;
    }

    function addKeyValue(key, value) {
        addPageCheck(7);
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(10);
        doc.setTextColor(107, 114, 128);
        doc.text(key + ':', margin, y);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(17, 24, 39);
        doc.text(String(value || '—'), margin + 45, y);
        y += 6;
    }

    function addLine() {
        doc.setDrawColor(209, 213, 219);
        doc.line(margin, y, pageW - margin, y);
        y += 4;
    }

    function addSpacer(h = 5) { y += h; }

    // ========== PAGE 1: HEADER ==========
    // Header bar
    doc.setFillColor(30, 58, 138);
    doc.rect(0, 0, pageW, 30, 'F');
    doc.setTextColor(255);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(20);
    doc.text('PDRDSS Analysis Report', margin, 18);
    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    doc.text('Post-Disaster Rescue Decision Support System', margin, 25);
    doc.text(new Date().toLocaleString() + ' UTC', pageW - margin, 25, { align: 'right' });
    y = 38;

    // Disclaimer
    doc.setFillColor(254, 243, 199);
    doc.roundedRect(margin, y, contentW, 12, 2, 2, 'F');
    doc.setTextColor(146, 64, 14);
    doc.setFontSize(8);
    doc.setFont('helvetica', 'bold');
    doc.text('ACADEMIC PROTOTYPE — This report is for research purposes only. Do not use as sole basis for life-safety decisions.', margin + 3, y + 7);
    y += 18;

    // ========== SECTION: OVERVIEW ==========
    addTitle('Disaster Overview');
    addKeyValue('Disaster Type', data.disaster_type?.toUpperCase());
    addKeyValue('Location', data.location || data.geo?.display_name || '—');
    addKeyValue('Coordinates', `${data.coordinates?.lat?.toFixed(4) || '—'}, ${data.coordinates?.lon?.toFixed(4) || '—'}`);
    addKeyValue('Severity', data.severity);
    addKeyValue('Priority', data.priority);
    addKeyValue('Timestamp', data.timestamp ? new Date(data.timestamp).toLocaleString() + ' UTC' : '—');
    addKeyValue('Analysis Time', `${data.elapsed_seconds}s`);
    addLine();

    // ========== SECTION: DISASTER INFO ==========
    if (data.disaster_info && !data.disaster_info.message) {
        addTitle('Disaster Information', 14);
        const info = data.disaster_info;
        addKeyValue('Event', info.what);
        addKeyValue('Where', info.where);
        if (info.when) addKeyValue('When', new Date(info.when).toLocaleString());
        if (info.magnitude) addKeyValue('Magnitude', 'M' + info.magnitude);
        if (info.depth_km) addKeyValue('Depth', info.depth_km.toFixed(1) + ' km');
        if (info.total_events) addKeyValue('Events in Area', info.total_events);
        if (info.mmi) addKeyValue('Max MMI', info.mmi.toFixed(1));
        if (info.alert_level) addKeyValue('Alert Level', info.alert_level.toUpperCase());
        if (info.intensity_kt) addKeyValue('Intensity', info.intensity_kt + ' kt');
        if (info.classification) addKeyValue('Classification', info.classification);
        addLine();
    }

    // ========== SECTION: POPULATION EXPOSURE ==========
    if (data.population_exposure) {
        addTitle('Population Exposure Estimate', 14);
        const pop = data.population_exposure;
        addKeyValue('Estimated Population', pop.estimated_population.toLocaleString());
        addKeyValue('Impact Area', pop.area_km2 + ' km²');
        addKeyValue('Density', pop.density_per_km2 + ' /km²');
        addKeyValue('Data Source', pop.data_source);
        addKeyValue('Confidence', pop.confidence);
        addText(pop.disclaimer, 8, [107, 114, 128]);
        addLine();
    }

    // ========== SECTION: KEY CONCERNS ==========
    if (data.concerns && data.concerns.length > 0) {
        addTitle('Key Concerns', 14);
        data.concerns.forEach((c, i) => {
            addText(`${i + 1}. ${c}`, 10);
        });
        addLine();
    }

    // ========== SECTION: RECOMMENDED TEAMS ==========
    if (data.teams && data.teams.length > 0) {
        addTitle('Recommended Response Teams', 14);
        const teamRows = data.teams.map(t => [t.name, t.priority, t.reason]);
        doc.autoTable({
            startY: y,
            margin: { left: margin, right: margin },
            head: [['Team', 'Priority', 'Reason']],
            body: teamRows,
            styles: { fontSize: 9, cellPadding: 3 },
            headStyles: { fillColor: [30, 58, 138], textColor: 255 },
            alternateRowStyles: { fillColor: [245, 247, 250] },
            columnStyles: { 0: { fontStyle: 'bold', cellWidth: 50 }, 1: { cellWidth: 25 } },
        });
        y = doc.lastAutoTable.finalY + 8;
    }

    // ========== SECTION: RESOURCE ALLOCATION ==========
    if (data.allocated_resources && data.allocated_resources.items?.length) {
        addTitle('Simulated Resource Allocation', 14);
        const allocRows = data.allocated_resources.items.map(i => [i.name, i.quantity + ' ' + i.unit]);
        doc.autoTable({
            startY: y,
            margin: { left: margin, right: margin },
            head: [['Resource', 'Quantity']],
            body: allocRows,
            styles: { fontSize: 9, cellPadding: 3 },
            headStyles: { fillColor: [30, 58, 138], textColor: 255 },
            alternateRowStyles: { fillColor: [245, 247, 250] },
        });
        y = doc.lastAutoTable.finalY + 4;
        addText(data.allocated_resources.disclaimer, 8, [107, 114, 128]);
        addLine();
    }

    // ========== SECTION: NEARBY RESOURCES ==========
    if (data.resources && data.resources.data) {
        addTitle('Nearby Emergency Facilities', 14);
        const rd = data.resources.data;
        const facilityRows = [];
        rd.hospitals?.forEach(h => facilityRows.push([h.name, 'Hospital', h.phone || '—']));
        rd.fire_stations?.forEach(f => facilityRows.push([f.name, 'Fire Station', f.phone || '—']));
        rd.police?.forEach(p => facilityRows.push([p.name, 'Police', p.phone || '—']));

        if (facilityRows.length > 0) {
            doc.autoTable({
                startY: y,
                margin: { left: margin, right: margin },
                head: [['Facility', 'Type', 'Phone']],
                body: facilityRows.slice(0, 20),
                styles: { fontSize: 8, cellPadding: 2.5 },
                headStyles: { fillColor: [30, 58, 138], textColor: 255 },
                alternateRowStyles: { fillColor: [245, 247, 250] },
            });
            y = doc.lastAutoTable.finalY + 4;
            if (facilityRows.length > 20) addText(`... and ${facilityRows.length - 20} more facilities`, 8, [107, 114, 128]);
        }
        addLine();
    }

    // ========== SECTION: NEWS ==========
    if (data.news && data.news.articles?.length) {
        addTitle('Related News Coverage', 14);
        data.news.articles.slice(0, 10).forEach((a, i) => {
            addText(`${i + 1}. ${a.title}`, 9, [17, 24, 39]);
            addText(`   Source: ${a.source} | ${a.url}`, 7, [107, 114, 128]);
        });
        addLine();
    }

    // ========== SECTION: DATA SOURCES ==========
    addTitle('Data Sources', 14);
    if (data.data_sources) {
        Object.entries(data.data_sources).forEach(([key, val]) => {
            addKeyValue(key.charAt(0).toUpperCase() + key.slice(1), `${val.source} — Status: ${val.status}`);
        });
    }
    addSpacer(5);

    // Footer
    addPageCheck(15);
    doc.setDrawColor(209, 213, 219);
    doc.line(margin, y, pageW - margin, y);
    y += 5;
    doc.setFont('helvetica', 'italic');
    doc.setFontSize(7);
    doc.setTextColor(156, 163, 175);
    doc.text('Generated by PDRDSS — Post-Disaster Rescue Decision Support System (Academic Prototype)', margin, y);
    y += 4;
    doc.text('Population data: WorldPop. No mobile tracking used. Resource allocation is simulated for academic demonstration.', margin, y);

    // Save
    const filename = `PDRDSS_Report_${data.disaster_type}_${(data.location || 'unknown').replace(/[^a-zA-Z0-9]/g, '_').substring(0, 30)}_${new Date().toISOString().slice(0, 10)}.pdf`;
    doc.save(filename);
    showNotification('PDF report downloaded!', 'success');
}

// ============================================================================
// UI Helpers
// ============================================================================
function setLoading(loading) {
    document.getElementById('loadingIndicator').classList.toggle('hidden', !loading);
    document.getElementById('analyzeBtn').disabled = loading;
}

function showSkeletons() {
    const sk = '<div class="skeleton skeleton-lg"></div><div class="skeleton skeleton-md"></div><div class="skeleton skeleton-sm"></div><div class="skeleton skeleton-md"></div>';
    ['panelInfoBody', 'panelPopulationBody', 'panelTeamsBody', 'panelConcernsBody', 'panelResourcesBody', 'panelAllocationBody'].forEach(id => document.getElementById(id).innerHTML = sk);
    document.getElementById('newsBody').innerHTML = '<div class="empty-state"><div class="spinner" style="margin:0 auto;"></div></div>';
}

function showErrorState(message) {
    document.getElementById('panelInfoBody').innerHTML = `<div class="error-state"><div class="error-icon">⚠️</div><div class="error-msg">${esc(message)}</div><button class="btn-retry" onclick="runAnalysis()">↻ Retry</button></div>`;
    ['panelPopulationBody', 'panelTeamsBody', 'panelConcernsBody', 'panelResourcesBody', 'panelAllocationBody'].forEach(id => {
        document.getElementById(id).innerHTML = '<div class="empty-state">Awaiting data</div>';
    });
}

function showNotification(msg, type = 'info') {
    const existing = document.querySelector('.inline-notif');
    if (existing) existing.remove();
    const n = document.createElement('div');
    n.className = 'inline-notif';
    const colors = { warning: ['var(--color-high-glow)', 'var(--color-high)'], success: ['var(--color-low-glow)', 'var(--color-low)'], info: ['var(--accent-blue-glow)', 'var(--accent-blue)'] };
    const [bg, fg] = colors[type] || colors.info;
    n.style.cssText = `position:fixed;top:70px;right:20px;z-index:9999;background:${bg};color:${fg};border:1px solid ${fg};padding:0.75rem 1.5rem;border-radius:var(--radius-md);font-size:1rem;font-weight:600;font-family:var(--font-sans);animation:slideUp 0.3s ease;`;
    n.textContent = msg;
    document.body.appendChild(n);
    setTimeout(() => n.remove(), 3000);
}

function getMagColor(mag) {
    if (mag >= 7) return 'var(--color-critical)';
    if (mag >= 5.5) return 'var(--color-high)';
    if (mag >= 4) return 'var(--color-medium)';
    return 'var(--color-low)';
}

function severityBadge(s) {
    const c = { CATASTROPHIC: 'var(--color-critical)', SEVERE: 'var(--color-critical)', MODERATE: 'var(--color-high)', MINOR: 'var(--color-medium)', NONE: 'var(--color-low)' };
    return `<span style="color:${c[s] || 'var(--text-muted)'};font-weight:800;">${s}</span>`;
}

function alertBadge(level) {
    const c = { red: 'var(--color-critical)', orange: 'var(--color-high)', yellow: 'var(--color-medium)', green: 'var(--color-low)' };
    return `<span style="color:${c[level] || 'var(--text-muted)'};font-weight:800;text-transform:uppercase;">${level}</span>`;
}

function truncate(str, len) { return str?.length > len ? str.substring(0, len) + '…' : (str || ''); }

function esc(str) {
    if (!str) return '';
    const d = document.createElement('div'); d.textContent = str; return d.innerHTML;
}

function fmtNewsDate(dateStr) {
    if (!dateStr) return '';
    try {
        if (dateStr.length >= 8 && !dateStr.includes('-')) return `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`;
        return new Date(dateStr).toLocaleDateString();
    } catch { return dateStr; }
}
