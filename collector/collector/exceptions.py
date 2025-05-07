class DryRunRollback(Exception):
    """Специальное исключение для отката транзакции в dry-run режиме."""


class EstablishmentProcessingError(Exception):
    """Исключение для ошибок, возникающих при обработке заведения."""

    default_message = "Ошибка обработки заведения."

    def __init__(self, additional: str = ""):
        message = self.default_message
        if additional:
            message += f"\n{additional}"
        super().__init__(message)


class HtmlNotLoadedError(EstablishmentProcessingError):
    default_message = "Ошибка загрузки страницы поиска заведения"


class DataExtractionError(EstablishmentProcessingError):
    default_message = "Ошибка извлечения данных заведения."


class AddEstablishmentError(EstablishmentProcessingError):
    default_message = "Ошибка при добавлении заведения"


class AddDescriptionError(EstablishmentProcessingError):
    default_message = "Ошибка при добавлении ai описания заведения"


class MessageProcessingError(Exception):
    pass
