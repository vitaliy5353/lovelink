from flask import Flask, request, jsonify
import telebot
import random
import time
import threading
import os

# Токен будет браться из настроек Render (Environment Variable), а не из кода!
BOT_TOKEN = os.environ.get('8987546633:AAGehEF6GHQCnjWTrpYbaqf7qDXlh37LACk')
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

# Разрешаем запросы с твоего GitHub Pages сайта
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

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

# Запуск бота в фоне
def run_bot():
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print("Ошибка бота, ждем 5 сек...")
            time.sleep(5)

# Render требует, чтобы сервер слушал порт
if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)