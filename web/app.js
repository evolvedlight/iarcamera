// State variables
let dates = [];
let photos = [];
let currentIndex = -1;
let isPlaying = false;
let playbackSpeed = 10; // fps
let isLooping = true;
let selectedDates = new Set();
let playbackTimer = null;
const preloadCache = new Map();
let preloadQueue = [];
let isPreloadingBackground = false;

// Zoom and Pan State
let scale = 1;
let panX = 0;
let panY = 0;
let isDragging = false;
let startX = 0;
let startY = 0;

// DOM Elements
let viewport, imageContainer, slider, tooltip;
let activeImgEl = null;
let bufferImgEl = null;
let currentLoadId = 0;

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    viewport = document.getElementById('viewer-viewport');
    imageContainer = document.getElementById('image-container');
    slider = document.getElementById('slider-timeline');
    tooltip = document.getElementById('timeline-tooltip');

    activeImgEl = document.getElementById('img-active');
    bufferImgEl = document.getElementById('img-buffer');

    init();
});

async function init() {
    setupControls();
    setupZoomPan();
    
    // Fetch dates first
    await fetchDates();
    
    // Apply default preset: Last 3 Days
    if (dates.length > 0) {
        applyPreset('3');
    } else {
        document.getElementById('txt-current-date').textContent = "No camera photos found";
        document.getElementById('txt-hud-time').textContent = "--:--:--";
        document.getElementById('txt-hud-date').textContent = "----------";
    }
}

// Fetch available dates from API
async function fetchDates() {
    try {
        const response = await fetch('/api/dates');
        dates = await response.json();
        renderDatesList();
    } catch (e) {
        console.error("Failed to fetch dates", e);
    }
}

// Fetch photos for selected dates
async function fetchPhotos(params = {}) {
    showLoadingSpinner(true);
    let url = '/api/photos';
    const queryParts = [];
    
    if (params.dates && params.dates.length > 0) {
        queryParts.push(`dates=${encodeURIComponent(params.dates.join(','))}`);
    } else if (params.days) {
        queryParts.push(`days=${params.days}`);
    }
    
    if (queryParts.length > 0) {
        url += '?' + queryParts.join('&');
    }
    
    try {
        const response = await fetch(url);
        photos = await response.json();
        
        // Update timeline range
        slider.min = 0;
        slider.max = Math.max(0, photos.length - 1);
        
        if (photos.length > 0) {
            // Go to the last frame by default so they see the latest image!
            currentIndex = photos.length - 1;
            updateFrame(currentIndex);
            
            // Build timeline ticks
            buildTimelineTicks();
            
            // Start background preloading
            startBackgroundPreload();
        } else {
            // Handle no photos
            document.getElementById('txt-current-date').textContent = "No photos selected";
            document.getElementById('txt-hud-time').textContent = "--:--:--";
            document.getElementById('txt-hud-date').textContent = "----------";
            document.getElementById('txt-current-filename').textContent = "";
            document.getElementById('txt-frame-index').textContent = "0 / 0";
            document.getElementById('img-active').removeAttribute('src');
            document.getElementById('img-buffer').removeAttribute('src');
        }
    } catch (e) {
        console.error("Failed to fetch photos", e);
    } finally {
        showLoadingSpinner(false);
    }
}

// Render dates list in sidebar
function renderDatesList() {
    const container = document.getElementById('date-list');
    container.innerHTML = '';
    
    if (dates.length === 0) {
        container.innerHTML = '<div class="loading-mini">No dates found</div>';
        return;
    }
    
    dates.forEach(item => {
        const div = document.createElement('div');
        div.className = 'date-item';
        
        const isChecked = selectedDates.has(item.date);
        
        div.innerHTML = `
            <div class="date-item-left">
                <input type="checkbox" id="chk-${item.date}" data-date="${item.date}" ${isChecked ? 'checked' : ''}>
                <label for="chk-${item.date}" class="date-label">${item.date}</label>
            </div>
            <span class="date-count">${item.count}</span>
        `;
        
        // Checkbox event
        const checkbox = div.querySelector('input');
        checkbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                selectedDates.add(item.date);
            } else {
                selectedDates.delete(item.date);
            }
            
            // Remove active state from presets
            deactivatePresets();
            
            // Reload photos
            loadSelectedPhotos();
        });
        
        // Click row toggles checkbox
        div.addEventListener('click', (e) => {
            if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'LABEL') {
                checkbox.checked = !checkbox.checked;
                checkbox.dispatchEvent(new Event('change'));
            }
        });
        
        container.appendChild(div);
    });
}

