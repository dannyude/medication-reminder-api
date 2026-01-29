// frontend/firebase-messaging-sw.js
importScripts('https://www.gstatic.com/firebasejs/12.8.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/12.8.0/firebase-messaging-compat.js');

firebase.initializeApp({
    apiKey: "AIzaSyC9BD1eVJkmzUL2fgwnBZNT9ufLDq_MiNI",
    authDomain: "medication-reminder-e87a4.firebaseapp.com",
    projectId: "medication-reminder-e87a4",
    storageBucket: "medication-reminder-e87a4.firebasestorage.app",
    messagingSenderId: "520153865045",
    appId: "1:520153865045:web:b23af841554f088c58addc",
    measurementId: "G-HDR04VFTWP"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage(function(payload) {
  console.log('Received background message ', payload);

  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: 'https://cdn-icons-png.flaticon.com/512/2966/2966327.png'
  };

  return self.registration.showNotification(notificationTitle, notificationOptions);
});