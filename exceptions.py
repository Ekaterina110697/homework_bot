class ApiError(Exception):
    """Возникла ошибка при запросе к API."""

    pass


class WrongStatusCode(Exception):
    """Получен неверный статус ошибки."""

    pass
