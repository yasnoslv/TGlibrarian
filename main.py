import os
import logging
import json
from aiogram import Bot, Dispatcher, executor, types
from decouple import config
import http.client
import requests
import random
from pymongo import *

servr_connect = MongoClient()
db_con = servr_connect['bookwormDB']


API_TOKEN = config('TELEGRAM_BOT_TOKEN')

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

books_keyboard = types.InlineKeyboardMarkup(row_width=1)
selected_keyboard = types.InlineKeyboardMarkup(row_width=3)


def get_books(data:dict): # ВСкод не дає підказки щодо документації, тож може виглядати дивновато
    """ Додає книги як кнопки у клавіатуру 
    
    :param data: Отримана получена дата АПІ в JSON
    :return: None
    """
    books = data['results']
    books_keyboard['inline_keyboard'] = []
    for book in books:
        book = types.InlineKeyboardButton(text = book["title"], callback_data = f'id_{book["id"]}')
        books_keyboard.add(book)

    
def get_selected(data:dict):
    """ Додає формати завантаження книги як кнопки у клавіатуру
    
    :param data: Отримана получена дата АПІ в JSON
    :return: None
    """
    book = data['results'][0]['formats']
    selected_keyboard['inline_keyboard'] = []
    selected_keyboard.add(
        types.InlineKeyboardButton(text = 'html', url = book['text/html']),
        types.InlineKeyboardButton(text = 'epub', url = book['application/epub+zip']),
        types.InlineKeyboardButton(text = 'mobi', url = book['application/x-mobipocket-ebook'])
    )


@dp.message_handler(commands=['start'])
async def quotes(message: types.Message):
    await message.answer('<b>Greetings!</b>\nThis bot will help you find some books, and motivate you to read them.\nTo search, just write the name or author of the book you want, and proceed.\nYou can also generate a random inspirational quote using <i>/quotes</i>\n<b>We appreciate your support, safe travels!~</b>', parse_mode='HTML')


@dp.message_handler(commands=['quotes'])
async def quotes(message: types.Message):
    quotes = db_con['quotes']
    for dc in quotes.find().skip(random.randint(1,5420)).limit(1):
        await message.answer(f'<i>{dc["quote"]}</i>\n<b>{dc["author"]}</b>', parse_mode='HTML')


@dp.message_handler()
async def results(message: types.Message):
    msg = message.text.replace(' ', '%20')
    response = requests.get("http://gutendex.com/books/?search="+msg)
    data = json.loads(response.content)
    get_books(data)
    await message.reply(f"{data['count']} results found.", reply_markup=books_keyboard)


@dp.callback_query_handler(text_contains='id_')
async def state_books(call: types.CallbackQuery):
    response = requests.get("http://gutendex.com/books/?ids="+call.data.split('_')[-1])
    data = json.loads(response.content)
    get_selected(data)
    title = data['results'][0]['title']
    authors = ' & '.join([i['name'] for i in data['results'][0]['authors']])
    subjects = '\n'.join(data['results'][0]['subjects'])
    languages = '\n'.join(data['results'][0]['languages'])
    image = data['results'][0]['formats']['image/jpeg']
    
    text = f"<b>{title}</b>\n<i>- by {authors}</i>\n\n{subjects}\n\n<i>languages: {languages}</i>"
    await call.message.answer_photo(image, caption = text, parse_mode='HTML', reply_markup=selected_keyboard)
    
    
    

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)