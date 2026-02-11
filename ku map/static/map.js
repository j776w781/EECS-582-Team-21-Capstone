/**
 * KU Parking Map - Sprint 1
 * Handles map initialization, lot markers, availability logic, and interactions
 */

// Global state
let map;
let lots = [];
let markers = [];
let lotToMarkerMap = {}; // Map lot ID to marker for quick lookup
let selectedLot = null;
let selectedMarker = null;

// KU campus center coordinates
const KU_CENTER = [38.9581, -95.2464];
const MAP_ZOOM = 15;

// Coordinate picker flag (set to false to disable)S
const ENABLE_COORDINATE_PICKER = true;

/**
 * Initialize the map
 */
function initMap() {
    // Create map centered on KU campus
    map = L.map('map').setView(KU_CENTER, MAP_ZOOM);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
    
    // Enable coordinate picker if flag is set
    if (ENABLE_COORDINATE_PICKER) {
        enableCoordinatePicker();
    }
}

/**
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
    return available ? '#28a745' : '#6c757d'; // Green or Gray
}

/**
 * Create a marker for a parking lot
 * @param {Object} lot - The parking lot object
 * @param {boolean} available - Whether the lot is currently available
 * @returns {L.CircleMarker} - Leaflet marker
 */
function createLotMarker(lot, available) {
    const color = getLotColor(available);
    
    const marker = L.circleMarker(lot.position, {
        radius: 7,
        fillColor: color,
        color: '#333',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
    }).addTo(map);
    
    // Store reference to lot in marker
    marker.lotId = lot.id;
    
    // Add popup with lot name
    marker.bindPopup(`<strong>${lot.name}</strong><br>Type: ${lot.type}`);
    
    // Click handler for map marker
    marker.on('click', function() {
        showLotDetails(lot);
        // Also open popup
        marker.openPopup();
    });
    
    // Store mapping from lot ID to marker
    lotToMarkerMap[lot.id] = marker;
    
    return marker;
}

/**
 * Update all markers based on current permit/day/time settings
 */
function updateMarkers() {
    const permit = document.getElementById('permit-select').value;
    const day = document.getElementById('day-select').value;
    const time = document.getElementById('time-input').value;
    
    // Update each marker's color based on availability
    markers.forEach((marker, index) => {
        const lot = lots[index];
        const available = isLotAvailable(lot, permit, day, time);
        const color = getLotColor(available);
        
        // If this marker is currently selected, keep it highlighted but update color
        if (selectedMarker && selectedMarker.lotId === lot.id) {
            marker.setStyle({
                radius: 10,
                color: '#0051ba',
                weight: 3,
                fillColor: color,
                fillOpacity: 0.9
            });
        } else {
            // Normal marker style
            marker.setStyle({
                radius: 7,
                fillColor: color,
                color: '#333',
                weight: 2,
                fillOpacity: 0.8
            });
        }
    });
}

/**
 * Highlight a marker on the map (make it visually distinct)
 * @param {L.CircleMarker} marker - The marker to highlight
 */
function highlightMarker(marker) {
    if (!marker) return;
    
    // Make marker larger and change border color to blue
    marker.setStyle({
        radius: 10,
        color: '#0051ba',
        weight: 3,
        fillOpacity: 0.9
    });
    
    // Open popup
    marker.openPopup();
}

/**
 * Unhighlight a marker (restore normal appearance)
 * @param {L.CircleMarker} marker - The marker to unhighlight
 */
function unhighlightMarker(marker) {
    if (!marker) return;
    
    // Restore normal size and get current availability color
    const permit = document.getElementById('permit-select').value;
    const day = document.getElementById('day-select').value;
    const time = document.getElementById('time-input').value;
    
    const lot = lots.find(l => l.id === marker.lotId);
    if (lot) {
        const available = isLotAvailable(lot, permit, day, time);
        const color = getLotColor(available);
        
        marker.setStyle({
            radius: 7,
            color: '#333',
            weight: 2,
            fillColor: color,
            fillOpacity: 0.8
        });
    }
}

/**
 * Show lot details in the details panel
 * @param {Object} lot - The parking lot object
 */
function showLotDetails(lot) {
    // Unhighlight previous marker if any
    if (selectedMarker) {
        unhighlightMarker(selectedMarker);
    }
    
    selectedLot = lot;
    
    // Find and highlight the corresponding marker
    const marker = lotToMarkerMap[lot.id];
    if (marker) {
        selectedMarker = marker;
        highlightMarker(marker);
        
        // Pan map to marker if needed (with smooth animation)
        map.setView(lot.position, map.getZoom(), { animate: true, duration: 0.5 });
    }
    
    // Update details panel content
    document.getElementById('details-name').textContent = lot.name;
    document.getElementById('details-type').textContent = lot.type;
    document.getElementById('details-restrictions').textContent = lot.restrictions;
    
    // Show details panel
    const detailsPanel = document.getElementById('details-panel');
    detailsPanel.classList.remove('hidden');
    
    // Highlight selected lot in list
    document.querySelectorAll('.lot-item').forEach(item => {
        item.classList.remove('selected');
        if (item.dataset.lotId === lot.id) {
            item.classList.add('selected');
        }
    });
}

/**
 * Hide the details panel
 */
function hideDetails() {
    const detailsPanel = document.getElementById('details-panel');
    detailsPanel.classList.add('hidden');
    
    // Unhighlight marker
    if (selectedMarker) {
        unhighlightMarker(selectedMarker);
        selectedMarker.closePopup();
        selectedMarker = null;
    }
    
    selectedLot = null;
    
    // Remove selection highlight from list
    document.querySelectorAll('.lot-item').forEach(item => {
        item.classList.remove('selected');
    });
}

/**
 * Render the lot list
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
        
        // Click handler for list item
        listItem.addEventListener('click', () => {
            showLotDetails(lot);
        });
        
        lotList.appendChild(listItem);
    });
}

/**
 * Load parking lots from API and initialize map
 */
async function loadLots() {
    try {
        const response = await fetch('/api/lots');
        lots = await response.json();
        
        // Render lot list
        renderLotList();
        
        // Create markers for all lots
        const permit = document.getElementById('permit-select').value;
        const day = document.getElementById('day-select').value;
        const time = document.getElementById('time-input').value;
        
        lots.forEach(lot => {
            const available = isLotAvailable(lot, permit, day, time);
            const marker = createLotMarker(lot, available);
            markers.push(marker);
        });
        
    } catch (error) {
        console.error('Error loading lots:', error);
        alert('Failed to load parking lots. Please refresh the page.');
    }
}

/**
 * Initialize the application
 */
function init() {
    // Initialize map
    initMap();
    
    // Load lots data
    loadLots();
    
    // Set up control event listeners
    document.getElementById('permit-select').addEventListener('change', updateMarkers);
    document.getElementById('day-select').addEventListener('change', updateMarkers);
    document.getElementById('time-input').addEventListener('change', updateMarkers);
    
    // Close details panel button
    document.getElementById('close-details').addEventListener('click', hideDetails);
    
    // Close details panel when clicking outside (optional enhancement)
    document.getElementById('details-panel').addEventListener('click', (e) => {
        if (e.target.id === 'details-panel') {
            hideDetails();
        }
    });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
