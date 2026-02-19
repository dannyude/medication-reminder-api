// Firebase Cloud Messaging Service Worker
// This runs in the background and handles push notifications when the page is closed

// 1. IMPORT NECESSARY SCRIPTS (CRITICAL FIX: Added Messaging)
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

// 2. FIREBASE CONFIGURATION
const firebaseConfig = {
    apiKey: "AIzaSyC9BD1eVJkmzUL2fgwnBZNT9ufLDq_MiNI",
    authDomain: "medication-reminder-e87a4.firebaseapp.com",
    projectId: "medication-reminder-e87a4",
    storageBucket: "medication-reminder-e87a4.firebasestorage.app",
    messagingSenderId: "520153865045",
    appId: "1:520153865045:web:b23af841554f088c58addc",
    measurementId: "G-HDR04VFTWP"
};

// 3. INITIALIZATION
firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

// 4. INSTALL & ACTIVATE LISTENERS (CRITICAL FIX: Forces update)
// Skip waiting ensures the new worker takes over as soon as it's registered
self.addEventListener('install', () => self.skipWaiting());

// Claim ensures that the worker starts controlling the page immediately
self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
    console.log('[SW] Service Worker Activated and Claimed');
});

// 5. BACKGROUND MESSAGE HANDLER
messaging.onBackgroundMessage((payload) => {
    console.log('[firebase-messaging-sw.js] Received background message:', payload);

    const data = payload.data || {};
    const supportsActions = typeof Notification !== 'undefined' && Number.isInteger(Notification.maxActions) && Notification.maxActions > 0;
    const supportsRequireInteraction = typeof Notification !== 'undefined'
        && Notification.prototype
        && 'requireInteraction' in Notification.prototype;

    // Fallback logic for title/body
    const notificationTitle = data.title || payload.notification?.title || 'Medication Reminder';
    const notificationOptions = {
        body: data.body || payload.notification?.body || 'Time to take your medication',
        icon: data.icon || '/favicon.ico',
        badge: data.badge || '/favicon.ico',
        tag: data.reminder_id ? `med-reminder-${data.reminder_id}` : 'general-reminder',
        renotify: true,           // Vibrate again even if tag is the same
        vibrate: [200, 100, 200], // Haptic feedback for importance
        data: {
            ...data,
            url: '/google-test.html' // Default redirect
        },
        actions: supportsActions ? [
            {
                action: 'mark-taken',
                title: '✅ Mark as Taken'
            },
            {
                action: 'snooze',
                title: '⏰ Snooze'
            }
        ].slice(0, Notification.maxActions) : []
    };

    if (supportsRequireInteraction) {
        notificationOptions.requireInteraction = true;
    }

    return self.registration.showNotification(notificationTitle, notificationOptions);
});

// 6. NOTIFICATION CLICK HANDLER
self.addEventListener('notificationclick', (event) => {
    const action = event.action;
    const notification = event.notification;
    const data = notification && notification.data && typeof notification.data === 'object' ? notification.data : {};

    notification.close(); // Close the notification popup

    const baseUrl = self.location.origin;
    let targetUrl = `${baseUrl}${data.url || '/google-test.html'}`;

    // If an action was clicked (e.g., mark-taken), append to URL
    if (action && data.reminder_id) {
        targetUrl += `?id=${data.reminder_id}&action=${action}`;
    }

    event.waitUntil(
        self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(windowClients => {
            // Check if tab is already open
            for (let client of windowClients) {
                if (client.url.includes('google-test.html') && 'focus' in client) {
                    // Navigate existing tab and focus it
                    return client.focus().then(c => c.navigate(targetUrl));
                }
            }
            // If not open, open a new window
            if (self.clients.openWindow) {
                return self.clients.openWindow(targetUrl);
            }
        })
    );
});