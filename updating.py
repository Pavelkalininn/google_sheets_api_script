import logging
import os
import sys
import time
import asyncio
from datetime import datetime, timedelta
from re import match

import httplib2
import psycopg2
import requests
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from telebot.async_telebot import AsyncTeleBot, ExceptionHandler
from googleapiclient.discovery import build

from exceptions import UpdateException, CriticalException

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_NAME = os.getenv("POSTGRES_NAME")
RETRY_TIME = 1

SHEET_ID = '10_vODw5byy8hyfke448_eqQUlgiV1KSbF-VHZR7I-EA'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
COURSE_ENDPOINT = 'https://www.cbr.ru/scripts/XML_daily.asp'
CREDENTIALS_JSON = "secret.json"


async def send_message(bot, message):
    """Отправляет сообщение в телеграм."""
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message
    )


def get_api_answer():
    """Возвращает API ответ от Google sheets."""
    return get_service_credential().spreadsheets().values().get(
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
            and os.path.exists(CREDENTIALS_JSON)
            and POSTGRES_NAME
            and POSTGRES_USER
            and POSTGRES_HOST
            and POSTGRES_PORT
            and POSTGRES_PASSWORD
    ):
        return True


def get_service_credential():
    """Авторизация сервисного аккаунта."""
    credential_service = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIALS_JSON,
        SCOPES
    ).authorize(httplib2.Http())
    return build('sheets', 'v4', http=credential_service)


async def send_overdue_orders(bot, orders):
    """Оповещение о просроченных заказах."""
    overdue_orders_id = []
    for order in orders:
        if datetime.strptime(order[3], '%d.%m.%Y') < datetime.today():
            overdue_orders_id.append(order[0])
    await send_message(bot, f'Заказ(-ы) {overdue_orders_id} просрочен(-ы)')


def get_course():
    """Запрос курса валюты с эндпоинта ЦБ."""
    try:
        response = requests.get(COURSE_ENDPOINT)
    except ConnectionError as exception:
        raise UpdateException(
            f'Ошибка получения данных с сайта ЦБ: {exception}'
        )
    if response.status_code != 200:
        raise UpdateException(
            'С сайта ЦБ пришел некорректный ответ (статус не ОК)'
        )
    if not response.text:
        raise UpdateException(
            'С сайта ЦБ пришел некорректный ответ (отсутствует текст в ответе)'
        )
    course_text = response.text.split(
        '<Name>Доллар США</Name><Value>'
    )[-1].split(
        '</Value>'
    )[0].replace(',', '.')
    if not match(r'^\d+?.\d+?$', course_text):
        raise UpdateException(
            'С сайта ЦБ пришел некорректный ответ'
            ' (курс валют не в формате десятичной дроби)'
        )
    return float(course_text)


def db_connection():
    """Соединение с БД."""
    try:
        return psycopg2.connect(
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_NAME
        )

    except psycopg2.Error as error:
        raise UpdateException(
            f'Ошибка подключения к БД: {error}'
        )


def db_update(orders_data: list) -> None:
    """Добавить список значений в БД, при наличии в БД такого order id
    обнавляет все значения в БД на значения из списка."""
    try:
        connection = db_connection()
        cursor = connection.cursor()
        create_table = (
            'CREATE TABLE IF NOT EXISTS orders '
            '(id INTEGER PRIMARY KEY, '
            'order_num INTEGER, '
            'costs_in_usd INTEGER, '
            'delivery_time DATA, '
            'costs_in_rubles REAL)'
        )
        cursor.execute(create_table)
        cursor.execute('DELETE FROM orders *')
        cursor.executemany(
            f"""INSERT INTO orders VALUES (%s, %s, %s, %s, %s);""",
            orders_data
        )
        connection.commit()
    except psycopg2.Error as error:
        logging.error(error, exc_info=True)
    finally:
        if connection:
            cursor.close()
            connection.close()


async def main():
    """Основная логика работы программы."""
    logging.info('Запуск')
    if not check_tokens():
        raise CriticalException(
            'Программа принудительно остановлена. Отсутствуют переменные'
            ' окружения и/или файл secret.json.'
        )
    overdue_orders_send_date = datetime.today().date() - timedelta(1)
    bot = AsyncTeleBot(TELEGRAM_TOKEN, exception_handler=ExceptionHandler())

    while True:
        try:
            orders = check_response(get_api_answer())[1:]
            course = get_course()
            crashed_data = []
            if orders:
                datetime_now = datetime.today()
                for order in orders:
                    if len(order) > 2 and order[0] and order[1] and order[2]:
                        order_cost = order[2]
                        if order_cost.isnumeric():
                            order.append(int(order[2]) * course)
                    else:
                        crashed_data.append(order)
                for crash_order in crashed_data:
                    orders.remove(crash_order)
                if (
                        datetime_now.date() > overdue_orders_send_date
                        and datetime_now.time().hour > 10
                ):
                    await send_overdue_orders(bot, orders)
                    overdue_orders_send_date = datetime.today().date()
                db_update(orders)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            await send_message(bot, message)
            logging.error(message, exc_info=True)
            time.sleep(RETRY_TIME)
        else:
            logging.debug(
                "Цикл обновления завершен без ошибок"
            )


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        handlers=[logging.StreamHandler(sys.stdout), ],
        format=f'%(asctime)s, %(levelname)s, %(message)s, %(name)s')
    asyncio.run(main())
