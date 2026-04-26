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
 * Revised 4/12/2026: Date picker UI; weekday synced to #day-select; API uses date + time.
 */
// Global state
let map;
let lots = [];
let specRestricts = [];
let markers = [];
let lotToMarkerMap = {};
let selectedLot = null;
let selectedMarker = null;

let lotSearchBlurTimer = null;
let filteredLots = [];
const KU_CENTER = [38.9581, -95.2464];
const MAP_ZOOM = 15;
const ENABLE_COORDINATE_PICKER = false;

let basketballMode = false;
const GAME_LOTS = ["20", "31", "54", "70", "71", "72", "90", "93","117", "118", "125", "127"];
const GAME_GARAGES = ["AFPK","CDPG","MSPK"];

/** JS weekday 0=Sun … 6=Sat → Mon/Tue/… value for #day-select */
const WEEKDAY_TO_ABBR = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

// cooldown to dispute restriction
const DISPUTE_COOLDOWN_MS = 5*60*1000; // 5 minutes

function syncDaySelectFromDate() {
    const dateInput = document.getElementById('date-input');
    const daySelect = document.getElementById('day-select');
    if (!dateInput || !daySelect) return;
    if (!dateInput.value) {
        const t = new Date();
        dateInput.value = `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, '0')}-${String(t.getDate()).padStart(2, '0')}`;
    }
    const d = new Date(dateInput.value + 'T12:00:00');
    daySelect.value = WEEKDAY_TO_ABBR[d.getDay()];
}

/**
 * Initialize map
 */
function isMobileLayout() {
    return window.matchMedia('(max-width: 1023px)').matches;
}

function closeMobileTocDrawer() {
    const tocMenu = document.getElementById('tocMenuMob');
    const backdrop = document.getElementById('tocDrawerBackdrop');
    const tocBtn = document.getElementById('tocBtnMob');
    if (tocMenu) tocMenu.classList.remove('toc-menu--drawer-open');
    if (backdrop) {
        backdrop.classList.remove('toc-drawer-backdrop--visible');
        backdrop.setAttribute('aria-hidden', 'true');
    }
    if (tocBtn) {
        tocBtn.classList.remove('active');
        tocBtn.setAttribute('aria-expanded', 'false');
    }
}

function toggleMobileTocDrawer() {
    const tocMenu = document.getElementById('tocMenuMob');
    const backdrop = document.getElementById('tocDrawerBackdrop');
    const tocBtn = document.getElementById('tocBtnMob');
    if (!tocMenu || !backdrop || !tocBtn) return;
    const opening = !tocMenu.classList.contains('toc-menu--drawer-open');
    if (opening) {
        closeMobileLotPicker();
        tocMenu.classList.add('toc-menu--drawer-open');
        backdrop.classList.add('toc-drawer-backdrop--visible');
        backdrop.setAttribute('aria-hidden', 'false');
    } else {
        closeMobileTocDrawer();
    }
    tocBtn.classList.toggle('active', opening);
    tocBtn.setAttribute('aria-expanded', opening);
}

function setMobileLotPickerScrollLock(on) {
    if (!isMobileLayout()) return;
    const root = document.documentElement;
    if (on) {
        root.classList.add('mobile-lot-picker-active');
        document.body.classList.add('mobile-lot-picker-active');
    } else {
        root.classList.remove('mobile-lot-picker-active');
        document.body.classList.remove('mobile-lot-picker-active');
    }
}

/** iOS keyboard / viewport: extra bottom inset so list items aren’t under the keyboard */
function updateMobileKeyboardInset() {
    if (!window.visualViewport || !isMobileLayout()) {
        document.documentElement.style.setProperty('--mobile-keyboard-inset', '0px');
        return;
    }
    const vv = window.visualViewport;
    const hidden = Math.max(0, window.innerHeight - vv.height - vv.offsetTop);
    document.documentElement.style.setProperty('--mobile-keyboard-inset', hidden + 'px');
}

