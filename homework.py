import time
import logging
import sys
import os
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (WrongStatusCode, ApiError)

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TOKENS = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
NO_TOKEN_MESSAGE = ('Программа  была принудительно остановлена. '
                    'Отсутствует: {token}')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка доступности переменных окружения."""
    missed_tokens = [token for token in TOKENS if not globals()[token]]
    if missed_tokens:
        logging.critical(NO_TOKEN_MESSAGE.format(token=missed_tokens))
        raise ValueError(NO_TOKEN_MESSAGE.format(token=missed_tokens))


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    logging.debug('Начало отправки')
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f'Сообщение отправлено {message}')
    except Exception as error:
        logging.error(error)


def get_api_answer(timestamp):
    """Отправка запроса к эндпоинту API-сервиса."""
    params = {'from_date': timestamp}
    logging.info(f'Отправка запроса на {ENDPOINT} с параметрами {params}')
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        logging.info('Ответ на запрос к API получен')
    except requests.RequestException as error:
        raise ApiError(f'Возникла ошибка {error} при запросе к API')
    if response.status_code != HTTPStatus.OK:
        raise WrongStatusCode(f'Ошибка {response.status_code}')
    return response.json()


def check_response(response):
    """Проверить валидность ответа."""
    logging.debug('Начало проверки')
    if not isinstance(response, dict):
        raise TypeError(f'{response} не является dict')
    if 'homeworks' not in response:
        raise KeyError('Нет ключа homeworks')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError(f'{homeworks} не является list')


def parse_status(homework):
    """Распарсить ответ."""
    logging.info('Начинаем проверку статуса домашней работы!')
    if 'homework_name' not in homework:
        logging.error('В ответе отсутсвует ключ')
        raise KeyError('В ответе отсутсвует ключ homework_name')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        logging.error('Неизвестный статус работы')
        raise ValueError(f'Неизвестный статус работы - {homework_status}')
    logging.info('Проверка статуса домашней работы успешна!')
    return (
        'Изменился статус проверки работы "{homework_name}". {verdict}'
    ).format(
        homework_name=homework_name,
        verdict=HOMEWORK_VERDICTS[homework_status]
    )


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    send_message(bot, 'Я включился, отслеживаю изменения.')
    last_message = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homeworks = response['homeworks']
            if homeworks == 0:
                logging.debug('Домашних работ нет.')
                continue
            if homeworks:
                message = parse_status(homeworks[0])
                if last_message != message:
                    send_message(bot, message)
                    last_message = message
            timestamp = response.get('current_date', timestamp)

        except telegram.error.TelegramError as error:
            logging.error(f'Не удалось отправить сообщение {error}')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(f'Сбой в работе программы: {error}')
            if last_message != message:
                send_message(bot, message)
                last_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format=(
            '%(asctime)s - %(levelname)s - %(name)s'
            '- %(funcName)s - %(lineno)d - %(message)s'
        ),
        handlers=[logging.FileHandler('my_logging.log'),
                  logging.StreamHandler(sys.stdout)])
    main()
