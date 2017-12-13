# python-icq-bot

Pure Python interface for ICQ Bot API. Bot cookbook for Humans.

# Getting started

Create your bot by sending /newbot command to MegaBot https://icq.com/people/70001 and follow instructions.

# Examples

See example directory.

## Starting your bot

```bash
( { [ ! -d venv ] && virtualenv venv; } || true && source venv/bin/activate && pip install -r requirements.txt && cd example && PYTHONPATH='..' python test_bot.py && deactivate )
```

# News

ICQ channel: https://icq.com/chat/python-icq-bot