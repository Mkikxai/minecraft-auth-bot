import os
import telebot
from telebot import types
from flask import Flask, request, jsonify

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Базы данных в памяти
pending_codes = {}     # { code: { 'player': player_name, 'chat_id': chat_id } }
player_chats = {}      # { player_name: chat_id }
linked_accounts = {}   # { player_name: chat_id }

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    btn_link = types.InlineKeyboardButton("🔗 Привязать аккаунт", callback_data="get_link_code")
    markup.add(btn_link)
    
    bot.send_message(
        message.chat.id, 
        "🛡 *Система безопасности сервера*\n\nНажмите кнопку ниже, чтобы начать привязку:", 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "get_link_code":
        msg = bot.send_message(call.message.chat.id, "👤 Введите ваш точный никнейм в игре:")
        bot.register_next_step_handler(msg, process_nickname)
    
    elif call.data.startswith("accept_"):
        player_name = call.data.split("_")[1]
        bot.edit_message_text(f"✅ Вход в аккаунт *{player_name}* подтвержден.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    elif call.data.startswith("kick_"):
        player_name = call.data.split("_")[1]
        bot.edit_message_text(f"🚨 Сессия игрока *{player_name}* сброшена!", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

def process_nickname(message):
    import random
    player_name = message.text.strip().lower()
    chat_id = message.chat.id
    
    code = str(random.randint(100000, 999999))
    pending_codes[code] = {
        'player': player_name,
        'chat_id': chat_id
    }

    bot.send_message(
        chat_id, 
        f"🔑 Ваш код для привязки: *{code}*\n\nЗайдите на сервер и введите в чат:\n`/tg {code}`", 
        parse_mode="Markdown"
    )

# Проверка кода из игры (вызывается плагином Minecraft)
@app.route('/verify-code', methods=['POST'])
def verify_code():
    data = request.json
    if not data:
        return jsonify({"status": "error"}), 400
        
    code = data.get('code')
    player_name = data.get('player')
    
    if not code or not player_name:
        return jsonify({"status": "error"}), 400
        
    player_name = player_name.lower()

    if code in pending_codes and pending_codes[code]['player'] == player_name:
        chat_id = pending_codes[code]['chat_id']
        player_chats[player_name] = chat_id
        linked_accounts[player_name] = chat_id
        del pending_codes[code]
        return jsonify({"status": "success"}), 200
    
    return jsonify({"status": "error"}), 400

# Уведомление о входе
@app.route('/alert', methods=['POST'])
def alert_user():
    data = request.json
    if not data:
        return "Bad Request", 400
        
    player_name = data.get('player')
    ip = data.get('ip', 'Неизвестный IP')
    
    if not player_name:
        return "Bad Request", 400
        
    player_name = player_name.lower()
    
    chat_id = player_chats.get(player_name)
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
    import threading
    # Запуск Flask-сервера на порту, который требует Render (по умолчанию 10000 или из переменной PORT)
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port)).start()
    bot.infinity_polling()
