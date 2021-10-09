from abc import ABC, abstractmethod

from pydantic import BaseModel


class Policy(ABC, BaseModel):
    @abstractmethod
    def to_imap_standard(self) -> str:
        """"""

    def __add__(self, other: "Policy"):
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
        return f"AND {self.left.to_imap_standard()} {self.right.to_imap_standard()}"


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


all_ = Intrinsic(intrinsic="ALL")
answered = Intrinsic(intrinsic="ANSWERED")
deleted = Intrinsic(intrinsic="DELETED")
draft = Intrinsic(intrinsic="DRAFT")
flagged = Intrinsic(intrinsic="FLAGGED")

body_contains = lambda content: OneString(intrinsic="BODY", value=content)
from_ = lambda sender: OneString(intrinsic="FROM", value=sender)
subject_contains = lambda content: OneString(intrinsic="SUBJECT", value=content)
to = lambda sender: OneString(intrinsic="TO", value=sender)

larger_than = lambda size: OneInteger(intrinsic="LARGER", value=size)
smaller_than = lambda size: OneInteger(intrinsic="SMALLER", value=size)
