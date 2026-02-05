import logging
from sqlalchemy.orm import Session
from app.models.schemas import Account, FiatCurrency
from sqlalchemy import or_


class FiatCurrencyRepository:

    def is_empty(self, session: Session) -> bool:
        return session.query(FiatCurrency).count() == 0

    def store_all(self, session: Session, fiat_currencies: list[FiatCurrency]):
        session.add_all(fiat_currencies)

    def find_by_short_name(self, session: Session, short_name: str) -> FiatCurrency | None:
        return session.query(FiatCurrency).filter(FiatCurrency.short_name.ilike(short_name)).first()

    def find_by_full_or_short_name(self, session: Session, name: str) -> FiatCurrency | None:
        return (
            session.query(FiatCurrency)
            .filter(or_(FiatCurrency.full_name.ilike(name), FiatCurrency.short_name.ilike(name)))
            .first()
        )

    def list_all(self, session: Session) -> list[FiatCurrency]:
        return session.query(FiatCurrency).all()

    def set_fiat_currency(
        self, session: Session, account: Account, fiat_currency_id: int
    ) -> Account:
        account.selected_fiat_currency_id = fiat_currency_id
        session.flush()
        logging.info(
            f"Updated fiat currency for {account.platform.value} account {account.platform_user_id} to {fiat_currency_id}"
        )
        return account
