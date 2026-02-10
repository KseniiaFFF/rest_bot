
import random

from API_TG import bot
from telebot import types
from db import db
from db import db_fetchall
from keyb_rest import create_keyboards

#sozdanie bd

# try:
#     db("ALTER TABLE tables ADD COLUMN user_id INTEGER")
# except:
#     pass
# try:
#     db("UPDATE tables SET is_free = 1 WHERE is_free = 0")
# except:
#     pass


def create_tables():
    db("""CREATE TABLE IF NOT EXISTS users (tg_id INTEGER PRIMARY KEY , name TEXT)""")
    db("""CREATE TABLE IF NOT EXISTS tables (id INTEGER PRIMARY KEY AUTOINCREMENT, is_free INTEGER)""")
    db("""CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, table_id INTEGER, order_text TEXT)""")



#menu knopki
@bot.message_handler(commands=['start'])
def add_user(message):
    chat_id = message.chat.id

    db(
        "UPDATE tables SET is_free = 1, user_id = NULL WHERE user_id = ?",
        (chat_id,)
    )

    create_keyboards(message)

    user_name = message.from_user.username
    db(
        "INSERT OR IGNORE INTO users (tg_id, name) VALUES (?, ?)",
        (chat_id, user_name)
    )

    bot.send_message(chat_id, "Добро пожаловать 👋")


    
@bot.message_handler(func=lambda message: message.text in [
    'Reserve a table',
    'Menu/Order',
    'My orders',
    'Exit'
])
def handle_buttons(message):

    if message.text == 'Reserve a table':
        bot.send_message(message.chat.id, 'Select an available table')
        hochu_stolik(message)

    elif message.text == 'Menu/Order':
        bot.send_message(message.chat.id, 'Our menu')
        menu(message)

    elif message.text == 'My orders':
        bot.send_message(message.chat.id, 'Your orders')
        my_orders(message)

    elif message.text == 'Exit':
        bot.send_message(message.chat.id, 'We look forward to your return')    


#logika knopki chochu stolik
def hochu_stolik(message):
    rows = db_fetchall("SELECT id FROM tables WHERE is_free = 1")

    if not rows:
        bot.send_message(message.chat.id, "Свободных столов нет")
        return

    markup = types.InlineKeyboardMarkup()
    for row in rows:
        markup.add(
            types.InlineKeyboardButton(
                text=f"Стол {row[0]}",
                callback_data=f"table_{row[0]}"
            )
        )

    bot.send_message(
        message.chat.id,
        "Стол выбран:)",
        reply_markup=markup
    )



#fix broni

@bot.callback_query_handler(func=lambda call: call.data.startswith("table_"))
def occupy_table(call):
    chat_id = call.message.chat.id
    table_id = int(call.data.split("_")[1])

    rows = db_fetchall(
        "SELECT is_free FROM tables WHERE id = ?",
        (table_id,)
    )

    if not rows:
        bot.send_message(chat_id, "Такого стола не существует")
        return

    if rows[0][0] == 0:
        bot.send_message(chat_id, "Стол уже занят ")
        return

    db(
        "UPDATE tables SET is_free = 0, user_id = ? WHERE id = ?",
        (chat_id, table_id)
    )

    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=None
    )

    bot.send_message(
        chat_id,
        f"Стол №{table_id} забронирован ✅\n"
        "Перехожу в меню "
    )

    menu(call.message)

  

#menu bluda

def menu(message):

    menu_items = {
        'cake': 40,
        'pizza': 100,
        'icecreame': 30,
        'water': 300
    }

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    for item, price in menu_items.items():
        keyboard.add(
            types.KeyboardButton(f'{item}-{price}')
        )

    keyboard.add(types.KeyboardButton('Готово / Оплатить'))
    keyboard.add(types.KeyboardButton('Exit'))

    bot.send_message(
        message.chat.id,
        'Выберите блюда. Когда закончите — нажмите «Готово / Оплатить» 👇',
        reply_markup=keyboard
    )

user_data = {}