// Apply quick filters
function applyPreset(days) {
    deactivatePresets();
    
    // Find preset button
    const btn = document.querySelector(`.preset-btn[data-preset="${days}"]`);
    if (btn) btn.classList.add('active');
    
    selectedDates.clear();
    
    if (days === 'all') {
        dates.forEach(d => selectedDates.add(d.date));
    } else {
        const num = parseInt(days);
        const targetDates = dates.slice(0, num);
        targetDates.forEach(d => selectedDates.add(d.date));
    }
    
    // Update checkboxes
    dates.forEach(item => {
        const chk = document.getElementById(`chk-${item.date}`);
        if (chk) {
            chk.checked = selectedDates.has(item.date);
        }
    });
    
    loadSelectedPhotos();
}

function deactivatePresets() {
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.classList.remove('active');
    });
}

function loadSelectedPhotos() {
    pause();
    if (selectedDates.size === 0) {
        photos = [];
        updateFrame(0);
        buildTimelineTicks();
        return;
    }
    fetchPhotos({ dates: Array.from(selectedDates) });
}

// Update Active Frame
let loadingTimeout = null;
function showLoadingSpinner(show) {
    const spinner = document.getElementById('loading-overlay');
    if (show) {
        if (!loadingTimeout) {
            loadingTimeout = setTimeout(() => {
                spinner.classList.remove('hidden');
            }, 200); // Only show if takes longer than 200ms
        }
    } else {
        if (loadingTimeout) {
            clearTimeout(loadingTimeout);
            loadingTimeout = null;
        }
        spinner.classList.add('hidden');
    }
}

function updateFrame(index) {
    if (photos.length === 0) return;
    
    // Wrap index range
    if (index < 0) index = 0;
    if (index >= photos.length) index = photos.length - 1;
    
    currentIndex = index;
    const photo = photos[currentIndex];
    
    // Update labels
    const timeParts = photo.time.split(' ');
    document.getElementById('txt-hud-time').textContent = timeParts[1] || '--:--:--';
    document.getElementById('txt-hud-date').textContent = timeParts[0] || photo.date;
    document.getElementById('txt-current-date').textContent = formatDateHeader(photo.date);
    document.getElementById('txt-current-filename').textContent = photo.filename;
    document.getElementById('txt-frame-index').textContent = `${currentIndex + 1} / ${photos.length}`;
    
    slider.value = currentIndex;
    
    const targetUrl = '/' + photo.path;
    
    // If the active image already shows this, do nothing
    if (activeImgEl.src === window.location.origin + targetUrl || activeImgEl.getAttribute('src') === targetUrl) {
        showLoadingSpinner(false);
        return;
    }
    
    // Synchronous cached fast-path:
    // If the image is already preloaded and complete in the cache,
    // we can set activeImgEl.src directly to bypass double-buffering,
    // which avoids async promise scheduling overhead and guarantees
    // steady 60fps playback.
    const cachedImg = preloadCache.get(targetUrl);
    if (cachedImg && cachedImg.complete) {
        currentLoadId++; // Cancel pending async operations
        activeImgEl.src = targetUrl;
        showLoadingSpinner(false);
        preloadNearbyFrames();
        return;
    }
    
    // Increment request ID to cancel older outstanding requests
    const loadId = ++currentLoadId;
    
    showLoadingSpinner(true);
    
    // Set src on buffer element
    bufferImgEl.src = targetUrl;
    
    // Define the swap function
    const performSwap = () => {
        if (loadId !== currentLoadId) return; // Discard outdated requests
        
        // Swap active classes in DOM
        activeImgEl.classList.remove('active');
        bufferImgEl.classList.add('active');
        
        // Swap JS references
        const temp = activeImgEl;
        activeImgEl = bufferImgEl;
        bufferImgEl = temp;
        
        showLoadingSpinner(false);
        preloadNearbyFrames();
    };

    if (typeof bufferImgEl.decode === 'function') {
        bufferImgEl.decode()
            .then(performSwap)
            .catch(err => {
                // Ignore EncodingError (aborted load due to src change)
                if (loadId === currentLoadId) {
                    if (err.name !== 'EncodingError') {
                        performSwap();
                    }
                }
            });
    } else {
        // Fallback for older browsers
        bufferImgEl.onload = performSwap;
        bufferImgEl.onerror = () => {
            if (loadId === currentLoadId) showLoadingSpinner(false);
        };
    }
}

