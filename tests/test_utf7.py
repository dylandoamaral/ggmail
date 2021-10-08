from ggmail.utf7 import decode
import pytest
from pytest import raises
from ggmail.exception import WrongUTF7String


class TestUTF7Decode:
    @pytest.mark.parametrize(
        "encoded_message,decoded_message",
        [
            ("Messages envoy&AOk-s", "Messages envoyés"),
            ("Dog &- Cat", "Dog & Cat"),
        ],
    )
    def test_decode(self, encoded_message, decoded_message):
        assert decode(encoded_message) == decoded_message

    def test_decode_fail(self):
        with raises(WrongUTF7String):
            decode("Dog & Cat")