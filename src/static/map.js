/**
 * KU Parking Map - Sprint 1
 * Handles map initialization, lot markers, availability logic, and interactions
 * Authors: Li K, Kitchin Mark, Welicky Joshua
 * Created February 8th, 2026
 * Revised February 15th, 2026
 * Revised March 1, 2026: Tweaks to initial JavaScript to account for updated Python Backend.
 * No known errors or crashes
 * Most of the logic done in this file will be moved to a python based backend in the next sprint
 * RELIES ON Leaflet.js library.
 * Revised 3/28/2026: Disclaimer functionality added.
 * Revised 3/29/2026: Mobile map-first UI — search opens lot list, hides map until pick.
 */
// Global state
let map;
let lots = [];
let markers = [];
let lotToMarkerMap = {};
let selectedLot = null;
let selectedMarker = null;

let lotSearchBlurTimer = null;
let filteredLots = [];
const KU_CENTER = [38.9581, -95.2464];
const MAP_ZOOM = 15;
const ENABLE_COORDINATE_PICKER = false;

/**
 * Initialize map
 */
function isMobileLayout() {
    return window.matchMedia('(max-width: 768px)').matches;
}

function openMobileLotPicker() {
    if (!isMobileLayout()) return;
    const container = document.querySelector('.container');
    if (container) container.classList.add('mobile-lot-picker-open');
    applyLotSearchFilter();
}

function closeMobileLotPicker() {
    const container = document.querySelector('.container');
    if (!container || !container.classList.contains('mobile-lot-picker-open')) return;
    container.classList.remove('mobile-lot-picker-open');
    const search = document.getElementById('lot-search');
    if (search) search.blur();
    requestAnimationFrame(function () {
        if (map) map.invalidateSize();
    });
}

function applyLotSearchFilter() {
    const search = document.getElementById('lot-search');
    if (!search) return;
    const q = (search.value || '').trim().toLowerCase();
    document.querySelectorAll('#lot-list .lot-item').forEach(function (li) {
        const name = (li.dataset.lotName || '').toLowerCase();
        if (!q || name.indexOf(q) !== -1) {
            li.classList.remove('lot-item--hidden');
        } else {
            li.classList.add('lot-item--hidden');
        }
    });
}

function initMap() {
    map = L.map('map').setView(KU_CENTER, MAP_ZOOM);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);

    // Coordinate picker functionality disabled for now
    // if (ENABLE_COORDINATE_PICKER) {
    //     enableCoordinatePicker();
    // }
}

/**
 * Get color based on backend-provided availability
 * Enable coordinate picker: click map to get lat/lng coordinates
 * Only works when ENABLE_COORDINATE_PICKER is true
 */
function enableCoordinatePicker() {
    // Safety guard: exit if map is not initialized
    if (!map) {
        console.warn('Coordinate picker: map is not initialized');
        return;
    }
    
    // Create a temporary marker for displaying coordinates
    let tempMarker = null;
    
    // Attach click handler to map
    map.on('click', function(e) {
        const lat = e.latlng.lat.toFixed(6);
        const lng = e.latlng.lng.toFixed(6);
        const coords = `[${lat}, ${lng}]`;
        
        // Log coordinates to console
        console.log(coords);
        
        // Remove previous temporary marker if exists
        if (tempMarker) {
            map.removeLayer(tempMarker);
        }
        
        // Create popup at clicked location
        tempMarker = L.marker(e.latlng).addTo(map);
        tempMarker.bindPopup(`Copy this: ${coords}`).openPopup();
    });
}

/**
 * Get color for a lot based on availability
 * @param {Object} lot - The parking lot object with available and available_in_one_hour properties
 * @returns {string} - Color code (green for available, yellow for becoming unavailable, red for unavailable)
 */
function getLotColor(lot) {
    //This method is very simplified now that the backend decides the color, not JavaScript.
   return lot.color;
}

/**
 * Create lot marker
 */
