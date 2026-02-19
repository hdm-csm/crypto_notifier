from app.repository.vs_currency_repository import VsCurrencyRepository
from app.db import session_scope
from app.models.schemas import Account, VsCurrency
from app.services.account_lookup_service import AccountLookupService
from app.services.crypto_api_service import CryptoApiService
from app.utils.currency_mappings import get_currency_full_name
from sqlalchemy.orm import Session


class VsCurrencyService:

    def __init__(
        self,
        vs_currency_repository: VsCurrencyRepository,
        account_lookup_service: AccountLookupService,
        crypto_api_service: CryptoApiService,
    ):
        self._vs_currency_repository = vs_currency_repository
        self._account_lookup_service = account_lookup_service
        self._crypto_api_service = crypto_api_service

    async def init_vs_currencies(self):
        with session_scope() as session:
            if self._vs_currency_repository.is_empty(session):
                supported_vs_currencies_symbols = (
                    await self._crypto_api_service.get_coingecko_supported_vs_currencies()
                )
                vs_currencies = [
                    VsCurrency(symbol=symbol, name=get_currency_full_name(symbol))
                    for symbol in supported_vs_currencies_symbols
                ]
                self._vs_currency_repository.store_all(session, vs_currencies)

    def get_vs_currency(self, account: Account) -> str:
        symbol = account.selected_vs_currency.symbol.upper()
        name = account.selected_vs_currency.name
        return f"Currency: {symbol} — {name}\n\nChange with `/set_vs <code>`"

    def get_all(self, db_session: Session) -> list[VsCurrency]:
        return self._vs_currency_repository.get_all(db_session)

    def list_supported_vs_currencies(self, db_session: Session) -> str:
        vs_currencies: list[VsCurrency] = self._vs_currency_repository.get_all(session=db_session)
        lines = [f"{c.symbol.upper()} — {c.name}" for c in vs_currencies]
        message = f"Supported currencies ({len(vs_currencies)})\n\n"
        message += "\n".join(lines)
        message += "\n\nChange with `/set_vs <code>`"
        return message

    def set_vs_currency(self, db_session: Session, account: Account, input: str) -> str:
        vs_currency: VsCurrency | None = self._vs_currency_repository.find_by_symbol_or_name(
            session=db_session, input=input
        )

        if vs_currency is None:
            return f"❌ Currency '{input}' not found."

        self._vs_currency_repository.set_vs_currency(
            session=db_session, account=account, vs_currency_id=int(vs_currency.id)
        )

        return f"✅ Currency set to {vs_currency.symbol.upper()} — {vs_currency.name}."

    def find_by_symbol_or_name(self, session: Session, input: str) -> VsCurrency | None:
        return self._vs_currency_repository.find_by_symbol_or_name(session=session, input=input)
