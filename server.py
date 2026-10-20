import telebot
import random
import time
import os

BOT_TOKEN = os.environ.get('8987546633:AAGehEF6GHQCnjWTrpYbaqf7qDXlh37LACk')
bot = telebot.TeleBot(BOT_TOKEN)

active_codes = {}
sessions = {}

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет! Отправь мне код с сайта LoveLink, чтобы войти.")

@bot.message_handler(func=lambda message: True)
def handle_code(message):
    code = message.text.strip()
    if code in active_codes:
        data = active_codes[code]
        if time.time() - data['time'] < 300:
            session_id = str(random.randint(100000, 999999))
            sessions[session_id] = {
                "name": message.from_user.first_name or "Пользователь",
                "username": message.from_user.username or "user_" + str(message.from_user.id)
            }
            del active_codes[code]
            bot.send_message(message.chat.id, f"✅ Успешно! Возвращайся на сайт.")
            active_codes[code] = {"session_id": session_id, "status": "ok"}
        else:
            bot.send_message(message.chat.id, "❌ Код истек.")
    else:
        bot.send_message(message.chat.id, "❌ Неверный код.")

# Тут мы создаем простой веб-сервер для связи с сайтом (сайту нужен адрес)
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response

@app.route('/api/get_code', methods=['POST'])
def get_code():
    code = str(random.randint(1000, 9999))
    active_codes[code] = {"time": time.time(), "status": "waiting"}
    return jsonify({"code": code})

@app.route('/api/check_code', methods=['POST'])
def check_code():
    data = request.json
    code = data.get('code')
    if code in active_codes:
        if active_codes[code].get('status') == 'ok':
            session_id = active_codes[code]['session_id']
            user_data = sessions.get(session_id)
            if user_data:
                del active_codes[code]
                return jsonify({"success": True, "user": user_data})
        return jsonify({"success": False, "status": "waiting"})
    return jsonify({"success": False, "status": "invalid"})

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    import threading
    threading.Thread(target=lambda: bot.polling(none_stop=True), daemon=True).start()
    # Запускаем Flask для сайта
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
