from app.repository.fiat_currency_repository import FiatCurrencyRepository
from app.db import session_scope
from app.models.schemas import Account, FiatCurrency
from app.services.account_lookup_service import AccountLookupService
from app.services.crypto_api_service import CryptoApiService
from app.models.currency_mappings import get_currency_full_name
from sqlalchemy.orm import Session


class FiatCurrencyService:

    def __init__(
        self,
        fiat_currency_repository: FiatCurrencyRepository,
        account_lookup_service: AccountLookupService,
        _crypto_api_service: CryptoApiService,
    ):
        self._fiat_currency_repository = fiat_currency_repository
        self._account_lookup_service = account_lookup_service
        self._crypto_api_service = _crypto_api_service

    async def init_fiat_currencies(self):
        with session_scope() as session:
            if self._fiat_currency_repository.is_empty(session):
                supported_fiat_currencies = (
                    await self._crypto_api_service.get_supported_fiat_currencies()
                )
                fiat_currencies = [
                    FiatCurrency(
                        short_name=short_name, full_name=get_currency_full_name(short_name)
                    )
                    for short_name in supported_fiat_currencies
                ]
                self._fiat_currency_repository.store_all(session, fiat_currencies)

    def get_fiat_currency(self, account: Account) -> str:
        message: str = "Your current fiat currency: "
        message += f"`{account.selected_fiat_currency.short_name.upper()}` - {account.selected_fiat_currency.full_name}\n"
        message += (
            "\nTo change your preferred currency, use the command:\n`/set_fiat <CURRENCY_CODE>`"
        )
        return message

    def list_supported_fiat_currencies(self, db_session: Session) -> str:
        fiat_currencies: list[FiatCurrency] = self._fiat_currency_repository.list_all(
            session=db_session
        )
        message: str = "List of the supported currencies:\n"
        for currency in fiat_currencies:
            message += f"`{currency.short_name.upper()}` - {currency.full_name}\n"
        message += (
            "\nTo change your preferred currency, use the command:\n`/set_fiat <CURRENCY_CODE>`"
        )
        return message

    # except Exception as e:
    #     logging.error(f"Error listing supported fiat currencies: {e}")
    #     return (
    #         "❌ An error occurred while listing supported fiat currencies. "
    #         "Please try again later."
    #     )

    def set_fiat_currency(self, db_session: Session, account: Account, input: str) -> str:
        fiat_currency: FiatCurrency | None = (
            self._fiat_currency_repository.find_by_full_or_short_name_2(
                session=db_session, input=input
            )
        )

        if fiat_currency is None:
            return f"⚠️ Currency '{input}' not found. " "Please check the name/symbol and try again."

        self._fiat_currency_repository.set_fiat_currency(
            session=db_session, account=account, fiat_currency_id=int(fiat_currency.id)
        )

        return f"✅ Saved {input} as your preferred currency!"

        # except AccountNotFoundOrCreatedException as e:
        #     logging.exception(str(e))
        #     return "⚠️ Account not found for user."
        # except Exception as e:
        #     logging.error(f"Error changing currency: {e}")
        #     return (
        #         "❌ An error occurred while saving your preferred currency. "
        #         "Please try again later."
        #     )
