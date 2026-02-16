/**
 * KU Parking Map - Sprint 1
 * Handles map initialization, lot markers, availability logic, and interactions
 * Authors: Li K, Kitchin Mark, Welicky Joshua
 * Created February 8th, 2026
 * Revised February 15th, 2026
 * No known errors or crashes
 * Most of the logic done in this file will be moved to a python based backend in the next sprint
 * RELIES ON Leaflet.js library.
 */
// Global state
let map;
let lots = [];
let markers = [];
let lotToMarkerMap = {};
let selectedLot = null;
let selectedMarker = null;

const KU_CENTER = [38.9581, -95.2464];
const MAP_ZOOM = 15;
const ENABLE_COORDINATE_PICKER = false;

/**
 * Initialize map
 */
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
 * Determine if a lot is available based on permit, day, and time
 * @param {Object} lot - The parking lot object
 * @param {string} permit - User's permit type (NONE, YELLOW, RED, BLUE)
 * @param {string} day - Day of week (Mon, Tue, Wed, Thu, Fri, Sat, Sun)
 * @param {string} timeHHMM - Time in HH:MM format (e.g., "09:00", "17:00")
 * @returns {boolean} - True if lot is available, false otherwise
 */

/*
NOTE: This function exists in the frontend JavaScript for prototyping purposes.
It will be moved to a Python-based backend for consistent in SPRINT 2, centralized information
and updates.
*/
function isLotAvailable(lot, permit, day, timeHHMM) {
    const lotType = lot.type.toUpperCase();
    
    // Parse time
    const [hours, minutes] = timeHHMM.split(':').map(Number);
    const timeInMinutes = hours * 60 + minutes;
    
    // Yellow lots logic
    if (lotType === 'YELLOW') {
        // If user has Yellow permit, lot is always available
        if (permit === 'YELLOW') {
            return true;
        }
        
        // If user has no permit
        if (permit === 'NONE') {
            // Mon-Fri between 08:00-16:00 (8 AM - 4 PM) -> NOT available
            // After 17:00 (5 PM) -> available
            const isWeekday = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'].includes(day);
            
            if (isWeekday) {
                // Restricted hours: 08:00 (480 min) to before 17:00 (1020 min)
                if (timeInMinutes >= 480 && timeInMinutes < 1020) {
                    return false; // NOT available
                }
            }
            
            // After 17:00 (5 PM) or weekends -> available
            return true;
        }
        
        // Other permits don't grant access to Yellow lots
        return false;
    }
    
    // Red lots require RED permit
    if (lotType === 'RED') {
        return permit === 'RED';
    }
    
    // Blue lots require BLUE permit
    if (lotType === 'BLUE') {
        return permit === 'BLUE';
    }
    
    // Default: not available
    return false;
}

/**
 * Get color for a lot based on availability
 * @param {boolean} available - Whether the lot is available
 * @returns {string} - Color code (green for available, gray for not available)
 */
function getLotColor(available) {
    return available ? '#28a745' : '#6c757d';
}

/**
 * Create lot marker
 */
function createLotMarker(lot) {
    const color = getLotColor(lot.available);

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
    const color = getLotColor(lot.available);

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
    const color = getLotColor(lot.available);
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
    document.getElementById('details-restrictions').textContent = lot.restrictions;

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
}

/**
 * Render lot list
 */
function renderLotList() {
    const lotList = document.getElementById('lot-list');
    lotList.innerHTML = '';

    lots.forEach(lot => {
        const listItem = document.createElement('li');
        listItem.className = 'lot-item';
        listItem.dataset.lotId = lot.id;

        listItem.innerHTML = `
            <div class="lot-name">${lot.name}</div>
            <div class="lot-type">${lot.type}</div>
        `;

        listItem.addEventListener('click', () => {
            showLotDetails(lot);
        });

        lotList.appendChild(listItem);
    });
}

/**
 * Initialize app
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
    
    console.log('[DEBUG] Event listeners attached');
}

if (document.readyState === 'loading') {
    console.log('[DEBUG] DOM still loading, waiting for DOMContentLoaded');
    document.addEventListener('DOMContentLoaded', init);
} else {
    console.log('[DEBUG] DOM ready, initializing app immediately');
    init();
}