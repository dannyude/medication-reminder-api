import enum
class FrequencyType(str, enum.Enum):
    """How often the medication should be taken."""
    ONCE_DAILY = "once_daily"
    TWICE_DAILY = "twice_daily"
    THREE_TIMES_DAILY = "three_times_daily"
    FOUR_TIMES_DAILY = "four_times_daily"
    EVERY_X_HOURS = "every_x_hours"
    AS_NEEDED = "as_needed"
    CUSTOM = "custom"


class MedicationForm(str, enum.Enum):
    """Form of the medication."""
    TABLET = "tablet"
    CAPSULE = "capsule"
    LIQUID = "liquid"
    INJECTION = "injection"
    CREAM = "cream"
    DROPS = "drops"
    INHALER = "inhaler"
    TOPICAL = "topical"
    PATCH = "patch"
    OTHER = "other"


class ReminderStatus(str, enum.Enum):
    """State of a scheduled reminder."""
    PENDING = "pending"
    SENT = "sent"
    TAKEN = "taken"
    MISSED = "missed"
    SKIPPED = "skipped"