

# Run dev
```sh
python -m venv venv
venv/bin/pip install -e .
TELEGRAM_BOT_TOKEN="YOURBOTTOKENHERE" venv/bin/python -m us-pres-elec-bot
```

# Run prod
```sh
python -m venv venv
venv/bin/pip install us-pres-elec-bot.whl
TELEGRAM_BOT_TOKEN="YOURBOTTOKENHERE" venv/bin/python -m us-pres-elec-bot
```