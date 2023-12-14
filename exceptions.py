
class EmptyResponseFromAPI(Exception):
    """Пустой ответ от API."""

    pass


class ApiError(Exception):
    """Возникла ошибка при запросе к API."""

    pass


class WrongStatusCode(Exception):
    """Получен неверный статус ошибки."""

    pass


class StrangeStatus(Exception):
    """Исключение при получении неустановленного статуса домашней работы."""

    pass
