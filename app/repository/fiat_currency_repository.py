from sqlalchemy.orm import Session
from app.models.schemas import FiatCurrency
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
