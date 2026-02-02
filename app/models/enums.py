import enum


class PlatformType(enum.Enum):
    DISCORD = "discord"
    TELEGRAM = "telegram"


class NotificationDirection(enum.Enum):
    ABOVE = "above"
    BELOW = "below"
