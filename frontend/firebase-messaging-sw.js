// Firebase Cloud Messaging Service Worker
// This runs in the background and handles push notifications when the page is closed

// Import Firebase scripts for Service Worker environment
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-messaging-compat.js');

// Firebase Configuration (Same as your main app)
const firebaseConfig = {
    apiKey: "AIzaSyC9BD1eVJkmzUL2fgwnBZNT9ufLDq_MiNI",
    authDomain: "medication-reminder-e87a4.firebaseapp.com",
    projectId: "medication-reminder-e87a4",
    storageBucket: "medication-reminder-e87a4.firebasestorage.app",
    messagingSenderId: "520153865045",
    appId: "1:520153865045:web:b23af841554f088c58addc",
    measurementId: "G-HDR04VFTWP"
};

// Initialize Firebase in Service Worker
firebase.initializeApp(firebaseConfig);

// Get Messaging instance
const messaging = firebase.messaging();

// BACKGROUND MESSAGE HANDLER
// This fires when a push notification arrives while the app is in the background
messaging.onBackgroundMessage((payload) => {
    console.log('[firebase-messaging-sw.js] Received background message:', payload);

    // Normalize notification payload (prefer data payload for reliability)
    const data = payload.data || {};
    const notificationTitle = data.title || payload.notification?.title || 'Medication Reminder';
    const notificationOptions = {
        body: data.body || payload.notification?.body || 'Time to take your medication',
        icon: data.icon || '/favicon.ico',  // You can replace with your app icon
        badge: data.badge || '/favicon.ico',    // Small icon shown in notification tray
        tag: `med-reminder-${data.reminder_id}`, // Groups notifications with same tag
        renotify: true, // Add this to ensure the phone vibrates again for the new one
        requireInteraction: true,   // Notification stays until user interacts
        data: {
            ...data,
            medication_id: data.medication_id,
            reminder_id: data.reminder_id,
        },
        vibrate: [200, 100, 200],   // Vibration pattern (mobile)
        actions: [
            {
                action: 'mark-taken',
                title: '✅ Mark as Taken'
            },
            {
                action: 'snooze',
                title: '⏰ Snooze'
            }
        ]
    };

    // Show the notification
    return self.registration.showNotification(notificationTitle, notificationOptions);
});


// NOTIFICATION CLICK HANDLER
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    const action = event.action;
    const data = event.notification.data;
    const baseUrl = self.location.origin;
    let targetUrl = `${baseUrl}/google-test.html`;

    if (action && data.reminder_id) {
        targetUrl += `?id=${data.reminder_id}&action=${action}`;
    }

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(windowClients => {
            // 1. Check if app is already open
            for (let client of windowClients) {
                if (client.url.includes('google-test.html') && 'focus' in client) {
                    // If open, focus it and navigate to the new URL
                    return client.focus().then(c => c.navigate(targetUrl));
                }
            }
            // 2. If not open, open a new window
            return clients.openWindow(targetUrl);
        })
    );
});