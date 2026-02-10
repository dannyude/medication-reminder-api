import firebase_admin
from firebase_admin import credentials
import os
import logging


logger = logging.getLogger(__name__)

def initialize_firebase():
    """
    Initializes the Firebase Admin SDK.
    Should be called once when the FastAPI app starts.
    """
    try:
        # Check if Firebase is already running (to prevent double-init errors)
        firebase_admin.get_app()
        logger.info("✅ Firebase is already initialized. Skipping.")
        return

    except ValueError:
        # ValueError means "No app exists", so we are safe to initialize!
        pass

        # Path to service account key for Firebase
        base_dir = os.getcwd()
        key_path = os.path.join(base_dir, "serviceAccountKey.json")

        if not os.path.exists(key_path):
            logger.error("❌ CRITICAL: Firebase key not found at: %s", key_path)
            return

        try:
            # Load the credentials and start the app
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
            logger.info("✅ Firebase initialized successfully!")

        except Exception as e:
            logger.error("❌ Failed to initialize Firebase: %s", str(e))