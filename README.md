# GGmail

[![GGmail Continuous Integration](https://github.com/dylandoamaral/ggmail/actions/workflows/ci.yml/badge.svg)](https://github.com/dylandoamaral/ggmail/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/dylandoamaral/ggmail/branch/main/graph/badge.svg?token=KY5JTQWZLF)](https://codecov.io/gh/dylandoamaral/ggmail)

Manage gmail account using python, forget about imap and just code what you supposed to do.

## Help

See [documentation](https://github.com/dylandoamaral/ggmail/wiki) for more details.

## Install

Install using `pip install ggmail`.

## A Simple Example

```python
from ggmail import Account
from ggmail.policy import from_contains, flagged

account = Account(username="ggmail@gmail.com", password="secret")
with account:
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