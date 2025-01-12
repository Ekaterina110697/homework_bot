### Telegram-bot

Бот для проверки статуса домашней работы.

Бот осуществляет проверяет статус отправленной на ревью домашней работы с заданным интервалом.
При обновлении статуса анализирует ответ API и отправлять соответствующее уведомление в Telegram.

### Технологии:
- Python
- python-dotenv 
- python-telegram-bot 

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:Ekaterina110697/homework_bot.git
```

```
cd homework_bot
```

Cоздать и активировать виртуальное окружение:

```
python -m venv env
```

```
source venv\Scripts\activate  
```

Установить зависимости из файла requirements.txt:

```
python -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Записать в переменные окружения (файл .env) необходимые ключи:
- токен профиля на Яндекс.Практикуме
- токен телеграм-бота
- свой ID в телеграме


Запустить проект:

```
python homework.py
```