function formatDateHeader(dateStr) {
    try {
        const parts = dateStr.split('-');
        const date = new Date(parts[0], parts[1] - 1, parts[2]);
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        return date.toLocaleDateString('en-US', options);
    } catch (e) {
        return dateStr;
    }
}

// Preload adjacent frames
function preloadNearbyFrames() {
    if (photos.length === 0) return;
    
    // Dynamic preloading range based on playback speed (minimum 25, up to 150)
    const range = Math.min(photos.length, Math.max(25, Math.round(playbackSpeed * 2.5)));
    const indicesToPreload = [];
    
    for (let i = 1; i <= range; i++) {
        // Prioritize forward direction
        const fwdIdx = currentIndex + i;
        if (fwdIdx < photos.length) indicesToPreload.push(fwdIdx);
        
        // Backward direction
        const bwdIdx = currentIndex - i;
        if (bwdIdx >= 0) indicesToPreload.push(bwdIdx);
    }
    
    indicesToPreload.forEach(idx => {
        const path = photos[idx].path;
        const url = '/' + path;
        
        if (!preloadCache.has(url)) {
            const img = new Image();
            img.src = url;
            preloadCache.set(url, img);
            
            // Keep cache size bounded to the total photo list size (min 300)
            // to prevent the browser from evicting frames during a playback loop.
            const maxCacheSize = Math.max(300, photos.length);
            if (preloadCache.size > maxCacheSize) {
                const firstKey = preloadCache.keys().next().value;
                preloadCache.delete(firstKey);
            }
        }
    });
}

// Sequential background preloading to cache the entire timeline
function startBackgroundPreload() {
    if (photos.length === 0) return;
    
    // Create list of all frame indices
    const indices = [];
    for (let i = 0; i < photos.length; i++) {
        indices.push(i);
    }
    
    // Sort indices to prioritize frames closest to the current frame
    indices.sort((a, b) => {
        const distA = Math.abs(a - currentIndex);
        const distB = Math.abs(b - currentIndex);
        return distA - distB;
    });
    
    // Filter out URLs that are already preloaded
    preloadQueue = indices.map(idx => '/' + photos[idx].path).filter(url => !preloadCache.has(url));
    
    if (!isPreloadingBackground) {
        isPreloadingBackground = true;
        preloadNextInQueue();
    }
}

function preloadNextInQueue() {
    // If playback is playing at high speeds, temporarily pause background preloading
    // to give 100% of browser resources to playback rendering.
    if (isPlaying && playbackSpeed >= 30) {
        isPreloadingBackground = false;
        return;
    }
    
    if (preloadQueue.length === 0) {
        isPreloadingBackground = false;
        return;
    }
    
    const url = preloadQueue.shift();
    
    if (preloadCache.has(url)) {
        // Already loaded, process next immediately
        preloadNextInQueue();
        return;
    }
    
    const img = new Image();
    img.onload = img.onerror = () => {
        // Check after loading if we should continue
        setTimeout(preloadNextInQueue, 25);
    };
    img.src = url;
    preloadCache.set(url, img);
    
    // Keep cache bounded
    const maxCacheSize = Math.max(300, photos.length);
    if (preloadCache.size > maxCacheSize) {
        const firstKey = preloadCache.keys().next().value;
        preloadCache.delete(firstKey);
    }
}

