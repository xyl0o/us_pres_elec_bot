import logging
import os

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, PicklePersistence

from check import parse_data, get_data, textify_change, filter_states

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
Use /set <minutes> to set the interval i should look for new votes.
Use /cancel to stop me from texting you.
Use /poll to get updates now.

Currently the following states are considered: {battlegrounds}.
""")


def check(context):
    """Crawl api and notfy "subscribers" if votes changed"""

    dp = context.dispatcher
    user_data = dp.user_data

    chat_id = context.job.context

    new = parse_data(get_data())
    old = user_data.get('old')

    if not old:
        user_data['old'] = new
        return

    for state in filter_states(old, new, battlegrounds):

        txt = textify_change(
            state=state, old=old[state], new=new[state], candidates=candidates)

        context.bot.send_message(chat_id, text=txt)

        old[state] = new[state]
    else:
        return False # loop never ran

    user_data['old'] = old

    return True


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

        text = 'Interval set successfully!'

        update.message.reply_text(text)

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

    if chat_id in context.bot_data['intervals']:
        interval = context.bot_data['intervals'][chat_id]
        remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_repeating(check, interval, context=chat_id, name=str(chat_id))

    context.job_queue.run_once(check, 0, context=chat_id, name=f"{chat_id}_poll")


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