/** Row 1 height + fixed search/chip stack height for CSS (position fixed rows 2–3 below flowing row 1) */
function updateMobileChromeMetrics() {
    if (!isMobileLayout()) {
        document.documentElement.style.removeProperty('--jaypark-mobile-row1-bottom');
        document.documentElement.style.removeProperty('--jaypark-mobile-fixed-stack-h');
        if (map) map.invalidateSize();
        return;
    }
    const row1 = document.querySelector('.mobile-floating-topbar');
    const fixedEl = document.querySelector('.mobile-fixed-controls');
    if (row1) {
        const r = row1.getBoundingClientRect();
        /* Round: subpixel r.bottom jitter + avoid reflow loops from visualViewport scroll */
        document.documentElement.style.setProperty('--jaypark-mobile-row1-bottom', Math.round(r.bottom) + 'px');
    }
    if (fixedEl) {
        document.documentElement.style.setProperty(
            '--jaypark-mobile-fixed-stack-h',
            Math.round(fixedEl.getBoundingClientRect().height) + 'px'
        );
    }
    if (map) map.invalidateSize();
}

function openMobileLotPicker() {
    if (!isMobileLayout()) return;
    closeMobileTocDrawer();
    const container = document.querySelector('.container');
    if (container) container.classList.add('mobile-lot-picker-open');
    setMobileLotPickerScrollLock(true);
    updateMobileKeyboardInset();
    const navBtn = document.getElementById('tocBtnMob');
    if (navBtn) {
        navBtn.classList.add('lot-search-nav--back');
        navBtn.classList.remove('active');
    }
    applyLotSearchFilter();
    requestAnimationFrame(function () {
        requestAnimationFrame(updateMobileChromeMetrics);
    });
}