@bot.message_handler(func=lambda m: m.text and m.text.count('-') == 1)

def add_to_order(message):
    chat_id = message.chat.id

    if chat_id not in user_data:
        user_data[chat_id] = {'order': []}

    user_data[chat_id]['order'].append(message.text)

    bot.send_message(
        chat_id,
        f"Добавлено: {message.text} ✅\n"
        "Можно выбрать ещё или нажать «Готово / Оплатить»"
    )

@bot.message_handler(func=lambda message: message.text == 'Готово / Оплатить')
def go_to_payment(message):
    chat_id = message.chat.id

    order = user_data.get(chat_id, {}).get('order')

    if not order:
        bot.send_message(chat_id, "Вы не выбрали ни одного блюда ")
        return

    order_text = ', '.join(order)

    bot.send_message(
        chat_id,
        f"Ваш заказ:\n{order_text}\n\n"
        "Введите номер карты "
    )

    bot.register_next_step_handler(message, get_card)


#oplata

def get_card(message):
    chat_id = message.chat.id
    card = message.text.strip()

    if not card.isdigit() or len(card) != 12:
        bot.send_message(
            chat_id,
            'Номер карты должен состоять из 12 цифр. Попробуйте ещё раз'
        )
        bot.register_next_step_handler(message, get_card)
        return

    user_data.setdefault(chat_id, {})
    user_data[chat_id]['card'] = card

    bot.send_message(chat_id, 'Введите CVV код ')
    bot.register_next_step_handler(message, get_cvv)


def get_cvv(message):
    chat_id = message.chat.id
    cvv = message.text.strip()

    if not cvv.isdigit() or len(cvv) != 3:
        bot.send_message(
            chat_id,
            'CVV должен состоять из 3 цифр. Попробуйте ещё раз'
        )
        bot.register_next_step_handler(message, get_cvv)
        return

    user_data[chat_id]['cvv'] = cvv

    bot.register_next_step_handler(message, pay_verif)


def pay_verif(message):
    chat_id = message.chat.id

    if random.random() >= 0.5:
        bot.send_message(chat_id, "Проверка...Оплата не прошла ")
        return

    order = user_data.get(chat_id, {}).get('order')
    if not order:
        bot.send_message(chat_id, "Ошибка: заказ не найден")
        return

    order_text = ', '.join(order)

    rows = db_fetchall(
        "SELECT id FROM tables WHERE user_id = ? AND is_free = 0",
        (chat_id,)
    )

    if not rows:
        bot.send_message(chat_id, "Ошибка: стол не найден")
        return

    table_id = rows[0][0]

    db(
        "INSERT INTO orders (user_id, table_id, order_text) VALUES (?, ?, ?)",
        (chat_id, table_id, order_text)
    )

    bot.send_message(
        chat_id,
        f"Оплата прошла успешно ✅\n"
        f"Стол №{table_id}\n"
        f"Заказ: {order_text}"
    )

    user_data.pop(chat_id, None)


#orders

@bot.message_handler(func=lambda message: message.text == 'My orders')
def my_orders(message):
    chat_id = message.chat.id

    rows = db_fetchall(
        "SELECT table_id, order_text FROM orders WHERE user_id = ?",
        (chat_id,)
    )

    if not rows:
        bot.send_message(chat_id, "У вас пока нет заказов 📭")
        return

    text = "Ваши заказы:\n\n"
    for i, row in enumerate(rows, start=1):
        table_id, order_text = row
        text += f"{i}. Стол №{table_id}\n   {order_text}\n\n"

    bot.send_message(chat_id, text)



# #uvelich kol-vo stolov
@bot.message_handler(commands=['max'])
def max_tables(message):
    chat_id = message.chat.id

    db("INSERT INTO tables (is_free) VALUES (1)")

    cursor = db("SELECT COUNT(*) FROM tables")
    total_tables = cursor.fetchone()[0]

    bot.send_message(chat_id, f"Стол добавлен. Всего столов: {total_tables}")



bot.polling()    