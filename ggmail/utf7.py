import base64

from .exception import WrongUTF7String

# https://stackoverflow.com/questions/12776679/imap-folder-path-encoding-imap-utf-7-for-
# python


def unpadded_b64_decode(b: bytes):
    """Decode unpadded base64 data"""
    b += (-len(b) % 4) * "="  # base64 padding (if adds '===', no valid padding anyway)
    return base64.b64decode(b, altchars="+,", validate=True).decode("utf-16-be")


def decode(s: str) -> str:
    """
    Decode a string encoded according to RFC2060 aka IMAP UTF7.

    Minimal validation of input, only works with trusted data

    :param s: The string to decode
    :return: The decoded string
    """
    lst = s.split("&")
    out = lst[0]
    for e in lst[1:]:
        try:
            u, a = e.split("-", 1)
        except ValueError:
            raise WrongUTF7String(f"The string {s} can't be decoded using utf7")
        if u == "":
            out += "&"
        else:
            out += unpadded_b64_decode(u)
        out += a
    return out
