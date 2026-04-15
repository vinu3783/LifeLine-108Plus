/**
 * Offline Map Manager for the ambulance driver app
 * Handles map tile caching and offline navigation
 */
class OfflineMapManager {
    constructor() {
        this.isOnline = navigator.onLine;
        this.mapBounds = null;
        this.offlineMapElement = null;
        this.offlineBanner = null;
        
        // Set up event listeners
        window.addEventListener('online', () => this.handleConnectivityChange(true));
        window.addEventListener('offline', () => this.handleConnectivityChange(false));
    }
    
    // Initialize the offline map manager
    init(map, offlineMapElement, offlineBanner) {
        this.map = map;
        this.offlineMapElement = offlineMapElement;
        this.offlineBanner = offlineBanner;
        
        // Show/hide offline elements based on current connectivity
        this.updateOfflineUI(this.isOnline);
        
        // Register the service worker
        this.registerServiceWorker();
    }
    
    // Register service worker for offline support
    registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/service-worker.js')
                .then(registration => {
                    console.log('Service Worker registered with scope:', registration.scope);
                })
                .catch(error => {
                    console.error('Service Worker registration failed:', error);
                });
            
            // Listen for messages from the service worker
            navigator.serviceWorker.addEventListener('message', event => {
                if (event.data && event.data.type === 'sync-complete') {
                    console.log(`Sync completed: ${event.data.count} items synced`);
                    // You could show a notification here
                }
            });
        } else {
            console.warn('Service workers are not supported in this browser');
        }
    }
    
    // Handle online/offline changes
    handleConnectivityChange(isOnline) {
        this.isOnline = isOnline;
        this.updateOfflineUI(isOnline);
        
        if (isOnline) {
            console.log('App is now online');
            // Trigger background sync
            this.triggerSync();
        } else {
            console.log('App is now offline');
        }
    }
    
    // Update UI based on online/offline status
    updateOfflineUI(isOnline) {
        if (this.offlineBanner) {
            this.offlineBanner.style.display = isOnline ? 'none' : 'block';
        }
        
        // Update other UI elements that depend on connectivity
        document.querySelectorAll('.online-only').forEach(el => {
            el.disabled = !isOnline;
        });
    }
    
    // Trigger background sync when online
    triggerSync() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.ready
                .then(registration => {
                    return registration.sync.register('sync-outbox');
                })
                .catch(err => {
                    console.error('Background sync registration failed:', err);
                });
        }
    }
    
    // Cache the current map area
    cacheMapArea() {
        if (!this.map) return;
        
        // Get current map bounds
        const bounds = this.map.getBounds();
        this.mapBounds = bounds;
        
        // Get zoom levels to cache
        const currentZoom = this.map.getZoom();
        const minZoom = Math.max(currentZoom - 2, 10); // Don't go below zoom level 10
        const maxZoom = currentZoom + 1;
        
        console.log(`Caching map area from zoom ${minZoom} to ${maxZoom}`);
        
        // Calculate tile URLs to cache
        const tilesToCache = this.getTileUrlsInBounds(bounds, minZoom, maxZoom);
        
        // Cache tiles
        this.cacheTiles(tilesToCache);
    }
    
    // Get tile URLs for an area
    getTileUrlsInBounds(bounds, minZoom, maxZoom) {
        const tiles = [];
        const tileLayer = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
        
        // For each zoom level
        for (let z = minZoom; z <= maxZoom; z++) {
            // Get tile coordinates for the bounds
            const northEast = bounds.getNorthEast();
            const southWest = bounds.getSouthWest();
            
            // Convert lat/lng to tile numbers
            const neTile = this.latLngToTile(northEast.lat, northEast.lng, z);
            const swTile = this.latLngToTile(southWest.lat, southWest.lng, z);
            
            // Get all tiles in the range
            for (let x = Math.min(swTile.x, neTile.x); x <= Math.max(swTile.x, neTile.x); x++) {
                for (let y = Math.min(swTile.y, neTile.y); y <= Math.max(swTile.y, neTile.y); y++) {
                    // Generate the URL for this tile
                    const url = tileLayer
                        .replace('{z}', z)
                        .replace('{x}', x)
                        .replace('{y}', y)
                        .replace('{s}', 'a'); // Use a single subdomain
                    
                    tiles.push(url);
                }
            }
        }
        
        return tiles;
    }
    
    // Convert lat/lng to tile coordinates
    latLngToTile(lat, lng, zoom) {
        const n = Math.pow(2, zoom);
        const x = Math.floor((lng + 180) / 360 * n);
        const y = Math.floor((1 - Math.log(Math.tan(lat * Math.PI / 180) + 1 / Math.cos(lat * Math.PI / 180)) / Math.PI) / 2 * n);
        return { x, y };
    }
    
    // Cache a list of tile URLs
    async cacheTiles(tileUrls) {
        if (!('caches' in window)) {
            console.warn('Cache API not supported');
            return;
        }
        
        try {
            const cache = await caches.open('map-tiles-cache');
            
            // Limit the number of tiles to cache to avoid overwhelming the browser
            const tilesToCache = tileUrls.slice(0, 200);
            
            console.log(`Caching ${tilesToCache.length} map tiles...`);
            
            const promises = tilesToCache.map(url => {
                return fetch(url)
                    .then(response => {
                        if (response.ok) {
                            return cache.put(url, response);
                        }
                    })
                    .catch(error => {
                        console.warn(`Failed to cache tile: ${url}`, error);
                    });
            });
            
            await Promise.all(promises);
            console.log('Map tiles cached successfully');
        } catch (error) {
            console.error('Error caching map tiles:', error);
        }
    }
    
    // Cache current emergency assignment for offline use
    cacheEmergencyAssignment(emergency) {
        if (!emergency) return;
        
        if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({
                type: 'cache-emergency',
                emergency_call: emergency
            });
        }
        
        // Also store in IndexedDB for redundancy
        this.storeEmergencyInIndexedDB(emergency);
    }
    
    // Store emergency in IndexedDB
    async storeEmergencyInIndexedDB(emergency) {
        try {
            const db = await this.openOfflineDB();
            const tx = db.transaction('emergency-assignments', 'readwrite');
            const store = tx.objectStore('emergency-assignments');
            
            await store.put({
                id: emergency.id,
                data: emergency,
                timestamp: Date.now()
            });
            
            console.log('Emergency assignment stored in IndexedDB');
        } catch (error) {
            console.error('Error storing emergency in IndexedDB:', error);
        }
    }
    
    // Open the offline database
    openOfflineDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('ers-offline-db', 1);
            
            request.onerror = event => {
                reject('IndexedDB error');
            };
            
            request.onsuccess = event => {
                resolve(event.target.result);
            };
            
            request.onupgradeneeded = event => {
                const db = event.target.result;
                
                // Create outbox store for pending requests
                if (!db.objectStoreNames.contains('outbox')) {
                    db.createObjectStore('outbox', { keyPath: 'timestamp' });
                }
                
                // Create store for emergency assignments
                if (!db.objectStoreNames.contains('emergency-assignments')) {
                    db.createObjectStore('emergency-assignments', { keyPath: 'id' });
                }
                
                // Create store for location updates
                if (!db.objectStoreNames.contains('location-updates')) {
                    db.createObjectStore('location-updates', { keyPath: 'timestamp' });
                }
            };
        });
    }
    
    // Store location update for later syncing
    async storeLocationUpdate(ambulanceId, latitude, longitude) {
        try {
            const db = await this.openOfflineDB();
            const tx = db.transaction('location-updates', 'readwrite');
            const store = tx.objectStore('location-updates');
            
            await store.add({
                ambulance_id: ambulanceId,
                latitude: latitude,
                longitude: longitude,
                timestamp: Date.now(),
                synced: false
            });
            
            console.log('Location update stored for later sync');
            return true;
        } catch (error) {
            console.error('Error storing location update:', error);
            return false;
        }
    }
}

// Create global instance
window.offlineMapManager = new OfflineMapManager();