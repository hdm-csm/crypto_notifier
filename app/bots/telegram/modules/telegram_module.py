from abc import ABC, abstractmethod
from telegram.ext import Application
from app.services.account_lookup_service import AccountLookupService


class TelegramModule(ABC):
    _account_lookup_service: AccountLookupService

    def __init__(self, account_lookup_service: AccountLookupService):
        self._account_lookup_service = account_lookup_service

    @abstractmethod
    def register(self, app: Application) -> None:
        raise NotImplementedError
