import os
import telebot
from telebot import types

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Хранилище привязок: { player_name: chat_id }
linked_players = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("🔗 Привязать аккаунт", callback_data="start_link")
    markup.add(btn)
    bot.send_message(
        message.chat.id, 
        "🛡 *Система безопасности сервера*\n\nНажмите кнопку ниже, чтобы привязать ваш игровой аккаунт:", 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "start_link")
def ask_nickname(call):
    msg = bot.send_message(call.message.chat.id, "👤 Введите ваш точный никнейм в игре (как в Minecraft):")
    bot.register_next_step_handler(msg, save_link)

def save_link(message):
    player_name = message.text.strip().lower()
    chat_id = message.chat.id
    
    linked_players[player_name] = chat_id
    
    bot.send_message(
        chat_id,
        f"✅ Ваш ник *{player_name}* успешно связан с этим Telegram!\nТеперь зайдите на сервер и введите в чат команду:\n`/tg`",
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    print("Бот успешно запущен и работает!")
    bot.infinity_polling()
