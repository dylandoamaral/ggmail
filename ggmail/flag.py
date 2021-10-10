from enum import Enum


class Flag(Enum):
    ANSWERED = "\\Answered"
    DELETED = "\\Deleted"
    DRAFT = "\\Draft"
    FLAGGED = "\\Flagged"
    SEEN = "\\Seen"
