import logging
from discord.ext import commands
from app.bots.discord.cogs.account_cog import AccountCog
from app.bots.discord.custom_context import CustomContext
from app.db import session_scope
from app.models.enums import PlatformType
from app.models.schemas import Account
from app.services.account_lookup_service import AccountLookupService
from app.services.fiat_currency_service import FiatCurrencyService
from app.utils.exceptions import AccountNotFoundOrCreatedException


class SettingsCog(AccountCog):

    PLATFORM_TYPE = PlatformType.DISCORD

    def __init__(
        self,
        bot,
        _account_lookup_service: AccountLookupService,
        _fiat_currency_service: FiatCurrencyService,
    ):
        self.bot = bot
        self._account_lookup_service = _account_lookup_service
        self._fiat_currency_service = _fiat_currency_service

    @commands.command(name="get_fiat")
    async def _get_fiat_currency(self, ctx: CustomContext):
        # with session_scope() as session:
        #     try:
        #         account: Account = self._account_lookup_service.find_or_create_account(
        #             db_session=session,
        #             platform_type=self.PLATFORM_TYPE,
        #             platform_user_id=str(ctx.author.id),
        #         )
        #         message: str = "Your current fiat currency: "
        #         message += f"`{account.selected_fiat_currency.short_name.upper()}` - {account.selected_fiat_currency.full_name}\n"
        #         message += "\nTo change your preferred currency, use the command:\n`/set_fiat <CURRENCY_CODE>`"
        #     except AccountNotFoundOrCreatedException as e:
        #         logging.exception(str(e))
        #         return "⚠️ Account not found for user."
        #     except Exception as e:
        #         logging.error(f"Error adding favorite: {e}")
        #         return "❌ An error occurred while saving your favorite. " "Please try again later."

        answer: str = self._fiat_currency_service.get_fiat_currency(ctx.account)
        await ctx.send(answer)

    @commands.command(name="list_fiat")
    async def _list_fiat_currencies(self, ctx: CustomContext):
        message = self._fiat_currency_service.list_supported_fiat_currencies(ctx.db_session)
        await ctx.send(message)

    @commands.command(name="set_fiat")
    async def _set_fiat_currency(self, ctx: CustomContext, input: str):
        """Set preferred fiat currency."""
        # user_id: str = str(ctx.author.id)
        # answer: str = self._fiat_currency_service.set_fiat_currency(
        #     platform_type=self.PLATFORM_TYPE,
        #     platform_user_id=user_id,
        #     input=input,
        # )
        answer: str = self._fiat_currency_service.set_fiat_currency(
            ctx.db_session, ctx.account, input
        )
        await ctx.send(answer)
