import pytest

from ggmail.policy import all_, from_, larger_than, smaller_than, to


class TestPolicy:
    @pytest.mark.parametrize(
        "policy,result",
        [
            pytest.param(all_, "ALL", id="all"),
            pytest.param(from_("test@gmail.com"), "FROM test@gmail.com", id="from"),
            pytest.param(to("test@gmail.com"), "TO test@gmail.com", id="to"),
            pytest.param(smaller_than(3), "SMALLER 3", id="smaller than"),
            pytest.param(~all_, "NOT ALL", id="not"),
            pytest.param(
                from_("test@gmail.com") + to("test2@gmail.com"),
                "AND FROM test@gmail.com TO test2@gmail.com",
                id="and",
            ),
            pytest.param(
                from_("test@gmail.com") | to("test2@gmail.com"),
                "OR FROM test@gmail.com TO test2@gmail.com",
                id="or",
            ),
        ],
    )
    def test_policies(self, policy, result):
        assert policy.to_imap_standard() == result
