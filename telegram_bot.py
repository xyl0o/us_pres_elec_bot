import logging
import os

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, PicklePersistence

from check import parse_data, get_data, textify_change, filter_states
from states import states_dict

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

battlegrounds = {
    # 'Alaska',
    # 'Michigan',
    # 'Wisconsin',
    'Arizona',
    'Georgia',
    'Nevada',
    'North Carolina',
    'Pennsylvania',
}

candidates = ['Joe Biden', 'Donald Trump']


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(f"""
Hey there!

Use /subscribe to get vote updates.
Use /unsubscribe to stop me from texting you.
Use /states to get a list of all states.
Use /state <state> to get current state votes.
Use /info <state> to get current state votes.
Use /info to get current state votes of your watchlist.
Use /watch <state> to add a state to your watchlist.
Use /unwatch <state> to unwatch a state.
""")


def _check(api_data, user_data):
    if not (old := user_data.get('old')):
        user_data['old'] = api_data
        return False

    for state in filter_states(old, api_data, user_data['watchlist']):
        yield textify_change(
            state=state, old=old[state], new=api_data[state], candidates=candidates)

        old[state] = api_data[state]
    else:
        return False # loop never ran

    user_data['old'] = old

    return True


def _select_state(txt):
    if (txt_upper := txt.upper()) in states_dict.keys():
        return states_dict[txt_upper]

    if txt in states_dict.values():
        return txt

    return


def _get_user_data(chat_id, bot_data):

    if chat_id not in bot_data['chats']:
        bot_data['chats'][chat_id] = {}

    user_data = bot_data['chats'][chat_id]

    if 'watchlist' not in user_data:
        user_data['watchlist'] = battlegrounds

    return user_data


def info(update: Update, context: CallbackContext) -> None:
    """Allow the user to cancel the updates"""
    chat_id = update.message.chat_id
    user_data = _get_user_data(chat_id, context.bot_data)

    if len(context.args) == 0:
        states = user_data['watchlist']

        if not states:
            update.message.reply_text(f"You aren't watching any states")
            return
    else:
        if not (state := _select_state(context.args[0])):
            update.message.reply_text(f'Unknown state {raw_state}')
            return
        states = {state}

    new = parse_data(get_data())

    txt = "\n\n".join(
        textify_change(state=s, new=new[s], candidates=candidates)
        for s in states)

    if txt:
        update.message.reply_text(txt)


def watch(update: Update, context: CallbackContext) -> None:
    """Allow the user to cancel the updates"""
    chat_id = update.message.chat_id
    user_data = _get_user_data(chat_id, context.bot_data)

    try:
        raw_state = str(context.args[0])
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /watch <state>')
        return

    if not (state := _select_state(raw_state)):
        update.message.reply_text(f'Unknown state {raw_state}')
        return

    update.message.reply_text(f"I've added {state} to your watchlist.")

    user_data['watchlist'] |= {state}


def unwatch(update: Update, context: CallbackContext) -> None:
    """Allow the user to cancel the updates"""
    chat_id = update.message.chat_id
    user_data = _get_user_data(chat_id, context.bot_data)

    try:
        raw_state = context.args[0]
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /unwatch <state>')
        return

    if not (state := _select_state(raw_state)):
        update.message.reply_text(f'Unknown state {raw_state}')
        return

    update.message.reply_text(f"I've removed {state} from your watchlist.")

    user_data['watchlist'] -= {state}


def states(update: Update, context: CallbackContext) -> None:
    """Allow the user to cancel the updates"""
    chat_id = update.message.chat_id
    user_data = _get_user_data(chat_id, context.bot_data)

    txt = 'I know of the following states:\n'
    for k, v in states_dict.items():
        txt += f'{v} ({k})'
        if v in user_data['watchlist']:
            txt += ' - watching'
        txt += '\n'

    update.message.reply_text(txt)


def subscribe(update: Update, context: CallbackContext) -> None:
    """Allow the user to cancel the updates"""
    chat_id = update.message.chat_id
    user_data = _get_user_data(chat_id, context.bot_data)
    context.bot_data['subscribers'] |= {chat_id}

    update.message.reply_text(f"I will message you when new votes come in.")


def unsubscribe(update: Update, context: CallbackContext) -> None:
    """Allow the user to cancel the updates"""
    chat_id = update.message.chat_id
    user_data = _get_user_data(chat_id, context.bot_data)
    context.bot_data['subscribers'] -= {chat_id}

    update.message.reply_text(f"I won't bother you with updates anymore.")


def poll_api(context):
    api_data = parse_data(get_data())

    for chat_id in context.bot_data['subscribers']:

        if chat_id not in context.bot_data['chats']:
            context.bot_data['chats'] = {}

        user_data = _get_user_data(chat_id, context.bot_data)

        txt = "\n\n".join(_check(api_data, user_data))
        if txt:
            context.bot.send_message(chat_id, text=txt)


def main():
    persistence = PicklePersistence(filename='bot_persistence')

    updater = Updater(
        os.environ["TELEGRAM_BOT_TOKEN"],
        use_context=True,
        persistence=persistence)

    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("help", start))
    updater.dispatcher.add_handler(CommandHandler("info", info))
    updater.dispatcher.add_handler(CommandHandler("watch", watch))
    updater.dispatcher.add_handler(CommandHandler("unwatch", unwatch))
    updater.dispatcher.add_handler(CommandHandler("states", states))
    updater.dispatcher.add_handler(CommandHandler("state", info))
    updater.dispatcher.add_handler(CommandHandler("subscribe", subscribe))
    updater.dispatcher.add_handler(CommandHandler("unsubscribe", unsubscribe))

    updater.dispatcher.bot_data['chats'] = \
        updater.dispatcher.bot_data.get('chats', {})

    updater.dispatcher.bot_data['subscribers'] = \
        updater.dispatcher.bot_data.get('subscribers', set())

    updater.job_queue.run_repeating(poll_api, interval=60, first=10)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