function createLotMarker(lot) {
    const color = getLotColor(lot);

    const marker = L.circleMarker(lot.position, {
        radius: 7,
        fillColor: color,
        color: '#333',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
    }).addTo(map);

    marker.lotId = lot.id;

    marker.bindPopup(`<strong>${lot.name}</strong><br>Type: ${lot.type}`);

    marker.on('click', function () {
        showLotDetails(lot);
        marker.openPopup();
    });

    lotToMarkerMap[lot.id] = marker;

    return marker;
}

/**
 * Load lots from backend (now includes availability)
 */
async function loadLots() {
    try {
        const permit = document.getElementById('permit-select').value;
        const day = document.getElementById('day-select').value;
        const time = document.getElementById('time-input').value;

        console.log('Fetching lots with params:', { permit, day, time });

        const response = await fetch(
            `/api/lots?permit=${permit}&day=${day}&time=${time}`
        );

        if (!response.ok) {
            throw new Error(`API returned status ${response.status}: ${response.statusText}`);
        }

        lots = await response.json();
        filteredLots = getSortedLots(lots);
        console.log('Successfully loaded lots:', lots);

        if (!Array.isArray(lots)) {
            throw new Error('Expected lots to be an array, got: ' + typeof lots);
        }

        renderLotList();

        // Remove old markers
        markers.forEach(marker => map.removeLayer(marker));
        markers = [];
        lotToMarkerMap = {};

        lots.forEach(lot => {
            const marker = createLotMarker(lot);
            markers.push(marker);
        });

    } catch (error) {
        console.error('Error loading lots:', error);
        alert('Failed to load parking lots.');
    }
}

/**
 * Update markers by reloading from backend
 */
function updateMarkers() {
    // Close any open details when updating
    if (selectedMarker) {
        hideDetails();
    }
    loadLots();
}

/**
 * Highlight marker
 */
function highlightMarker(marker) {
    marker.setStyle({
        radius: 10,
        color: '#0051ba',
        weight: 3,
        fillOpacity: 0.9
    });
    marker.openPopup();
}

/**
 * Unhighlight marker
 */
function unhighlightMarker(marker) {
    const lot = lots.find(l => l.id === marker.lotId);
    //const color = getLotColor(lot.available);
    const color = getLotColor(lot);

    marker.setStyle({
        radius: 7,
        fillColor: color,
        color: '#333',
        weight: 2,
        fillOpacity: 0.8
    });
}

/**
 * Grey out marker (when other lots are selected)
 */
function greyOutMarker(marker) {
    marker.setStyle({
        radius: 7,
        fillColor: '#cccccc',
        color: '#999999',
        weight: 2,
        fillOpacity: 0.5
    });
}

/**
 * Restore marker to normal color based on availability
 */
function restoreMarkerColor(lot, marker) {
    const color = getLotColor(lot);
    marker.setStyle({
        radius: 7,
        fillColor: color,
        color: '#333',
        weight: 2,
        fillOpacity: 0.8
    });
}

/**
 * Show lot details
 */
function showLotDetails(lot) {
    clearTimeout(lotSearchBlurTimer);
    closeMobileLotPicker();

    if (selectedMarker) {
        unhighlightMarker(selectedMarker);
    }

    selectedLot = lot;

    const marker = lotToMarkerMap[lot.id];
    if (marker) {
        selectedMarker = marker;
        highlightMarker(marker);
        map.setView(lot.position, map.getZoom(), { animate: true, duration: 0.5 });
    }

    // Grey out all other markers
    markers.forEach(marker => {
        if (marker.lotId !== lot.id) {
            greyOutMarker(marker);
        }
    });

    document.getElementById('details-name').textContent = lot.name;
    document.getElementById('details-type').textContent = lot.type;
    document.getElementById('details-restrictions').textContent = lot.description;

    // Reset report form and status on selecting lot
    document.getElementById('report-description').value = '';
    document.getElementById('report-start').value = '';
    document.getElementById('report-end').value = '';
    document.getElementById('report-status').textContent = '';

    document.getElementById('details-panel').classList.remove('hidden');

    document.querySelectorAll('.lot-item').forEach(item => {
        item.classList.remove('selected');
        if (item.dataset.lotId === lot.id) {
            item.classList.add('selected');
        }
    });
}

