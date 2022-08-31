import os
import textwrap
import time

import requests
import telegram
from dotenv import load_dotenv

if __name__ == '__main__':
    load_dotenv()

    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    DEVMAN_AUTH_TOKEN = os.getenv('DEVMAN_AUTH_TOKEN')
    header = {'Authorization': DEVMAN_AUTH_TOKEN}

    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

    review_result = None
    timestamp = ''

    while True:
        if review_result:
            timestamp = review_result['new_attempts'][0]['timestamp']
        try:
            response = requests.get(
                'https://dvmn.org/api/long_polling/',
                params={'timestamp': timestamp},
                headers=header,
                timeout=60,
            )
            response.raise_for_status()
            review_result = response.json()
            lesson_title = review_result['new_attempts'][0]['lesson_title']
            lesson_url = review_result['new_attempts'][0]['lesson_url']
            is_negative = review_result['new_attempts'][0]['is_negative']

            negative_reply = textwrap.dedent(f'''
            Преподаватель проверил работу «{lesson_title}» {lesson_url}

            К сожалению в работе нашлись ошибки.
            ''')
            positive_reply = textwrap.dedent(f'''
            Преподаватель проверил работу «{lesson_title}» {lesson_url}

            Преподавателю всё понравилось, можно приступать к следующему уроку!
            ''')

            if is_negative:
                bot.send_message(chat_id=chat_id,
                                 text=negative_reply)
            else:
                bot.send_message(chat_id=chat_id,
                                 text=positive_reply)

        except requests.exceptions.ReadTimeout:
            print('Время ожидание вышло. Посылаю ещё один запрос')
        except requests.exceptions.ConnectionError:
            print('Соединение с Интернетом не установлено')
            time.sleep(5)
