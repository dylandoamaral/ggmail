from datetime import date

import pytest

from ggmail.policy import (
    Flag,
    all_,
    before,
    from_contains,
    header,
    keyword,
    larger_than,
    smaller_than,
    to_contains,
    unseen,
)


class TestPolicy:
    @pytest.mark.parametrize(
        "policy,result",
        [
            pytest.param(all_, "ALL", id="all"),
            pytest.param(
                from_contains("test@gmail.com"), "FROM test@gmail.com", id="from"
            ),
            pytest.param(to_contains("test@gmail.com"), "TO test@gmail.com", id="to"),
            pytest.param(smaller_than(3), "SMALLER 3", id="smaller than"),
            pytest.param(before(date(2015, 10, 3)), "BEFORE 03-Oct-2015", id="before"),
            pytest.param(header("key", "value"), "HEADER key value", id="header"),
            pytest.param(keyword(Flag.ANSWERED), r"KEYWORD \Answered", id="keyword"),
            pytest.param(~all_, "NOT ALL", id="not"),
            pytest.param(
                from_contains("test@gmail.com") + to_contains("test2@gmail.com"),
                "FROM test@gmail.com TO test2@gmail.com",
                id="and",
            ),
            pytest.param(
                from_contains("test@gmail.com") | to_contains("test2@gmail.com"),
                "OR FROM test@gmail.com TO test2@gmail.com",
                id="or",
            ),
        ],
    )
    def test_policies(self, policy, result):
        assert policy.to_imap_standard() == result

    def test_iadd(self):
        policy = unseen
        policy += from_contains("test@gmail.com")
        assert policy.to_imap_standard() == "UNSEEN FROM test@gmail.com"
