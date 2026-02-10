import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from api.src.reminders.tasks import check_and_send_pending_reminders

# Import all models to ensure SQLAlchemy can resolve relationships.
from api.src.auth.models import RefreshToken
from api.src.logs.models import MedicationLog
from api.src.medications.models import Medication
from api.src.reminders.models import Reminder
from api.src.users.models import User

# Configure application logging for the scheduler process.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("MediScheduler")

def run_scheduler():
    # Initialize an asyncio-based scheduler.
    scheduler = AsyncIOScheduler()

    # Schedule the reminder task to run every minute.
    scheduler.add_job(check_and_send_pending_reminders, 'interval', minutes=1)

    # Start the scheduler and report status.
    scheduler.start()
    logger.info("🚀 Dedicated Scheduler Service Started! Waiting for tasks...")

    # Keep the event loop running so scheduled jobs can execute.
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        # Graceful shutdown on termination signals.
        logger.info("🛑 Scheduler shutting down...")


if __name__ == "__main__":
    run_scheduler()