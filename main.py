import logging
import os
import textwrap
import time

import requests
import telegram
from dotenv import load_dotenv

from tg_logs_handler import TelegramLogsHandler


def create_logger(bot, chat_id):
    logger = logging.getLogger('Logger')
    logger.setLevel(logging.WARNING)
    logger.addHandler(TelegramLogsHandler(bot, chat_id))
    return logger


if __name__ == '__main__':
    load_dotenv()

    tg_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    devman_auth_token = os.getenv('DEVMAN_AUTH_TOKEN')
    header = {'Authorization': devman_auth_token}

    bot = telegram.Bot(token=tg_bot_token)
    logger = create_logger(bot, chat_id)

    logger.warning("Бот запущен")

    timestamp = ''

    while True:
        try:
            response = requests.get(
                'https://dvmn.org/api/long_polling/',
                params={'timestamp': timestamp},
                headers=header,
                timeout=86400,
            )
            response.raise_for_status()
            review_result = response.json()

            if review_result.get('status') == 'found':
                timestamp = review_result['new_attempts'][0]['timestamp']
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
                    bot.send_message(chat_id=chat_id, text=negative_reply)
                else:
                    bot.send_message(chat_id=chat_id, text=positive_reply)
            else:
                timestamp = review_result['timestamp_to_request']

        except requests.exceptions.ReadTimeout as ex:
            logger.exception(ex)
            continue
        except requests.exceptions.ConnectionError:
            print('Соединение с Интернетом не установлено')
            time.sleep(5)
