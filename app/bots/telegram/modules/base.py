from abc import ABC, abstractmethod
from telegram.ext import Application
from app.models.enums import PlatformType
from app.services.account_lookup_service import AccountLookupService


class AccountModule(ABC):
    PLATFORM_TYPE = PlatformType.TELEGRAM
    _account_lookup_service: AccountLookupService

    def __init__(self, app: Application, account_lookup_service: AccountLookupService):
        self._app = app
        self._account_lookup_service = account_lookup_service

    @abstractmethod
    def register(self) -> None:
        raise NotImplementedError

    def register_jobs(self) -> None:
        """Optional: override to register background jobs."""
        pass
