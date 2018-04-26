# python-icq-bot

Pure Python interface for ICQ Bot API. Bot cookbook for Humans.

# Installing

```bash
git clone git@github.com:icq-bot/python-icq-bot.git
cd python-icq-bot
python setup.py install
```

# Getting started

Create your bot by sending /newbot command to MegaBot https://icq.com/people/70001 and follow instructions.

# Examples

See example directory.

## Starting your bot

Without virtualenv:
```bash
python test_bot.py
```

With virtualenv:
```bash
( { [ ! -d venv ] && virtualenv venv; } || true && source venv/bin/activate && pip install -r requirements.txt && pip install -r example/requirements.txt && cd example && PYTHONPATH='..' python test_bot.py && deactivate )
```

# News

ICQ channel: https://icq.com/chat/python-icq-bot