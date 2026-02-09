import logging
from sqlalchemy.orm import Session
from app.models.schemas import Account, VsCurrency
from sqlalchemy import select, or_


class VsCurrencyRepository:

    def is_empty(self, session: Session) -> bool:
        return session.query(VsCurrency).count() == 0

    def store_all(self, session: Session, vs_currencies: list[VsCurrency]):
        session.add_all(vs_currencies)

    def find_by_short_name(self, session: Session, short_name: str) -> VsCurrency | None:
        return session.query(VsCurrency).filter(VsCurrency.short_name.ilike(short_name)).first()

    def find_by_full_or_short_name(self, session: Session, name: str) -> VsCurrency | None:
        return (
            session.query(VsCurrency)
            .filter(or_(VsCurrency.full_name.ilike(name), VsCurrency.short_name.ilike(name)))
            .first()
        )

    def find_by_full_or_short_name_2(self, session: Session, input: str) -> VsCurrency | None:
        stmt = select(VsCurrency).where(
            or_(VsCurrency.full_name.ilike(input), VsCurrency.short_name.ilike(input))
        )
        return session.execute(stmt).scalar_one_or_none()

    def list_all(self, session: Session) -> list[VsCurrency]:
        return session.query(VsCurrency).all()

    def set_vs_currency(self, session: Session, account: Account, vs_currency_id: int) -> Account:
        account.selected_vs_currency_id = vs_currency_id
        session.flush()
        logging.info(
            f"Updated vs currency for {account.platform.value} account {account.platform_user_id} to {vs_currency_id}"
        )
        return account