/**
 * Hide details
 */
function hideDetails() {
    document.getElementById('details-panel').classList.add('hidden');

    if (selectedMarker) {
        unhighlightMarker(selectedMarker);
        selectedMarker.closePopup();
        selectedMarker = null;
    }

    // Restore all markers to normal colors
    markers.forEach(marker => {
        const lot = lots.find(l => l.id === marker.lotId);
        if (lot) {
            restoreMarkerColor(lot, marker);
        }
    });

    selectedLot = null;

    document.querySelectorAll('.lot-item').forEach(item => {
        item.classList.remove('selected');
    });

    closeReportModal();
}

/**
 * Show report modal (only when a lot is selected)
 */
function openReportModal() {
    if (!selectedLot) return;
    document.body.classList.add('report-modal-active');
    document.getElementById('report-modal-overlay').classList.remove('hidden');
    document.getElementById('report-description').value = '';
    document.getElementById('report-start').value = '';
    document.getElementById('report-end').value = '';
    document.getElementById('report-status').textContent = '';
}

/**
 * Hide report modal and clear form
 */
function closeReportModal() {
    document.body.classList.remove('report-modal-active');
    document.getElementById('report-modal-overlay').classList.add('hidden');
    document.getElementById('report-description').value = '';
    document.getElementById('report-start').value = '';
    document.getElementById('report-end').value = '';
    document.getElementById('report-status').textContent = '';
}

/**
 * Submit special restriction report
 */
