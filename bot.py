import os
import telebot
from flask import Flask, request, jsonify

TOKEN = os.getenv("BOT_TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "https://minecraft-auth-bot.onrender.com")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

pending_codes = {}   
player_chats = {}    

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    btn_link = telebot.types.InlineKeyboardButton("🔗 Привязать аккаунт", callback_data="get_link_code")
    markup.add(btn_link)
    
    bot.send_message(
        message.chat.id, 
        "🛡 *Система безопасности сервера*\n\nНажмите кнопку ниже для привязки аккаунта:", 
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
    pending_codes[code] = chat_id
    player_chats[player_name] = chat_id
    
    print(f"[DEBUG] Сгенерирован код {code} для игрока {player_name} (chat_id: {chat_id})")
    print(f"[DEBUG] Активные коды сейчас: {list(pending_codes.keys())}")

    bot.send_message(
        chat_id, 
        f"🔑 Ваш код для привязки: *{code}*\n\nЗайдите на сервер и введите в чат:\n`/tg {code}`", 
        parse_mode="Markdown"
    )

@app.route('/verify', methods=['POST'])
@app.route('/verify-code', methods=['POST'])
def verify_code():
    data = request.get_json()
    print(f"[DEBUG] Получен запрос /verify с данными: {data}")
    
    if not data:
        return jsonify({"status": "error", "message": "No JSON data"}), 400
        
    code = str(data.get('code')).strip()
    player_name = str(data.get('player')).strip().lower()
    
    print(f"[DEBUG] Игрок {player_name} пытается ввести код: {code}")
    print(f[DEBUG] "Активные коды в памяти: {pending_codes}")

    if code in pending_codes:
        chat_id = pending_codes[code]
        bot.send_message(
            chat_id, 
            f"✅ Аккаунт успешно привязан к игроку *{player_name}*!", 
            parse_mode="Markdown"
        )
        del pending_codes[code]
        return jsonify({"status": "success"}), 200
        
    return jsonify({"status": "error", "message": "Invalid code"}), 400

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route('/')
def index():
    return "Bot is running!", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_EXTERNAL_URL}/{TOKEN}")
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
