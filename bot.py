import os
import telebot
from telebot import types

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Хранилище кодов привязки
pending_codes = {}   # { code: player_name }
player_chats = {}    # { player_name: chat_id }

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    btn_link = types.InlineKeyboardButton("🔗 Привязать аккаунт", callback_data="get_link_code")
    markup.add(btn_link)
    
    bot.send_message(
        message.chat.id, 
        "🛡 *Система безопасности сервера*\n\nНажмите кнопку ниже для привязки:", 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "get_link_code":
        msg = bot.send_message(call.message.chat.id, "👤 Введите ваш точный никнейм в игре:")
        bot.register_next_step_handler(msg, process_nickname)

def process_nickname(message):
    import random
    player_name = message.text.strip().lower()
    chat_id = message.chat.id
    
    code = str(random.randint(100000, 999999))
    pending_codes[code] = player_name
    player_chats[player_name] = chat_id

    bot.send_message(
        chat_id, 
        f"🔑 Ваш код для привязки: *{code}*\n\nЗайдите на сервер и введите:\n`/tg {code}`", 
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    print("Бот запущен в режиме Long Polling...")
    # Очищаем зависшие соединения и запускаем бесконечный опрос
    bot.infinity_polling(skip_pending=True)