function closeMobileLotPicker() {
    const container = document.querySelector('.container');
    if (!container || !container.classList.contains('mobile-lot-picker-open')) return;
    container.classList.remove('mobile-lot-picker-open');
    setMobileLotPickerScrollLock(false);
    document.documentElement.style.setProperty('--mobile-keyboard-inset', '0px');
    const navBtn = document.getElementById('tocBtnMob');
    if (navBtn) navBtn.classList.remove('lot-search-nav--back');
    const search = document.getElementById('lot-search');
    if (search) search.blur();
    requestAnimationFrame(function () {
        updateMobileChromeMetrics();
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
    const lotId = String(lot.id);
    const lotNumber = String(lot.id).replace(/\D/g, ""); 
    if (basketballMode && (GAME_LOTS.includes(lotNumber) || GAME_GARAGES.includes(lotId))) {
        return "#FF0000";
    }
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
        syncDaySelectFromDate();
        const permit = document.getElementById('permit-select').value;
        const day = document.getElementById('day-select').value;
        const time = document.getElementById('time-input').value;
        const dateEl = document.getElementById('date-input');
        const viewDate = dateEl && dateEl.value ? dateEl.value : '';
        const params = new URLSearchParams({ permit, day, time, ...(viewDate ? { date: viewDate } : {}) });
        console.log('Fetching lots with params:', params.toString());
        const response = await fetch(`/api/lots?${params}`);

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

    let description = lot.description; 
    const lotId = String(lot.id);
    const lotNumber = String(lot.id).replace(/\D/g, "");

    if (basketballMode && (GAME_LOTS.includes(lotNumber) || GAME_GARAGES.includes(lotId))) {
        description = "GAME DAY RESTRICTION:\n\nThis lot is reserved for basketball game parking.";
    }
  
    document.getElementById('details-restrictions').textContent = description;

    // Reset report form and status on selecting lot
    document.getElementById('report-description').value = '';
    document.getElementById('report-start').value = '';
    document.getElementById('report-end').value = '';
    document.getElementById('report-status').textContent = '';


    //VIEW SPECIAL RESTRICTIONS
    document.getElementById('details-panel').classList.remove('hidden');
    if (selectedLot.specRestrict) {
        document.getElementById('spec-btn').hidden = false;
    } else {
        document.getElementById('spec-btn').hidden = true;
    }


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
    document.getElementById('spec-btn').hidden = true;
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



//New restriction viewing feature!
async function viewRestrictions() {
    //Open up the form.
    if (!selectedLot) return;
    document.body.classList.add('report-modal-active');
    document.getElementById('spec-overlay').classList.remove('hidden');
    document.getElementById('spec-modal-header').innerText = 'Active Special Restrictions for ' + selectedLot.name;

    
    try {
        //Retrieve relevant restrictions from database.
        syncDaySelectFromDate();
        const lot_id = selectedLot.id;
        const time = document.getElementById('time-input').value;
        const dateEl = document.getElementById('date-input');
        const viewDate = dateEl && dateEl.value ? dateEl.value : '';
        const params = new URLSearchParams({ lot_id, time, ...(viewDate ? { date: viewDate } : {}) });
        console.log('Fetching restrictions with params:', params.toString());
        const response = await fetch(`/api/restrictions?${params}`);

        if (!response.ok) {
            throw new Error(`API returned status ${response.status}: ${response.statusText}`);
        }

        specs = await response.json();
        console.log('We got them!', specs);

        if (!Array.isArray(specs)) {
            throw new Error('Expected restrictions to be an array, got: ' + typeof lots);
        }

        const list = document.getElementById('spec-list');
        list.innerHTML = ''; // clear old content

        //Add HTML elements for each special restriction.
        specs.forEach(spec => {
            const section = document.createElement('div');
            section.className = 'spec-item';

            section.innerHTML = `
                <p><strong>Description:</strong> ${spec.description}</p>
                <p><strong>Start:</strong> ${spec.start_date || 'N/A'}</p>
                <p><strong>End:</strong> ${spec.end_date || 'N/A'}</p>
                <p><strong>Disputes:</strong> ${spec.disputes || 0}</p>
                <button class="dispute-btn" data-report-id="${spec.id}">Dispute Report</button>
            `;
            const disputeBtn = section.querySelector('.dispute-btn');
            disputeBtn.addEventListener('click', () => disputeRestriction(spec.id));

            list.appendChild(section);

            applyDisputeCooldown(spec.id);
        });


    } catch (error) {
        console.error('Error loading restrictions:', error);
        alert('Failed to load special restrictions.');
    }


}

// track when report was last disputed
function disputeCooldownKey(reportId) {
    return 'dispute_cooldown_${reportId}'
}

// disable button and show live cooldown if button for reportId is currently on cooldown
function applyDisputeCooldown(reportId) {
    const btn = document.querySelector('.dispute-btn[data-report-id="${reportId}"]');
    if (!btn) return;

    const stored = localStorage.getItem(disputeCooldownKey(reportId));
    if (!stored) return;

    if (Date.now() < parseInt(stored, 10)) {
        btn.disabled = true;
    } else {
        localStorage.removeItem(disputeCooldownKey(reportId));
    }
}


async function disputeRestriction(reportId) {
    // block if still within cooldown window
    const stored = localStorage.getItem(disputeCooldownKey(reportId));
    if (stored && Date.now() < parseInt(stored, 10)) {
        return;
    }

    try {
        const response = await fetch('/api/dispute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ report_id: reportId })
        });

        if (response.ok) {
            const result = await response.json();

            // record cooldown timestamp before refreshing list
            localStorage.setItem(disputeCooldownKey(reportId), Date.now() + DISPUTE_COOLDOWN_MS);

            if (result.status === 'deleted') {
                alert('Dispute submitted! The restriction has been removed due to multiple disputes.');
            } else {
                alert('Dispute submitted successfully!');
            }
            // Refresh the restrictions list
            viewRestrictions();
        } else {
            const error = await response.json();
            alert('Failed to submit dispute: ' + (error.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error submitting dispute:', error);
        alert('Failed to submit dispute. Please try again.');
    }
}

function closeRestrictions() {
    document.body.classList.remove('report-modal-active');
    document.getElementById('spec-overlay').classList.add('hidden');
    document.getElementById('spec-modal-header').innerText = 'Active Special Restrictions for ' + selectedLot.name;
    const list = document.getElementById('spec-list');
    //VERY VERY VERY VERY IMPORTANT. Don't want unaccounted for HTML elements.
    if (list) list.innerHTML = '';
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
    const dateInputInit = document.getElementById('date-input');
    if (dateInputInit) dateInputInit.addEventListener('change', updateMarkers);
    document.getElementById('time-input').addEventListener('change', updateMarkers);
    document.getElementById('close-details').addEventListener('click', hideDetails);
    document.getElementById('report-btn').addEventListener('click', openReportModal);
    document.getElementById('report-modal-close').addEventListener('click', closeReportModal);
    document.getElementById('report-cancel').addEventListener('click', closeReportModal);
    document.getElementById('submit-report').addEventListener('click', submitReport);
    document.getElementById('spec-btn').addEventListener('click', viewRestrictions);
    document.getElementById('spec-close').addEventListener('click', closeRestrictions);

    const toggle = document.getElementById("basketball-toggle");
    const label = document.getElementById("basketball-label");

    if (toggle) {
        toggle.addEventListener("change", () => {
            basketballMode = toggle.checked;

            if (label) {
                if (basketballMode) {
                    label.classList.add("basketball-active");
                } else {
                    label.classList.remove("basketball-active");
                }
            }

            updateMarkers(); // refresh map
        });
    }

    document.getElementById('report-modal-overlay').addEventListener('click', function (e) {
        if (e.target === this) closeReportModal();
    });

    const lotSearch = document.getElementById('lot-search');
    const lotSearchSidebar = document.getElementById('lot-search-sidebar');
    const lotListPanel = document.querySelector('.lot-list-panel');

    const tocBtnMob = document.getElementById('tocBtnMob');
    const tocDrawerBackdrop = document.getElementById('tocDrawerBackdrop');
    const tocMenuMob = document.getElementById('tocMenuMob');

    if (tocDrawerBackdrop) {
        tocDrawerBackdrop.addEventListener('click', closeMobileTocDrawer);
    }
    if (tocMenuMob) {
        tocMenuMob.addEventListener('click', function (e) {
            e.stopPropagation();
        });
        tocMenuMob.querySelectorAll('a').forEach(function (a) {
            a.addEventListener('click', closeMobileTocDrawer);
        });
    }

    if (tocBtnMob) {
        tocBtnMob.addEventListener('click', function (e) {
            if (!isMobileLayout()) return;
            e.stopPropagation();
            const c = document.querySelector('.container');
            if (c && c.classList.contains('mobile-lot-picker-open')) {
                closeMobileLotPicker();
                closeMobileTocDrawer();
                return;
            }
            toggleMobileTocDrawer();
        });
    }

    // Top search
    if (lotSearch) {
        lotSearch.addEventListener('focus', function () {
            clearTimeout(lotSearchBlurTimer);
            openMobileLotPicker();
        });

        /* Do not close on blur: iOS keyboard ✓/Done blurs input but list should stay open. */

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
        const c = document.querySelector('.container');
        if (!isMobileLayout()) {
            if (c) c.classList.remove('mobile-lot-picker-open');
            setMobileLotPickerScrollLock(false);
            if (map) map.invalidateSize();
            updateMobileChromeMetrics();
        } else if (map) {
            map.invalidateSize();
            updateMobileKeyboardInset();
            updateMobileChromeMetrics();
        }
    });

    if (window.visualViewport) {
        window.visualViewport.addEventListener('resize', function () {
            updateMobileKeyboardInset();
            updateMobileChromeMetrics();
        });
        /* scroll fires on many taps (e.g. map) without real chrome size change — remeasuring row1.bottom jitters the row1–2 gap */
        window.visualViewport.addEventListener('scroll', function () {
            updateMobileKeyboardInset();
        });
    }

    if (typeof ResizeObserver !== 'undefined') {
        const row1El = document.querySelector('.mobile-floating-topbar');
        const fixedStackEl = document.querySelector('.mobile-fixed-controls');
        const ro = new ResizeObserver(function () {
            updateMobileChromeMetrics();
        });
        if (row1El) ro.observe(row1El);
        if (fixedStackEl) ro.observe(fixedStackEl);
    }
    updateMobileChromeMetrics();

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