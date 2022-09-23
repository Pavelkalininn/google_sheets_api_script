import logging
import os
import sys
import time

import httplib2
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from telegram import TelegramError, Bot
from googleapiclient.discovery import build

from exceptions import UpdateException

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_TIME = 1

SHEET_ID = '10_vODw5byy8hyfke448_eqQUlgiV1KSbF-VHZR7I-EA'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


def send_message(bot, message):
    """Отправляет сообщение в телеграм."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
    except TelegramError as error:
        logger.error(error, exc_info=True)


def get_api_answer():
    """Возвращает API ответ от Google sheets."""
    return get_service_sacc().spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range="Лист1!A1:Z999"
    ).execute()


def check_response(response):
    """Извлекает из словаря ответа сервера список заказов."""
    if not isinstance(response, dict):
        raise TypeError('Ответ response не в формате dict')
    data = response.get('values')
    if not isinstance(data, list):
        raise UpdateException('По ключу values пришел не список')
    return data


def check_tokens():
    """Проверка наличия констант в переменных окружения."""
    if (
            TELEGRAM_TOKEN
            and TELEGRAM_CHAT_ID
            and os.path.exists(os.path.dirname(__file__) + "/secret.json")
    ):
        return True


def get_service_sacc():
    creds_json = os.path.dirname(__file__) + "/secret.json"
    creds_service = ServiceAccountCredentials.from_json_keyfile_name(
        creds_json,
        SCOPES
    ).authorize(httplib2.Http())
    return build('sheets', 'v4', http=creds_service)


def main():
    """Основная логика работы программы."""
    logger.info('Запуск')
    if not check_tokens():
        logger.critical(
            'Отсутствуют переменные окружения и/или файл secret.json.'
        )
        raise UpdateException(
            'Программа принудительно остановлена. Отсутствуют переменные'
            ' окружения и/или файл secret.json.'
        )

    bot = Bot(token=TELEGRAM_TOKEN)

    while True:
        try:
            response = check_response(get_api_answer())
            print(response)
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.error(message, exc_info=True)
            time.sleep(RETRY_TIME)
        else:
            logger.debug(
                "Цикл обновления завершен без ошибок")


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(handler)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    main()
