// service-worker.js
const CACHE_NAME = 'ers-ambulance-app-v1';
const OFFLINE_URL = '/frontend/ambulance_app/offline.html';
const TILE_CACHE_NAME = 'map-tiles-cache';

// Assets to cache for offline use
const STATIC_ASSETS = [
  '/frontend/ambulance_app/index.html',
  '/frontend/ambulance_app/css/styles.css',
  '/frontend/ambulance_app/js/app.js',
  '/frontend/ambulance_app/offline.html',
  '/frontend/ambulance_app/images/ambulance-marker.png',
  '/frontend/ambulance_app/images/emergency-marker.png',
  '/frontend/ambulance_app/images/offline-map.png',
  'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.css',
  'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.js',
  'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  'https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.min.js'
];

// Install event - cache static assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.filter(name => {
          return name !== CACHE_NAME && name !== TILE_CACHE_NAME;
        }).map(name => {
          console.log('Deleting old cache:', name);
          return caches.delete(name);
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Helper to determine if a request is for a map tile
function isMapTile(url) {
  return url.includes('tile.openstreetmap.org');
}

// Cache a copy of map tiles as they're requested
async function cacheMapTile(request, response) {
  const cache = await caches.open(TILE_CACHE_NAME);
  cache.put(request, response.clone());
  return response;
}

// Fetch event - serve cached content when offline
self.addEventListener('fetch', event => {
  // Skip cross-origin requests
  if (!event.request.url.startsWith(self.location.origin) && 
      !isMapTile(event.request.url)) {
    return;
  }

  // Special handling for map tiles
  if (isMapTile(event.request.url)) {
    event.respondWith(
      fetch(event.request)
        .then(response => cacheMapTile(event.request, response))
        .catch(() => {
          return caches.match(event.request);
        })
    );
    return;
  }

  // Handle API requests
  if (event.request.url.includes('/api/')) {
    if (event.request.method === 'GET') {
      // Network-first strategy for GET API requests
      event.respondWith(
        fetch(event.request)
          .then(response => {
            // Clone the response to cache it
            const responseToCache = response.clone();
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });
            return response;
          })
          .catch(() => {
            // If network fails, try to return cached response
            return caches.match(event.request)
              .then(cachedResponse => {
                if (cachedResponse) {
                  return cachedResponse;
                }
                
                // For emergency assignment requests, serve cached fallback
                if (event.request.url.includes('/get-assignment/')) {
                  return caches.match('/api/ambulance/cached-assignment');
                }
                
                // Return offline JSON response
                return new Response(
                  JSON.stringify({
                    offline: true,
                    success: false,
                    error: "You are currently offline"
                  }),
                  {
                    headers: { 'Content-Type': 'application/json' }
                  }
                );
              });
          })
      );
    } else {
      // For POST/PUT requests, store in IndexedDB when offline
      if (!navigator.onLine) {
        event.respondWith(
          caches.match(OFFLINE_URL)
            .then(response => {
              // Store request for later sync
              storeRequestForSync(event.request.clone());
              
              // Return an "accepted" response
              return new Response(
                JSON.stringify({
                  offline: true,
                  queued: true,
                  message: "Request stored for processing when online"
                }),
                {
                  headers: { 'Content-Type': 'application/json' }
                }
              );
            })
        );
      }
    }
    return;
  }

  // For regular file requests (HTML, CSS, JS, etc.), use cache-first strategy
  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        if (cachedResponse) {
          return cachedResponse;
        }
        
        return fetch(event.request)
          .then(response => {
            // Cache new responses
            if (response.ok && response.type === 'basic') {
              const responseToCache = response.clone();
              caches.open(CACHE_NAME)
                .then(cache => {
                  cache.put(event.request, responseToCache);
                });
            }
            return response;
          })
          .catch(error => {
            // If it's a navigation, serve offline page
            if (event.request.mode === 'navigate') {
              return caches.match(OFFLINE_URL);
            }
            
            // Otherwise, propagate the error
            throw error;
          });
      })
  );
});

// Store offline requests for later sync
async function storeRequestForSync(request) {
  // Get the request data
  const requestData = await request.clone().json();
  
  // Open IndexedDB
  const db = await openOfflineDB();
  
  // Add to outbox store
  const tx = db.transaction('outbox', 'readwrite');
  const store = tx.objectStore('outbox');
  
  await store.add({
    url: request.url,
    method: request.method,
    data: requestData,
    timestamp: Date.now()
  });
  
  // Request background sync if supported
  if ('SyncManager' in self) {
    await self.registration.sync.register('sync-outbox');
  }
}

// Open the offline database
function openOfflineDB() {
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

// Sync event - process stored requests when back online
self.addEventListener('sync', event => {
  if (event.tag === 'sync-outbox') {
    event.waitUntil(syncOutbox());
  }
});

// Sync the outbox store
async function syncOutbox() {
  try {
    const db = await openOfflineDB();
    const tx = db.transaction('outbox', 'readonly');
    const store = tx.objectStore('outbox');
    const requests = await store.getAll();
    
    for (const request of requests) {
      try {
        await fetch(request.url, {
          method: request.method,
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(request.data)
        });
        
        // If successful, delete from outbox
        const deleteTx = db.transaction('outbox', 'readwrite');
        const deleteStore = deleteTx.objectStore('outbox');
        await deleteStore.delete(request.timestamp);
      } catch (error) {
        console.error('Error syncing request:', error);
        // Keep in outbox for next sync attempt
      }
    }
    
    // Notify clients that sync is complete
    const clients = await self.clients.matchAll();
    for (const client of clients) {
      client.postMessage({
        type: 'sync-complete',
        count: requests.length
      });
    }
  } catch (error) {
    console.error('Error in syncOutbox:', error);
  }
}

// Cache current emergency assignment
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'cache-emergency') {
    caches.open(CACHE_NAME)
      .then(cache => {
        const response = new Response(
          JSON.stringify({
            success: true,
            has_assignment: true,
            emergency_call: event.data.emergency_call,
            offline: true,
            cached: Date.now()
          }),
          { headers: { 'Content-Type': 'application/json' } }
        );
        
        cache.put('/api/ambulance/cached-assignment', response);
      });
  }
});