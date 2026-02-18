import enum


class LogAction(str, enum.Enum):
    TAKEN = "taken"
    SKIPPED = "skipped"
    MISSED = "missed"

class LogSource(str, enum.Enum):
    MANUAL = "manual"
    NOTIFICATION = "notification"
    WEARABLE = "wearable"
    IMPORT = "import"
    API = "api"