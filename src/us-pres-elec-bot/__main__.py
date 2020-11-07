
import os

from .bot import construct_bot
from .check import get_data


def main():

    updater = construct_bot(
        token=os.environ["TELEGRAM_BOT_TOKEN"],
        persistence_file='bot_persistence',
        poll_interval=60,
        api_func=get_data)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()