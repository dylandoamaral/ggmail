# GGmail

[![GGmail Continuous Integration](https://github.com/dylandoamaral/ggmail/actions/workflows/ci.yml/badge.svg)](https://github.com/dylandoamaral/ggmail/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/dylandoamaral/ggmail/branch/main/graph/badge.svg?token=KY5JTQWZLF)](https://codecov.io/gh/dylandoamaral/ggmail)
[![PyPI version](https://badge.fury.io/py/ggmail.svg)](https://badge.fury.io/py/ggmail)
[![downloads](https://pepy.tech/badge/ggmail/month)](https://pepy.tech/project/ggmail)
[![versions](https://img.shields.io/pypi/pyversions/ggmail.svg)](https://github.com/dylandoamaral/ggmail)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Manage mail account using python, forget about imap and just code what you supposed to do.

## Help

See [documentation](https://github.com/dylandoamaral/ggmail/wiki) for more details.

## Install

Install using `pip install ggmail`.

## A Simple Example

```python
from ggmail import Account, Google
from ggmail.policy import from_contains, flagged

authentication = Google(username="ggmail@gmail.com", password="secret")
with Account(authentication=authentication) as account:
    inbox = account.inbox()
    mailbox = account.create_mailbox("Favorite")
    policy = from_contains("from@gmail.com") + flagged
    messages = inbox.search(policy)

    for message in messages:
        message.copy(mailbox)
```

## Additional Information

### Why not use imbox instead ?

https://github.com/martinrusev/imbox is less high level than ggmail. I wanted something even more human than imbox.

### Why not use gmail instead ?

https://github.com/charlierguo/gmail seems to be dead.

## You don't support my mail provider ?

You can raise an issue and I will add it.
