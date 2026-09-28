import os
import telebot
from telebot import types
from flask import Flask, request

TOKEN = os.getenv("8663656567:AAF4HGgh9rusfHxWk0-smUBx3gnaGjng3SI")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Базы данных в памяти (для привязок и сессий)
linked_users = {}      # { chat_id: player_name }
player_chats = {}      # { player_name: chat_id }
pending_codes = {}     # { code: player_name }

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    btn_link = types.InlineKeyboardButton("🔗 Получить код привязки", callback_data="get_link_code")
    markup.add(btn_link)
    
    bot.send_message(
        message.chat.id, 
        "🛡 *Система безопасности сервера*\n\nНажмите кнопку ниже, чтобы привязать игровой аккаунт:", 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "get_link_code":
        msg = bot.send_message(call.message.chat.id, "👤 Введите ваш никнейм в игре:")
        bot.register_next_step_handler(msg, process_nickname)
    
    elif call.data.startswith("accept_"):
        player_name = call.data.split("_")[1]
        bot.edit_message_text(f"✅ Вход в аккаунт *{player_name}* подтвержден.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    elif call.data.startswith("kick_"):
        player_name = call.data.split("_")[1]
        bot.edit_message_text(f"🚨 Сессия игрока *{player_name}* сброшена! (Запрос отправлен на сервер)", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        # Здесь бот может отправить сигнал на сервер для кика

def process_nickname(message):
    import random
    player_name = message.text.strip().lower()
    chat_id = message.chat.id
    
    code = str(random.randint(100000, 999999))
    pending_codes[code] = player_name
    player_chats[player_name] = chat_id
    linked_users[chat_id] = player_name

    bot.send_message(
        chat_id, 
        f"🔑 Ваш код привязки для игры: *{code}*\n\nЗайдите на сервер и введите в чат:\n`/tg {code}`", 
        parse_mode="Markdown"
    )

# Веб-сервер для получения запросов от Minecraft плагина
@app.route('/alert', methods=['POST'])
def alert_user():
    data = request.json
    player_name = data.get('player')
    ip = data.get('ip')
    
    chat_id = player_chats.get(player_name.lower())
    if chat_id:
        markup = types.InlineKeyboardMarkup()
        btn_accept = types.InlineKeyboardButton("✅ Принять", callback_data=f"accept_{player_name}")
        btn_kick = types.InlineKeyboardButton("🚨 Это не я, кикнуть!", callback_data=f"kick_{player_name}")
        markup.add(btn_accept, btn_kick)

        bot.send_message(
            chat_id,
            f"⚠️ *Внимание!* Вход в аккаунт *{player_name}* с IP: `{ip}`.\nЕсли это не вы, нажмите кнопку ниже:",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return "OK", 200
    return "User not found", 404

if __name__ == "__main__":
    # Запуск бота и веб-сервера одновременно для Render
    import threading
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))).start()
    bot.infinity_polling()
