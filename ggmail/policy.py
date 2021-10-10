from abc import ABC, abstractmethod
from datetime import date, datetime

from pydantic import BaseModel

from .flag import Flag


class Policy(ABC, BaseModel):
    @abstractmethod
    def to_imap_standard(self) -> str:
        """"""

    def __add__(self, other: "Policy"):
        return And(left=self, right=other)

    def __iadd__(self, other: "Policy"):
        return And(left=self, right=other)

    def __or__(self, other: "Policy"):
        return Or(left=self, right=other)

    def __invert__(self):
        return Not(policy=self)


class Not(Policy):
    policy: Policy

    def to_imap_standard(self):
        return f"NOT {self.policy.to_imap_standard()}"


class And(Policy):
    left: Policy
    right: Policy

    def to_imap_standard(self):
        return f"{self.left.to_imap_standard()} {self.right.to_imap_standard()}"


class Or(Policy):
    left: Policy
    right: Policy

    def to_imap_standard(self):
        return f"OR {self.left.to_imap_standard()} {self.right.to_imap_standard()}"


class Intrinsic(Policy):
    intrinsic: str

    def to_imap_standard(self):
        return self.intrinsic


class OneString(Policy):
    intrinsic: str
    value: str

    def to_imap_standard(self):
        return f"{self.intrinsic} {self.value}"


class OneInteger(Policy):
    intrinsic: str
    value: int

    def to_imap_standard(self):
        return f"{self.intrinsic} {self.value}"


class OneDate(Policy):
    intrinsic: str
    date: date

    def to_imap_standard(self):
        date_time = datetime(self.date.year, self.date.month, self.date.day)
        date_format = "%d-%b-%Y"
        return f"{self.intrinsic} {date_time.strftime(date_format)}"


class OneFlag(Policy):
    intrinsic: str
    flag: Flag

    def to_imap_standard(self):
        return f"{self.intrinsic} {self.flag.value}"


# TODO field_name should be an enum
class Header(Policy):
    field_name: str
    value: str

    def to_imap_standard(self):
        return f"HEADER {self.field_name} {self.value}"


all_ = Intrinsic(intrinsic="ALL")
answered = Intrinsic(intrinsic="ANSWERED")
deleted = Intrinsic(intrinsic="DELETED")
draft = Intrinsic(intrinsic="DRAFT")
flagged = Intrinsic(intrinsic="FLAGGED")
new = Intrinsic(intrinsic="NEW")
old = Intrinsic(intrinsic="OLD")
recent = Intrinsic(intrinsic="RECENT")
seen = Intrinsic(intrinsic="SEEN")
unanswered = Intrinsic(intrinsic="UNANSWERED")
undeleted = Intrinsic(intrinsic="UNDELETED")
undraft = Intrinsic(intrinsic="UNDRAFT")
unflagged = Intrinsic(intrinsic="UNFLAGGED")
unseen = Intrinsic(intrinsic="UNSEEN")

bcc_contains = lambda content: OneString(intrinsic="BCC", value=content)
body_contains = lambda content: OneString(intrinsic="BODY", value=content)
cc_contains = lambda content: OneString(intrinsic="CC", value=content)
from_contains = lambda content: OneString(intrinsic="FROM", value=content)
subject_contains = lambda content: OneString(intrinsic="SUBJECT", value=content)
text_contains = lambda content: OneString(intrinsic="TEXT", value=content)
to_contains = lambda content: OneString(intrinsic="TO", value=content)
uid = lambda content: OneString(intrinsic="UID", value=content)

larger_than = lambda size: OneInteger(intrinsic="LARGER", value=size)
smaller_than = lambda size: OneInteger(intrinsic="SMALLER", value=size)

before = lambda date: OneDate(intrinsic="BEFORE", date=date)
on = lambda date: OneDate(intrinsic="ON", date=date)
sent_before = lambda date: OneDate(intrinsic="SENTBEFORE", date=date)
sent_on = lambda date: OneDate(intrinsic="SENTON", date=date)
sent_since = lambda date: OneDate(intrinsic="SENTSINCE", date=date)
since = lambda date: OneDate(intrinsic="SINCE", date=date)

header = lambda field_name, value: Header(field_name=field_name, value=value)
keyword = lambda flag: OneFlag(intrinsic="KEYWORD", flag=flag)
unkeyword = lambda flag: OneFlag(intrinsic="UNKEYWORD", flag=flag)
