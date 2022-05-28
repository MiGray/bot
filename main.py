import os
import telebot
import logging
import psycopg2
#from config import *
from flask import Flask, request

BOTTOKEN = os.environ.get('BOT_TOKEN', None)
DBURI = os.environ.get('DB_URI', None)
APPURL = os.environ.get('APP_URL', None)


bot = telebot.TeleBot(BOTTOKEN)
server = Flask(__name__)
logger = telebot.logger
logger.setLevel(logging.DEBUG)


db_connection = psycopg2.connect(DBURI, sslmode="require")
db_object = db_connection.cursor()


def update_message_count(user_id):
    db_object.execute(f"UPDATE users SET messages = messages + 1 WHERE id = {user_id}")
    db_connection.commit()


@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    bot.reply_to(message, f"Привет, {username}!")

    db_object.execute(f"SELECT id FROM users WHERE id = {user_id}")
    result = db_object.fetchone()

    if not result:
        db_object.execute("INSERT INTO users(id, username, messages) VALUES (%s, %s, %s)", (user_id, username, 0))
        db_connection.commit()

    update_message_count(user_id)

@bot.message_handler(func=lambda messaage: True, content_types=["text"])
def message_from_user(message):
    user_id = message.from_user.id
    update_message_count(user_id)


@server.route(f"/{BOTTOKEN}", methods=["POST"])
def redirect_message():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=APPURL)
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