// Draw timeline ticks
function buildTimelineTicks() {
    const ticksContainer = document.getElementById('timeline-ticks');
    ticksContainer.innerHTML = '';
    
    if (photos.length === 0) return;
    
    let lastDate = null;
    const dayBreaks = [];
    
    // Find all day breaks first
    for (let i = 0; i < photos.length; i++) {
        const photo = photos[i];
        if (photo.date !== lastDate) {
            dayBreaks.push({
                index: i,
                date: photo.date,
                month: photo.date.substring(0, 7)
            });
            lastDate = photo.date;
        }
    }
    
    const totalDays = dayBreaks.length;
    
    // Determine label spacing for day breaks
    // We want at most ~8-10 labels on the timeline to prevent overlap
    let labelInterval = 1;
    let showMonthsOnly = false;
    
    if (totalDays > 120) {
        showMonthsOnly = true;
    } else if (totalDays > 40) {
        labelInterval = 7; // weekly labels
    } else if (totalDays > 15) {
        labelInterval = 3; // every 3 days
    }
    
    // Render day breaks
    dayBreaks.forEach((db, dbIdx) => {
        const pct = (db.index / photos.length) * 100;
        
        // Draw tick line
        const marker = document.createElement('div');
        marker.className = 'tick-marker day-break';
        marker.style.left = `${pct}%`;
        ticksContainer.appendChild(marker);
        
        // Draw label based on spacing rules
        let shouldShowLabel = false;
        let labelText = '';
        
        if (showMonthsOnly) {
            // Show label when month changes (or first day)
            if (dbIdx === 0) {
                shouldShowLabel = true;
                labelText = formatMonthLabel(db.date);
            } else {
                const prevDb = dayBreaks[dbIdx - 1];
                if (db.month !== prevDb.month) {
                    shouldShowLabel = true;
                    labelText = formatMonthLabel(db.date);
                }
            }
        } else {
            // Show label based on intervals
            if (dbIdx % labelInterval === 0 || dbIdx === totalDays - 1) {
                shouldShowLabel = true;
                labelText = formatDateLabel(db.date);
            }
        }
        
        if (shouldShowLabel && labelText) {
            const label = document.createElement('div');
            label.className = 'tick-label';
            label.style.left = `${pct}%`;
            label.textContent = labelText;
            ticksContainer.appendChild(label);
        }
    });
    
    // Draw minor time ticks (only if total day breaks is small, otherwise it gets too busy)
    if (totalDays <= 5) {
        const step = Math.max(1, Math.round(photos.length / 8));
        for (let i = step; i < photos.length - step; i += step) {
            // Ensure we aren't drawing right on top of a day break
            const nearDayBreak = dayBreaks.some(db => Math.abs(db.index - i) < (step / 3));
            if (!nearDayBreak) {
                const photo = photos[i];
                const pct = (i / photos.length) * 100;
                
                const marker = document.createElement('div');
                marker.className = 'tick-marker';
                marker.style.left = `${pct}%`;
                ticksContainer.appendChild(marker);
                
                const label = document.createElement('div');
                label.className = 'tick-label';
                label.style.left = `${pct}%`;
                const timeParts = photo.time.split(' ');
                label.textContent = timeParts[1] ? timeParts[1].substring(0, 5) : '';
                ticksContainer.appendChild(label);
            }
        }
    }
}

function formatDateLabel(dateStr) {
    const parts = dateStr.split('-');
    return `${getMonthAbbr(parseInt(parts[1]))} ${parseInt(parts[2])}`;
}

function formatMonthLabel(dateStr) {
    const parts = dateStr.split('-');
    return `${getMonthAbbr(parseInt(parts[1]))} '${parts[0].substring(2)}`;
}

function getMonthAbbr(monthNum) {
    const months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return months[monthNum] || '';
}

// Playback Logic
function play() {
    if (isPlaying) return;
    isPlaying = true;
    
    document.querySelector('.icon-play').classList.add('hidden');
    document.querySelector('.icon-pause').classList.remove('hidden');
    
    showHUDIcon('play-icon');
    
    const interval = 1000 / playbackSpeed;
    playbackTimer = setInterval(() => {
        let nextIndex = currentIndex + 1;
        if (nextIndex >= photos.length) {
            if (isLooping) {
                nextIndex = 0;
            } else {
                pause();
                return;
            }
        }
        updateFrame(nextIndex);
    }, interval);
}

function pause() {
    if (!isPlaying) return;
    isPlaying = false;
    
    document.querySelector('.icon-play').classList.remove('hidden');
    document.querySelector('.icon-pause').classList.add('hidden');
    
    showHUDIcon('pause-icon');
    
    if (playbackTimer) {
        clearInterval(playbackTimer);
        playbackTimer = null;
    }
    
    // Restart background preloading for the rest of the frames
    startBackgroundPreload();
}

