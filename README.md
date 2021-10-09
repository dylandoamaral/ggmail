# GGmail

Manage gmail account using python, forget about imap and just code what you supposed to do with gmail.

## Install

You can't install it yet, it is still work in progress.

## How it works

The best way to explain it is actually using an example:

```python
from ggmail import Account
from ggmail.policy import from_contains, flagged

with Account(username="account@gmail.com", password="secret") as account:
    inbox = account.inbox()
    policy = from_contains("do.amaral.dylan@gmail.com") + flagged
    messages = inbox.search(policy)
    print([message.subject for message in messages])
```

## Additional Information

### Why not use imbox instead ?

https://github.com/martinrusev/imbox is less high level than ggmail. I wanted something even more human that imbox.

### Why not use gmail instead ?

https://github.com/charlierguo/gmail seems to be dead.