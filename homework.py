import time
import logging
import sys
import os
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (WrongStatusCode, StrangeStatus,
                        ApiError, EmptyResponseFromAPI)

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[logging.FileHandler('my_logging.log'),
              logging.StreamHandler(sys.stdout)])


def check_tokens():
    """Проверка доступности переменных окружения."""
    return all([TELEGRAM_TOKEN, PRACTICUM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    logging.debug('Начало отправки')
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f'Сообщение отправлено {message}')
    except telegram.error.TelegramError as error:
        logging.error(f'Не удалось отправить сообщение {error}')


def get_api_answer(timestamp):
    """Отправка запроса к эндпоинту API-сервиса."""
    params = {'from_date': timestamp}
    logging.info(f'Отправка запроса на {ENDPOINT} с параметрами {params}')
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        logging.info('Ответ на запрос к API получен')
        if response.status_code != HTTPStatus.OK:
            logging.error('Эндопоинт недоступен')
            raise WrongStatusCode('Получен статус отличный от 200')
    except Exception:
        logging.error('Эндопоинт недоступен')
        raise ApiError('Возникла ошибка при запросе к API')

    return response.json()


def check_response(response):
    """Проверить валидность ответа."""
    logging.debug('Начало проверки')
    if not isinstance(response, dict):
        raise TypeError('Ошибка в типе ответа API')
    if 'homeworks' not in response or 'current_date' not in response:
        raise EmptyResponseFromAPI('Пустой ответ от API')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Homeworks не является списком')
    return homeworks


def parse_status(homework):
    """Распарсить ответ."""
    if 'homework_name' not in homework:
        logging.error('В ответе отсутсвует ключ')
        raise KeyError('В ответе отсутсвует ключ homework_name')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        logging.error('Неизвестный статус работы')
        raise StrangeStatus(f'Неизвестный статус работы - {homework_status}')
    return (
        'Изменился статус проверки работы "{homework_name}" {verdict}'
    ).format(
        homework_name=homework_name,
        verdict=HOMEWORK_VERDICTS[homework_status]
    )


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical(
            'Отсутствуют токены.' 'Программа была принудительно остановлена.'
        )
        sys.exit('Нехватка токенов.')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    send_message(bot, 'Я включился, отслеживаю изменения.')
    last_message = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if len(homeworks) == 0:
                logging.debug('Домашних работ нет.')
                send_message(bot, 'Изменений нет.')
                break
            for homework in homeworks:
                message = parse_status(homework)
                if last_message != message:
                    send_message(bot, message)
                    last_message = message
            timestamp = response.get('current_date')

        except Exception as error:
            if last_message != message:
                message = f'Сбой в работе программы: {error}'
                send_message(bot, message)
                last_message = message
        else:
            last_message = ''
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':

    main()
