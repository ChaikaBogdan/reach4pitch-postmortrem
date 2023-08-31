from enum import Enum

SUBSCRIBERS_GROUP_NAME = "Subscribers"
PITCH_CHANGES_REQUESTED = "Request Changes"
TRUE_VALUES = frozenset(("1", "t", "on", "y", "true", "yes"))
TINY_MCE_ATTRS = (
    ("cols", 80),
    ("rows", 30),
)
PITCH_EXTERNAL_LINKS_INITIAL = (
    "Demo",
    "Gameplay",
    "Website",
)


class PitchReviewStatus(str, Enum):
    DRAFT = "Draft"
    ON_REVIEW = "On review"
    REVIEWED = "Reviewed"