function togglePlay() {
    if (isPlaying) pause();
    else play();
}

function showHUDIcon(className) {
    const icon = document.querySelector(`.hud-center-icon.${className}`);
    if (!icon) return;
    
    icon.classList.remove('hidden');
    const newIcon = icon.cloneNode(true);
    icon.parentNode.replaceChild(newIcon, icon);
    
    setTimeout(() => {
        newIcon.classList.add('hidden');
    }, 800);
}

function stepForward(amount) {
    if (photos.length === 0) return;
    let nextIndex = currentIndex + amount;
    if (nextIndex >= photos.length) {
        nextIndex = isLooping ? 0 : photos.length - 1;
    }
    updateFrame(nextIndex);
}

function stepBackward(amount) {
    if (photos.length === 0) return;
    let prevIndex = currentIndex - amount;
    if (prevIndex < 0) {
        prevIndex = isLooping ? photos.length - 1 : 0;
    }
    updateFrame(prevIndex);
}

function adjustSpeed(direction) {
    const select = document.getElementById('select-speed');
    const options = Array.from(select.options);
    let newIndex = select.selectedIndex + direction;
    newIndex = Math.max(0, Math.min(newIndex, options.length - 1));
    select.selectedIndex = newIndex;
    select.dispatchEvent(new Event('change'));
}

function toggleLoop() {
    isLooping = !isLooping;
    const btn = document.getElementById('btn-loop');
    if (isLooping) btn.classList.add('active');
    else btn.classList.remove('active');
}

// Zoom & Pan System
function setupZoomPan() {
    viewport.addEventListener('wheel', handleZoom, { passive: false });
    
    viewport.addEventListener('mousedown', (e) => {
        if (e.button !== 0) return; // Only left click
        isDragging = true;
        startX = e.clientX - panX;
        startY = e.clientY - panY;
        viewport.style.cursor = 'grabbing';
    });

    window.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        panX = e.clientX - startX;
        panY = e.clientY - startY;
        applyTransform();
    });

    window.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            viewport.style.cursor = scale > 1 ? 'grab' : 'default';
        }
    });

    viewport.addEventListener('dblclick', resetZoom);
}

function handleZoom(e) {
    e.preventDefault();
    const rect = viewport.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const zoomFactor = 1.15;
    const nextScale = e.deltaY < 0 
        ? Math.min(scale * zoomFactor, 10) 
        : Math.max(scale / zoomFactor, 1);

    if (nextScale === 1) {
        resetZoom();
    } else {
        // Zoom relative to mouse cursor position
        const originX = mouseX - rect.width / 2;
        const originY = mouseY - rect.height / 2;
        
        panX = originX - (originX - panX) * (nextScale / scale);
        panY = originY - (originY - panY) * (nextScale / scale);
        scale = nextScale;
        
        applyTransform();
    }
}

function resetZoom() {
    scale = 1;
    panX = 0;
    panY = 0;
    applyTransform();
}

function applyTransform() {
    imageContainer.style.transform = `translate(${panX}px, ${panY}px) scale(${scale})`;
    
    const badgeZoom = document.getElementById('badge-zoom');
    const txtZoomLevel = document.getElementById('txt-zoom-level');
    
    if (scale > 1) {
        badgeZoom.classList.remove('hidden');
        txtZoomLevel.textContent = `${Math.round(scale * 100)}%`;
        viewport.style.cursor = 'grab';
    } else {
        badgeZoom.classList.add('hidden');
        viewport.style.cursor = 'default';
    }
}