async function submitReport() {
    if (!selectedLot) {
        document.getElementById('report-status').textContent = 'Select a lot first.';
        return;
    }

    const description = document.getElementById('report-description').value.trim();
    const start = document.getElementById('report-start').value;
    const end = document.getElementById('report-end').value;

    // Frontend allows empty Description, Start, and End. Backend should implement default logic when any are missing, e.g.:
    // - No time (start/end) → restriction expires after 24 hours (Req 19).
    // - Time span > 48 hours → treat as 24 hours (Req 20).
    // - Empty description → backend may use a default label or still accept the report.
    const payload = { description: description || '' };
    if (start) payload.start = start;
    if (end) payload.end = end;

    try {
        const response = await fetch(`/api/lots/${selectedLot.id}/report`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const body = await response.json();
        if (!response.ok) {
            document.getElementById('report-status').textContent = `Error: ${body.error || response.statusText}`;
            return;
        }

        document.getElementById('report-status').textContent = 'Report submitted. Refreshing lots...';
        await loadLots();

        closeReportModal();

        // Re-open details for this lot after refresh
        const refreshedLot = lots.find(l => l.id === selectedLot.id);
        if (refreshedLot) {
            showLotDetails(refreshedLot);
        }

    } catch (err) {
        console.error('Report request failed:', err);
        document.getElementById('report-status').textContent = 'Failed to submit report. Try again.';
    }
}
/**
 * Sort lot list
 */
function getSortedLots(lotsArray) {
    return [...lotsArray].sort((a, b) => 
        a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' })
    );
}
/**
 * Render lot list
 */
function renderLotList() {
    const lotList = document.getElementById('lot-list');
    lotList.innerHTML = '';

    filteredLots.forEach(lot => {
        const listItem = document.createElement('li');
        listItem.className = 'lot-item';
        listItem.dataset.lotId = lot.id;
        listItem.dataset.lotName = lot.name;

        listItem.innerHTML = `
            <div class="lot-name">${lot.name}</div>
            <div class="lot-type">${lot.type}</div>
        `;

        listItem.addEventListener('click', () => {
            clearTimeout(lotSearchBlurTimer);
            showLotDetails(lot);
        });

        lotList.appendChild(listItem);
    });
}
/**
 * Search function
 */
/*document.getElementById('lot-search').addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        const query = event.target.value.toLowerCase();

        filteredLots = getSortedLots(lots).filter(lot =>
            lot.name.toLowerCase().includes(query) ||
            lot.type.toLowerCase().includes(query)
        );

        renderLotList();
    }
});
*/

// Unified search handler
function handleSearchInput(query) {
    query = (query || '').toLowerCase();

    filteredLots = getSortedLots(lots).filter(lot =>
        lot.name.toLowerCase().includes(query) ||
        lot.type.toLowerCase().includes(query)
    );

    renderLotList();
}

/**
 * Initial`ize app
 */
function init() {
    console.log('[DEBUG] App initialization starting');
    
    initMap();
    console.log('[DEBUG] Map initialized');
    
    loadLots();
    console.log('[DEBUG] Lots loading initiated');

    document.getElementById('permit-select').addEventListener('change', updateMarkers);
    document.getElementById('day-select').addEventListener('change', updateMarkers);
    document.getElementById('time-input').addEventListener('change', updateMarkers);
    document.getElementById('close-details').addEventListener('click', hideDetails);
    document.getElementById('report-btn').addEventListener('click', openReportModal);
    document.getElementById('report-modal-close').addEventListener('click', closeReportModal);
    document.getElementById('report-cancel').addEventListener('click', closeReportModal);
    document.getElementById('submit-report').addEventListener('click', submitReport);

    document.getElementById('report-modal-overlay').addEventListener('click', function (e) {
        if (e.target === this) closeReportModal();
    });

    const lotSearch = document.getElementById('lot-search');
    const lotSearchSidebar = document.getElementById('lot-search-sidebar');
    const lotListPanel = document.querySelector('.lot-list-panel');

    // Top search
    if (lotSearch) {
        lotSearch.addEventListener('focus', function () {
            clearTimeout(lotSearchBlurTimer);
            openMobileLotPicker();
        });

        lotSearch.addEventListener('blur', function () {
            lotSearchBlurTimer = setTimeout(function () {
                const ae = document.activeElement;
                if (ae === lotSearch || (lotListPanel && lotListPanel.contains(ae))) return;
                closeMobileLotPicker();
            }, 220);
        });

        lotSearch.addEventListener('input', function (event) {
            handleSearchInput(event.target.value);
        });
    }

    // Sidebar search 
    if (lotSearchSidebar) {
        lotSearchSidebar.addEventListener('input', function (event) {
            handleSearchInput(event.target.value);
        });
    }
    
    if (lotListPanel) {
        lotListPanel.addEventListener('mousedown', function () {
            clearTimeout(lotSearchBlurTimer);
        });
    }

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            closeMobileLotPicker();
        }
    });

    window.addEventListener('resize', function () {
        if (!isMobileLayout()) {
            document.querySelector('.container').classList.remove('mobile-lot-picker-open');
            if (map) map.invalidateSize();
        } else if (map) {
            map.invalidateSize();
        }
    });

    /*
    This makes it possible to actually close the disclaimer.
    */
    window.addEventListener('load', function () {
        //Store an indicator in local storage so the user isn't shown disclaimer after every refresh.
        if (!localStorage.getItem('disclaimerShown')) {
            const modal = document.getElementById('intro-modal');
            const closeBtn = document.getElementById('intro-close');

            //Show disclaimer
            setTimeout(function () {
                modal.classList.remove('hidden');
            }, 500);

            //enable close button.
            closeBtn.addEventListener('click', function () {
                modal.classList.add('hidden');
            });
            //Add indicator to local storage.
            localStorage.setItem('disclaimerShown', 'true');
        }
    });

    console.log('[DEBUG] Event listeners attached');
}

if (document.readyState === 'loading') {
    console.log('[DEBUG] DOM still loading, waiting for DOMContentLoaded');
    document.addEventListener('DOMContentLoaded', init);
} else {
    console.log('[DEBUG] DOM ready, initializing app immediately');
    init();
}