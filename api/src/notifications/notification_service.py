import os
import asyncio

import logging
import httpx

import firebase_admin
from firebase_admin import credentials, messaging


from api.src.config import settings
from api.src.reminders.models import Reminder


logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
KEY_PATH = os.path.join(BASE_DIR, "serviceAccountKey.json")

if os.path.exists(KEY_PATH):
    cred = credentials.Certificate(KEY_PATH)
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(cred)
    logger.info("✅ Firebase Admin Initialized.")
else:
    logger.warning("⚠️ Service Account Key NOT found at: %s", KEY_PATH)
    logger.warning("   -> Push notifications will NOT work until you add this file.")


class NotificationService:
    @staticmethod
    async def send_reminder_notification(reminder: Reminder, session) -> bool:
        """
        Send medication reminder notification.
        Tries SMS first, then push notification as fallback.
        Assumes reminder.user and reminder.medication are ALREADY loaded.
        """
        user = reminder.user
        medication = reminder.medication

        # If data is missing
        if not user or not medication:
            logger.error("❌ Data missing for reminder: %s", reminder.id)
            return False

        # Create message
        message = (
            f"🏥 Medi Reminder: Time to take {medication.name} ({medication.dosage}). "
            f"Stay healthy!"
        )

        sent_success = False

        # Attempt push notification first
        if user.fcm_token:
            sent_successfully = await NotificationService.send_push_notification(
                token=user.fcm_token,
                title="💊 Medication Reminder",
                body=f"Time to take {medication.name}",
                data={
                    "type": "medication_reminder",
                    "reminder_id": str(reminder.id)
                }
            )

            if sent_successfully:
                logger.info("✅ Push Notification sent to User %s", user.id)
                return True
            # Exit early if successful

        # else for fallback to SMS
        logger.info("⚠️ Push Notification failed or token missing. Trying SMS for User %s...", user.id)
        if user.mobile_number:
            sent_success = await NotificationService.send_sms(
                user.mobile_number,
                message
            )
            if sent_success:
                logger.info("✅ SMS sent to %s", user.mobile_number)
                return True
            # Exit early if successful
        else:
            logger.error("❌ No mobile number for User %s, cannot send SMS.", user.id)

        return False


    @staticmethod
    async def send_push_notification(token: str, title: str, body: str, data: dict) -> bool:
        """
        Sends Push Notification without blocking the main event loop.
        """
        try:
            # Create the message payload
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data,
                token=token,
            )

            # pawns off blocking call to a separate thread
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: messaging.send(message)
            )

            logger.info("📲 Firebase success ID: %s", response)
            return True
        except Exception as e:
            logger.error("❌ Firebase Push Failed: %s", e)
            return False


    @staticmethod
    async def send_sms(phone_number: str, message: str) -> bool:
        """
        Sends SMS via Africa's Talking API (Async).
        SAFE VERSION: Handles empty recipient lists without crashing.
        """
        api_key = settings.AT_API_KEY
        username = settings.AT_USERNAME
        sender_id = settings.AT_SENDER_ID
        env = settings.AT_ENV

        if not api_key or not username:
            logger.error("❌ Africa's Talking API Key or Username not set.")
            return False

        # Determine URL
        if env == "production":
            url = "https://api.africastalking.com/version1/messaging"
        else:
            url = "https://api.sandbox.africastalking.com/version1/messaging"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "apiKey": api_key
        }

        payload = {
            "username": username,
            "to": phone_number,
            "message": message
        }
        if env == "production" and sender_id:
            payload["from"] = sender_id

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, data=payload, headers=headers)
                # if not 201, something went wrong
                if response.status_code != 201:
                    logger.error("❌ AT SMS Failed (%s): %s", response.status_code, response.text)
                    return False

                data = response.json()
                recipients = data.get("SMSMessageData", {}).get("Recipients", [])


                # Case A: List is empty (e.g., Bad number, Sandbox restriction)
                if not recipients:
                    logger.error("❌ AT accepted request but returned NO recipients. Raw msg: %s", data)
                    return False

                # Case B: We have a recipient, let's check status
                first_recipient = recipients[0]
                status = first_recipient.get("status")

                if status == "Success":
                    logger.info("✅ AT SMS Sent: %s", first_recipient.get("messageId"))
                    return True
                else:
                    logger.warning("⚠️ AT SMS Status: %s (Cost: %s)", status, first_recipient.get("cost"))
                    # We return True here to stop retrying indefinitely if it's a permanent failure
                    return True

            except Exception as e:
                logger.error("❌ AT Unexpected Error: %s", e)
                return False
