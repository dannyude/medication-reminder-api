import firebase_admin
from firebase_admin import credentials, initialize_app
import os
import logging

logger = logging.getLogger(__name__)

def initialize_firebase():
    """
    Initializes the Firebase Admin SDK.
    """
    try:
        #  Check if already initialized
        firebase_admin.get_app()
        logger.info("✅ Firebase is already initialized. Skipping.")
        return
    except ValueError:
        # ValueError means "No app exists", so we proceed to initialize!
        pass

    try:
        # Define the two possible paths
        render_secret_path = "/etc/secrets/serviceAccountKey.json"
        local_secret_path = "serviceAccountKey.json"

        # Determine which file to use
        if os.path.exists(render_secret_path):
            logger.info(f"✅ Found Render secret at: {render_secret_path}")
            cred = credentials.Certificate(render_secret_path)
        elif os.path.exists(local_secret_path):
            logger.info(f"⚠️ Using local key at: {local_secret_path}")
            cred = credentials.Certificate(local_secret_path)
        else:
            # If neither exists, we cannot start
            logger.error(f"❌ CRITICAL: No serviceAccountKey.json found! Checked: {render_secret_path} and {local_secret_path}")
            return

        # 3. Initialize the app
        initialize_app(cred)
        logger.info("✅ Firebase initialized successfully!")

    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase: {str(e)}")