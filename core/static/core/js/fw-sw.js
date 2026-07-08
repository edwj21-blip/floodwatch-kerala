/*
 * FloodWatch Kerala — Service Worker
 * Handles background push notifications so users get alerts
 * even when the browser tab is closed / in background.
 *
 * Served via /fw-sw.js (mapped in urls.py to this static file).
 */

const CACHE_NAME = 'floodwatch-v1';
const POLL_INTERVAL_MS = 1500000; // 25 minutes — alert popup throttle interval

// ── Install ──────────────────────────────────────────────────────────────────
self.addEventListener('install', event => {
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(self.clients.claim());
});

// ── Background Sync / Periodic Check ─────────────────────────────────────────
// When the page sends a message to start polling, we store the state.
let lastAlertLevel = null;
let lastAlertIds   = new Set();

async function checkAlerts() {
    try {
        const res  = await fetch('/api/public-alerts/?sw=1');
        const data = await res.json();

        if (!data.alert_level) {
            lastAlertLevel = null;
            lastAlertIds.clear();
            return;
        }

        // Collect IDs of current alerts
        const allAlerts = [...data.extreme_alerts, ...data.high_alerts];
        const newIds    = allAlerts.map(a => a.id);
        const hasNew    = newIds.some(id => !lastAlertIds.has(id));

        if (hasNew || data.alert_level !== lastAlertLevel) {
            lastAlertLevel = data.alert_level;
            lastAlertIds   = new Set(newIds);

            const isExtreme  = data.alert_level === 'EXTREME';
            const topAlert   = allAlerts[0];

            // Show OS-level notification
            await self.registration.showNotification(
                isExtreme ? '🔴 RED ALERT — FloodWatch Kerala' : '🟠 ORANGE ALERT — FloodWatch Kerala',
                {
                    body:    topAlert
                             ? `${topAlert.title} — ${topAlert.affected_area}, ${topAlert.district}`
                             : (isExtreme ? 'Extreme flood danger. Take immediate action.' : 'High flood risk in your area.'),
                    icon:    '/static/core/img/fw-icon-192.png',
                    badge:   '/static/core/img/fw-badge-72.png',
                    tag:     'floodwatch-alert',          // replaces old notification
                    renotify: true,
                    vibrate: isExtreme ? [500,200,500,200,500] : [300,150,300],
                    data:    { url: '/alerts/' },
                    actions: [
                        { action: 'view',    title: '🔍 View Alerts' },
                        { action: 'dismiss', title: 'Dismiss'        },
                    ],
                    requireInteraction: isExtreme,        // stays until dismissed for EXTREME
                }
            );

            // Also tell any open tabs to show the popup + play sound
            const clients = await self.clients.matchAll({ type: 'window' });
            clients.forEach(client => {
                client.postMessage({
                    type:        'FW_ALERT',
                    alert_level: data.alert_level,
                    alerts:      data,
                });
            });
        }
    } catch (e) {
        // Network error — silently ignore
    }
}

// ── Notification click ────────────────────────────────────────────────────────
self.addEventListener('notificationclick', event => {
    event.notification.close();
    if (event.action === 'dismiss') return;
    event.waitUntil(
        self.clients.matchAll({ type: 'window' }).then(clients => {
            // Focus existing tab or open new one
            const existing = clients.find(c => c.url.includes(self.location.origin));
            if (existing) { existing.focus(); existing.navigate('/alerts/'); }
            else self.clients.openWindow('/alerts/');
        })
    );
});

// ── Message from page: start/stop polling ────────────────────────────────────
let pollTimer = null;
self.addEventListener('message', event => {
    if (event.data?.type === 'FW_START_POLL') {
        if (pollTimer) return; // already running
        checkAlerts(); // immediate check
        pollTimer = setInterval(checkAlerts, POLL_INTERVAL_MS);
    }
    if (event.data?.type === 'FW_STOP_POLL') {
        clearInterval(pollTimer);
        pollTimer = null;
    }
});
