from app.repository.crypto_currency_repository import CryptocurrencyRepository
from app.repository.vs_currency_repository import VsCurrencyRepository
from app.services.crypto_api_service import CryptoApiService


class InitService:
    def __init__(
        self,
        vs_currency_repository: VsCurrencyRepository,
        cryptocurrency_repository: CryptocurrencyRepository,
        crypto_api_service: CryptoApiService,
    ):
        self._vs_currency_repository = vs_currency_repository
        self._cryptocurrency_repository = cryptocurrency_repository
        self._crypto_api_service = crypto_api_service