// Wire Controls and Events
function setupControls() {
    // Buttons
    document.getElementById('btn-play-pause').addEventListener('click', togglePlay);
    document.getElementById('btn-prev').addEventListener('click', () => { pause(); stepBackward(1); });
    document.getElementById('btn-next').addEventListener('click', () => { pause(); stepForward(1); });
    document.getElementById('btn-jump-back').addEventListener('click', () => { pause(); stepBackward(10); });
    document.getElementById('btn-jump-forward').addEventListener('click', () => { pause(); stepForward(10); });
    document.getElementById('btn-first').addEventListener('click', () => { pause(); updateFrame(0); });
    document.getElementById('btn-last').addEventListener('click', () => { pause(); updateFrame(photos.length - 1); });
    document.getElementById('btn-loop').addEventListener('click', toggleLoop);
    document.getElementById('btn-reset-zoom').addEventListener('click', resetZoom);

    // Speed Selector
    document.getElementById('select-speed').addEventListener('change', (e) => {
        playbackSpeed = parseInt(e.target.value);
        if (isPlaying) {
            pause();
            play();
        }
    });

    // Timeline Slider input (active dragging)
    slider.addEventListener('input', (e) => {
        pause();
        updateFrame(parseInt(e.target.value));
    });
    
    // Slider drag completed (mouse release)
    slider.addEventListener('change', (e) => {
        startBackgroundPreload();
    });

    // Timeline Slider hover tooltip
    slider.addEventListener('mousemove', (e) => {
        if (photos.length === 0) return;
        
        const rect = slider.getBoundingClientRect();
        const offsetX = e.clientX - rect.left;
        const pct = Math.max(0, Math.min(offsetX / rect.width, 1));
        const hoverIdx = Math.round(pct * (photos.length - 1));
        
        if (hoverIdx >= 0 && hoverIdx < photos.length) {
            const photo = photos[hoverIdx];
            tooltip.classList.remove('hidden');
            tooltip.style.left = `${offsetX}px`;
            
            const timeStr = photo.time.split(' ')[1] || '';
            tooltip.textContent = `${photo.date} ${timeStr.substring(0, 5)}`;
        }
    });

    slider.addEventListener('mouseleave', () => {
        tooltip.classList.add('hidden');
    });

    // Bulk Select Buttons
    document.getElementById('btn-select-all').addEventListener('click', () => {
        dates.forEach(d => selectedDates.add(d.date));
        renderDatesList();
        loadSelectedPhotos();
    });

    document.getElementById('btn-select-none').addEventListener('click', () => {
        selectedDates.clear();
        deactivatePresets();
        renderDatesList();
        loadSelectedPhotos();
    });

    // Presets Click Handles
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const presetVal = e.target.getAttribute('data-preset');
            applyPreset(presetVal);
        });
    });

    // Help Modal
    const helpModal = document.getElementById('help-modal');
    const toggleHelpModal = () => helpModal.classList.toggle('hidden');
    
    document.getElementById('btn-help-trigger').addEventListener('click', toggleHelpModal);
    document.getElementById('btn-modal-close').addEventListener('click', toggleHelpModal);
    helpModal.addEventListener('click', (e) => {
        if (e.target === helpModal) toggleHelpModal();
    });

    // Keyboard Navigation
    window.addEventListener('keydown', (e) => {
        if (['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName)) return;
        
        switch (e.key) {
            case ' ':
                e.preventDefault();
                togglePlay();
                break;
            case 'ArrowRight':
            case 'd':
            case 'D':
                e.preventDefault();
                pause();
                stepForward(1);
                break;
            case 'ArrowLeft':
            case 'a':
            case 'A':
                e.preventDefault();
                pause();
                stepBackward(1);
                break;
            case ']':
            case 'e':
            case 'E':
                e.preventDefault();
                pause();
                stepForward(10);
                break;
            case '[':
            case 'q':
            case 'Q':
                e.preventDefault();
                pause();
                stepBackward(10);
                break;
            case 'ArrowUp':
            case 'w':
            case 'W':
                e.preventDefault();
                adjustSpeed(1);
                break;
            case 'ArrowDown':
            case 's':
            case 'S':
                e.preventDefault();
                adjustSpeed(-1);
                break;
            case 'l':
            case 'L':
                e.preventDefault();
                toggleLoop();
                break;
            case 'z':
            case 'Z':
            case 'r':
            case 'R':
                e.preventDefault();
                resetZoom();
                break;
            case 'Home':
                e.preventDefault();
                pause();
                updateFrame(0);
                break;
            case 'End':
                e.preventDefault();
                pause();
                updateFrame(photos.length - 1);
                break;
            case '?':
                e.preventDefault();
                toggleHelpModal();
                break;
        }
    });
}
