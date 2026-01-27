import enum


class LogAction(str, enum.Enum):
    TAKEN = "taken"
    SKIPPED = "skipped"
    MISSED = "missed"