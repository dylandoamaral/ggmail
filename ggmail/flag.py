from enum import Enum


class Flag(Enum):
    ANSWERED = "\\Answered"
    DELETED = "\\Deleted"
    DRAFT = "\\Draft"
    FLAGGED = "\\Flagged"
    SEEN = "\\Seen"
    BIT_0 = "$MailFlagBit0"
    BIT_1 = "$MailFlagBit1"
    BIT_2 = "$MailFlagBit2"
