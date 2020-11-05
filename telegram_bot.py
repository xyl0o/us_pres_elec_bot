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
Use /set <minutes> to set the update interval.
Use /cancel to stop me from texting you.
Use /poll to force me to look for updates now.
Use /info <state> to get current state votes.
Use /info to get current state votes of your watchlist.
Use /watch <state> to add a state to your watchlist.
Use /unwatch <state> to add unwatch a state.
Use /states to get a list of all states.

Currently the following states are considered: {battlegrounds}.
""")


def _check(user_data):
    new = parse_data(get_data())
    old = user_data.get('old')

    if not old:
        user_data['old'] = new
        return

    for state in filter_states(old, new, user_data['watchlist']):

        yield textify_change(
            state=state, old=old[state], new=new[state], candidates=candidates)

        old[state] = new[state]
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


def check(context):
    """Crawl api and notfy "subscribers" if votes changed"""

    chat_id = context.job.context

    for txt in _check(context.dispatcher.user_data):
        context.bot.send_message(chat_id, text=txt)


def remove_job_if_exists(name, context):
    current_jobs = context.job_queue.get_jobs_by_name(name)

    if not current_jobs:
        return False

    for job in current_jobs:
        job.schedule_removal()

    return True


def set_interval(update: Update, context: CallbackContext) -> None:
    """Set the update interval. context.args[0] should contain update interval in minutes."""
    chat_id = update.message.chat_id

    try:
        interval = int(context.args[0]) * 60
        if interval < 0:
            update.message.reply_text('Sorry, we can not go back to future!')
            return

        _ = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_repeating(check, interval, context=chat_id, name=str(chat_id))
        context.bot_data['intervals'].update({chat_id: interval})
        if 'watchlist' not in context.user_data:
            context.user_data['watchlist'] = battlegrounds

        txt = 'Interval set successfully!\n'
        txt += 'You are currently watching '
        txt += ', '.join(sorted(context.user_data['watchlist']))

        update.message.reply_text(txt)

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /set <minutes>')


def cancel(update: Update, context: CallbackContext) -> None:
    """Allow the user to cancel the updates"""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    context.bot_data['intervals'].update({chat_id: 0})
    text = "I won't bother you anymore." if job_removed else "I didn't plan on texting you anyway."
    update.message.reply_text(text)


def poll(update: Update, context: CallbackContext) -> None:
    """Allow the user to cancel the updates"""
    chat_id = update.message.chat_id

    for txt in _check(context.user_data):
        update.message.reply_text(txt)
    else:
        update.message.reply_text("No changes found")


def info(update: Update, context: CallbackContext) -> None:
    """Allow the user to cancel the updates"""
    chat_id = update.message.chat_id

    try:
        raw_state = context.args[0]
    except (IndexError, ValueError):
        states = context.user_data.get('watchlist', set())
    else:
        if not (state := _select_state(raw_state)):
            update.message.reply_text(f'Unknown state {raw_state}')
            return
        states = {raw_state}

    new = parse_data(get_data())
    for s in states:
        update.message.reply_text(
            textify_change(state=s, new=new[s], candidates=candidates))


def watch(update: Update, context: CallbackContext) -> None:
    """Allow the user to cancel the updates"""
    chat_id = update.message.chat_id

    try:
        raw_state = str(context.args[0])
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /watch <state>')
        return

    if not (state := _select_state(raw_state)):
        update.message.reply_text(f'Unknown state {raw_state}')
        return

    if 'watchlist' not in context.user_data:
        context.user_data['watchlist'] = battlegrounds

    update.message.reply_text(f"I've added {state} to your watchlist.")

    context.user_data['watchlist'] |= {state}


def unwatch(update: Update, context: CallbackContext) -> None:
    """Allow the user to cancel the updates"""
    chat_id = update.message.chat_id

    try:
        raw_state = context.args[0]
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /unwatch <state>')
        return

    if not (state := _select_state(raw_state)):
        update.message.reply_text(f'Unknown state {raw_state}')
        return

    if 'watchlist' not in context.user_data:
        context.user_data['watchlist'] = battlegrounds

    update.message.reply_text(f"I've removed {state} from your watchlist.")

    context.user_data['watchlist'] -= {state}


def states(update: Update, context: CallbackContext) -> None:
    """Allow the user to cancel the updates"""
    chat_id = update.message.chat_id

    watchlist = context.user_data.get('watchlist', set())

    txt = 'I know of the following states:\n'
    for k, v in states_dict.items():
        txt += f'{v} ({k})'
        if v in watchlist:
            txt += ' - watching'
        txt += '\n'

    update.message.reply_text(txt)


def main():
    persistence = PicklePersistence(filename='bot_persistence')

    updater = Updater(
        os.environ["TELEGRAM_BOT_TOKEN"],
        use_context=True,
        persistence=persistence)

    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("help", start))
    updater.dispatcher.add_handler(CommandHandler("set", set_interval))
    updater.dispatcher.add_handler(CommandHandler("poll", poll))
    updater.dispatcher.add_handler(CommandHandler("cancel", cancel))
    updater.dispatcher.add_handler(CommandHandler("info", info))
    updater.dispatcher.add_handler(CommandHandler("watch", watch))
    updater.dispatcher.add_handler(CommandHandler("unwatch", unwatch))
    updater.dispatcher.add_handler(CommandHandler("states", states))

    if 'intervals' not in updater.dispatcher.bot_data:
        updater.dispatcher.bot_data['intervals'] = {}

    for chat_id, interval in updater.dispatcher.bot_data['intervals'].items():
        if interval:
            updater.job_queue.run_repeating(
                check, interval, context=chat_id, name=str(chat_id))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
