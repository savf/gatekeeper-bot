#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.
#
# THIS EXAMPLE HAS BEEN UPDATED TO WORK WITH THE BETA VERSION 12 OF PYTHON-TELEGRAM-BOT.
# If you're still using version 11.1.0, please see the examples at
# https://github.com/python-telegram-bot/python-telegram-bot/tree/v11.1.0/examples

"""
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic inline bot example. Applies different text transformations.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import os
from loguru import logger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Filters, Updater, MessageHandler, CommandHandler, CallbackQueryHandler
from telegram.error import BadRequest
from random import shuffle

# Enable logging
logger.add("logs/gatekeeper-bot_{time}.log",
           format="{time} - {name} - {level} - {message}", level="INFO", rotation="5 MB")

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.


def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text("Hello, I am the Swiss Mechanical Keyboard Enthusiasts Gatekeeper. "
                              "As soon as a new user joins, they will be restricted to keep them "
                              "from posting until they prove they are not a robot.")


def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Available commands:\n\n/id')


def id(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text(update.effective_chat.id)


def remove_job_if_exists(name, context):
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(str(name))
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def welcome_timeout(context):
    """Remove welcome message after predifined timeout in os.environ['TIMEOUT'] """
    job_context = context.job.context

    if 'message_id' in job_context:
        try:
            context.bot.delete_message(
                chat_id=os.environ['CHAT_ID'],
                message_id=job_context['message_id']
            )
            logger.info('Welcome message for "{first_name}" timed out after {seconds} seconds.',
                        first_name=job_context['first_name'], seconds=os.environ['TIMEOUT'])
        except BadRequest:
            logger.info('Welcome message with id "{message_id}" no longer exists.',
                        message_id=job_context['message_id'])


def hodor(update, context):
    try:
        for new_member in update.message.new_chat_members:
            callback_id = str(new_member.id)
            context.bot.restrict_chat_member(
                int(os.environ['CHAT_ID']),
                new_member.id,
                ChatPermissions(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False)
            )

            keyboard_items = [
                InlineKeyboardButton(
                    'Mechanical', callback_data=callback_id + ',mech'),
                InlineKeyboardButton(
                    'Rubberdome', callback_data=callback_id + ',rubber'),
            ]

            shuffle(keyboard_items)
            keyboard = []
            for i in range(2):
                keyboard.append([keyboard_items[i]])
            reply_markup = InlineKeyboardMarkup(keyboard)

            timeout_seconds = int(os.environ['TIMEOUT'])
            timeout_minutes = str(int(timeout_seconds / 60))
            message = update.message.reply_text(
                'Hello, ' +
                new_member.first_name +
                ' and welcome to the Swiss Mech Chat. Just a small formality before we allow you to post: ' +
                'Please prove that you are not a robot by choosing "Mechanical" below. You have ' +
                timeout_minutes +
                ' minutes to answer.',
                reply_markup=reply_markup,
                disable_notification=True
            )

            remove_job_if_exists(callback_id, context)
            context.job_queue.run_once(welcome_timeout, timeout_seconds, context={
                                       "message_id": message.message_id, "first_name": new_member.first_name}, name=callback_id)
    except AttributeError:
        pass


def button(update, context):
    query = update.callback_query
    person_who_pushed_the_button = int(query.data.split(",")[0])

    if query.from_user.id == person_who_pushed_the_button:
        logger.info('User "{user}" sent back "{reply}"',
                    user=str(query.from_user), reply=str(query.data))
        remove_job_if_exists(person_who_pushed_the_button, context)
        if 'mech' in query.data:
            context.bot.delete_message(
                chat_id=update.callback_query.message.chat_id,
                message_id=update.callback_query.message.message_id
            )
            context.bot.restrict_chat_member(
                int(os.environ['CHAT_ID']),
                person_who_pushed_the_button,
                ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True)
            )
        else:
            query.edit_message_text(text="🚨 Looks like we have another bot. 🚨")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "{update}" caused error "{error}"',
                   update=update, error=context.error)


def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(str(os.environ['TOKEN']), use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("id", id))

    dp.add_handler(MessageHandler(
        Filters.chat(int(os.environ['CHAT_ID'])), hodor))

    updater.dispatcher.add_handler(CallbackQueryHandler(button))

    # on noncommand i.e message - echo the message on Telegram

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
