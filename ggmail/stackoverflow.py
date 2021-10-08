import base64

# https://stackoverflow.com/questions/12776679/imap-folder-path-encoding-imap-utf-7-for-
# python


def b64padanddecode(b):
    """Decode unpadded base64 data"""
    b += (-len(b) % 4) * "="  # base64 padding (if adds '===', no valid padding anyway)
    return base64.b64decode(b, altchars="+,", validate=True).decode("utf-16-be")


def imaputf7decode(s):
    """
    Decode a string encoded according to RFC2060 aka IMAP UTF7.

    Minimal validation of input, only works with trusted data
    """
    lst = s.split("&")
    out = lst[0]
    for e in lst[1:]:
        u, a = e.split(
            "-", 1
        )  # u: utf16 between & and 1st -, a: ASCII chars folowing it
        if u == "":
            out += "&"
        else:
            out += b64padanddecode(u)
        out += a
    return out


def imaputf7encode(s):
    """Encode a string into RFC2060 aka IMAP UTF7"""
    s = s.replace("&", "&-")
    iters = iter(s)
    unipart = out = ""
    for c in s:
        if 0x20 <= ord(c) <= 0x7F:
            if unipart != "":
                out += (
                    "&"
                    + base64.b64encode(unipart.encode("utf-16-be"))
                    .decode("ascii")
                    .rstrip("=")
                    + "-"
                )
                unipart = ""
            out += c
        else:
            unipart += c
    if unipart != "":
        out += (
            "&"
            + base64.b64encode(unipart.encode("utf-16-be")).decode("ascii").rstrip("=")
            + "-"
        )
    return out
