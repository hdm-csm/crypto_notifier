from app.models.schemas import FiatCurrency
from app.repository.cryptocurrency_repository import CryptocurrencyRepository
from app.repository.fiat_currency_repository import FiatCurrencyRepository
from app.services.crypto_api_service import CryptoApiService
from app.db import session_scope


class InitService:
    def __init__(
        self,
        fiat_currency_repository: FiatCurrencyRepository,
        cryptocurrency_repository: CryptocurrencyRepository,
        crypto_api_service: CryptoApiService,
    ):
        self._fiat_currency_repository = fiat_currency_repository
        self._cryptocurrency_repository = cryptocurrency_repository
        self._crypto_api_service = crypto_api_service
