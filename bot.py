import os
import telebot
from flask import Flask, request

TOKEN = os.getenv("BOT_TOKEN")
# Получаем URL вашего приложения на Render автоматически или вбейте вручную
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

# Вебхук-эндпоинт для получения обновлений от Telegram
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
    # Сбрасываем старый вебхук и устанавливаем новый
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_EXTERNAL_URL}/{TOKEN}")
    
    # Запускаем Flask-сервер на порту 10000, как требует Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
