from API_TG import bot
from telebot import types

def create_keyboards(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add(
        types.KeyboardButton('Reserve a table'),
        types.KeyboardButton('Menu/Order'),
        types.KeyboardButton('My orders')
    )
    keyboard.add(types.KeyboardButton('Exit'))

    bot.send_message(
        message.chat.id,
        'Select an action: ',
        reply_markup=keyboard
    )    