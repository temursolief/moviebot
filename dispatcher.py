#!/usr/bin/env python
# pylint: disable=C0116,W0613

import requests
import logging

from telegram import (Update, ForceReply, ParseMode,
                      ReplyKeyboardMarkup, KeyboardButton, 
                      InlineKeyboardMarkup, InlineKeyboardButton,
                      ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, 
                          MessageHandler, Filters, 
                          CallbackContext, ConversationHandler,
                          CallbackQueryHandler)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = ""

MOVIE_NAME, CHOICE = 0,1

""" BOT KEYBOARDS ---->
"""

def startmenu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard = [
            [KeyboardButton(text="🤭How to?"),
             KeyboardButton(text="🔍Search"),
             KeyboardButton(text="🔥Popular"), ],
            [KeyboardButton(text="📈Trending"),
             KeyboardButton(text="🧞‍♂️Genres")],
        ],
        resize_keyboard=True
    )
    
"""INLINE KEYBOARDS
"""

def search_result_inlinekeyboards(results):
    return InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton(text=result["original_title"], callback_data='movie-id-{0}'.format(result['id']))] for result in results
        ]
    )


def back_to_search_list():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("Back to the list", callback_data="Back-to-search-results-list")]
        ]
    )


"""BOT HANDLERS --->
"""
def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\! \nI am a movie info bot\. I will do my best to search for anything related to a movie from my database\. \nNow try me by using the keyboard given\.',
        reply_markup=startmenu_keyboard(),
    )


def help_command(update: Update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


MOVDB_API = ""
search_url = f"https://api.themoviedb.org/3/search/movie?api_key={MOVDB_API}&"
img_path = "https://image.tmdb.org/t/p/w500"



def wait_for_movie_name(update: Update, context:CallbackContext):
    update.message.reply_text(
        "Send me the name of the movie you want to find information about 😊:", reply_markup=ReplyKeyboardRemove(remove_keyboard=True))
    
    return MOVIE_NAME

def return_search_results(update:Update, context:CallbackContext):
    user_query = update.message.text
    user_id = update.message.from_user.id
    data = requests.get(search_url+f"query={user_query}").json()
    results = data['results']
    context.bot.send_message(
        chat_id=user_id, text="Search Results:", reply_markup=search_result_inlinekeyboards(results))
    
    return CHOICE

def return_movie_info(update:Update, context:CallbackContext):
    query = update.callback_query
    user_id = query.message.chat.id
    query.delete_message()
    
    data = update.callback_query.data.split('-')
    movie_id = data[2]
    movie_data = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={MOVDB_API}&language=en-US').json()
    photo = f"https://image.tmdb.org/t/p/w500{movie_data['poster_path']}"
    title = movie_data["original_title"]
    overview = movie_data["overview"]
    release_date = movie_data['release_date']
    budget = "${:,.2f}".format(movie_data["budget"])
    genres = " ".join([genre["name"].strip() for genre in movie_data["genres"]])
    production_companies = ", ".join([company["name"] for company in movie_data["production_companies"]])
    revenue = "${:,.2f}".format(movie_data["revenue"])
    tagline = movie_data["tagline"]
    vote_average = movie_data["vote_average"]
    
    caption = f'<b>{title}</b>\n\n'
    caption += f'Budget: {budget}\n'
    caption += f'Revenue: {revenue}\n'
    caption += f'Release Date: {release_date}\n\n'
    caption += f'{production_companies}\n\n'
    caption += f'<b>{genres}</b>\n\n'
    caption += f'Average vote: ⭐️ {vote_average} ⭐️\n\n'
    caption += f'{tagline}\n'
    caption += f'<i>{overview}</i>\n'
    try:
        context.bot.send_photo(chat_id=user_id, photo=photo,
                            caption=caption, parse_mode=ParseMode.HTML)
    except:
        context.bot.send_message(chat_id=user_id, text=caption, parse_mode=ParseMode)
    
    # reply_markup = back_to_search_list()
    return ConversationHandler.END


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TELEGRAM_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    search_handlers = ConversationHandler(
        entry_points=[MessageHandler(
            Filters.text('🔍Search'), wait_for_movie_name)],
        states = {
            MOVIE_NAME: [
                MessageHandler(Filters.text & ~Filters.command,
                               return_search_results)
            ],
            CHOICE: [
                CallbackQueryHandler(return_movie_info, pattern=r'movie-id-')],
            # BACK: [
            #     CallbackQueryHandler(return_search_results,
            #                          pattern='Back-to-search-results-list')
            # ],
        },
        fallbacks= [MessageHandler(Filters.regex('^Done$'), wait_for_movie_name)]
    )
    dispatcher.add_handler(search_handlers)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
