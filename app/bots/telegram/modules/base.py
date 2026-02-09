from abc import ABC, abstractmethod
from telegram.ext import Application
from app.models.enums import PlatformType
from app.services.account_lookup_service import AccountLookupService


class TelegramModule(ABC):
    PLATFORM_TYPE = PlatformType.TELEGRAM
    _account_lookup_service: AccountLookupService

    def __init__(self, account_lookup_service: AccountLookupService):
        self._account_lookup_service = account_lookup_service

    @abstractmethod
    def register(self, app: Application) -> None:
        raise NotImplementedError
