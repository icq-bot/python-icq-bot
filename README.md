<img src="https://github.com/icq-bot/python-icq-bot/raw/master/logo.png" width="100" height="100">

# 🐍 python-icq-bot

[![](https://img.shields.io/pypi/v/python-icq-bot.svg)](https://pypi.org/project/python-icq-bot/)
[![](https://img.shields.io/pypi/pyversions/python-icq-bot.svg)](https://pypi.org/project/python-icq-bot/)

Pure Python interface for ICQ Bot API. Bot cookbook for Humans.

# Table of contents
- [Introduction](#introduction)
- [Getting started](#getting-started)
- [Installing](#installing)
- [Example](#example)
- [Starting your bot](#starting-your-bot)
- [Get in touch](#get-in-touch)

# Introduction

This library provides complete ICQ Bot API 1.0 interface and compatible with Python 2.7, 3.4, 3.5 and 3.6.

# Getting started

Create your own bot by sending the /newbot command to <a href="https://icq.com/people/70001">MegaBot</a> and follow the instructions.

Note a bot can only reply after the user has added it to his contact list, or if the user was the first to start a dialogue.

# Installing

Install using pip:
```bash
pip install --upgrade python-icq-bot
```

Install from sources:
```bash
git clone https://github.com/icq-bot/python-icq-bot.git
cd python-icq-bot
python setup.py install
```

# Example

See the project example directory.

Some ICQ bots you can play with right now:<br>
<a href="https://icq.com/742103765">Chat ID Bot</a> [<a href="https://github.com/icq-bot/python-icq-bot/blob/master/example/chat_id_bot.py">source code</a>]<br>
<a href="https://icq.com/725223851">Echo Bot</a> [<a href="https://github.com/icq-bot/python-icq-bot/blob/master/example/echo_bot.py">source code</a>]<br>
<a href="https://icq.com/729805850">Giphy Bot</a> [<a href="https://github.com/icq-bot/python-icq-bot/blob/master/example/giphy_bot.py">source code</a>]<br>
<a href="https://icq.com/720507564">Hash Bot</a> [<a href="https://github.com/icq-bot/python-icq-bot/blob/master/example/hash_bot.py">source code</a>]<br>
<a href="https://icq.com/70003">Meme Bot</a><br>
<a href="https://icq.com/721765058">OAuth Bot</a> [<a href="https://github.com/icq-bot/python-icq-bot/blob/master/example/oauth_bot.py">source code</a>]<br>
<a href="https://icq.com/720020179">Reformat Bot</a> [<a href="https://github.com/icq-bot/python-icq-bot/blob/master/example/reformat_bot.py">source code</a>]<br>
<a href="https://icq.com/100500">Stickers Bot</a><br>
<a href="https://icq.com/728777874">URL Decode Bot</a> [<a href="https://github.com/icq-bot/python-icq-bot/blob/master/example/urldecode_bot.py">source code</a>]<br>
<a href="https://icq.com/724894572">URL Encode Bot</a> [<a href="https://github.com/icq-bot/python-icq-bot/blob/master/example/urlencode_bot.py">source code</a>]<br>
<a href="https://icq.com/720953874">Vinci Bot</a><br>
<a href="https://icq.com/729775354">WolframAlpha Bot</a> [<a href="https://github.com/icq-bot/python-icq-bot/blob/master/example/wolframalpha_bot.py">source code</a>]<br>

# Starting your bot

Without Virtualenv:
```bash
python my_bot.py
```

Using Virtualenv:
```bash
# Initializing Virtualenv.
virtualenv venv

# Activating Virtualenv.
source venv/bin/activate

# Installing python-icq-bot library into local venv directory.
pip install --upgrade python-icq-bot

# Starting your bot.
python my_bot.py

# Deactivating virtualenv.
deactivate
```

# Get in touch

<a href="https://icq.com/chat/python-icq-bot">python-icq-bot channel</a>