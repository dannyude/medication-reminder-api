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

    // Extract notification data
    const notificationTitle = payload.notification?.title || 'Medication Reminder';
    const notificationOptions = {
        body: payload.notification?.body || 'Time to take your medication',
        icon: '/favicon.ico',  // You can replace with your app icon
        badge: '/badge.png',    // Small icon shown in notification tray
        tag: 'medication-reminder', // Groups notifications with same tag
        requireInteraction: true,   // Notification stays until user interacts
        data: payload.data,         // Custom data you can access on click
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
// This fires when user clicks on the notification
self.addEventListener('notificationclick', (event) => {
    console.log('[firebase-messaging-sw.js] Notification click received:', event);

    event.notification.close(); // Close the notification

    const action = event.action;
    const reminderData = event.notification.data;

    if (action === 'mark-taken') {
        // Open app and mark medication as taken
        event.waitUntil(
            clients.openWindow(`/reminders/${reminderData.reminder_id}?action=taken`)
        );
    } else if (action === 'snooze') {
        // Open app and snooze reminder
        event.waitUntil(
            clients.openWindow(`/reminders/${reminderData.reminder_id}?action=snooze`)
        );
    } else {
        // Default: just open the app
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// SERVICE WORKER LIFECYCLE
self.addEventListener('install', (event) => {
    console.log('[firebase-messaging-sw.js] Service Worker installed');
    self.skipWaiting(); // Activate immediately
});

self.addEventListener('activate', (event) => {
    console.log('[firebase-messaging-sw.js] Service Worker activated');
    event.waitUntil(clients.claim()); // Take control of all pages
});