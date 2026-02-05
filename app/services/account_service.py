from app.models.schemas import Account
from app.repository.account_repository import AccountRepository


class AccountService:
    def __init__(self, account_repository: AccountRepository):
        self._account_repository = account_repository