from discord.ext import commands
from app.bots.discord.cogs.base import AccountCog
from app.bots.discord.custom_context import CustomContext
from app.models.enums import PlatformType
from app.services.account_lookup_service import AccountLookupService
from app.services.fiat_currency_service import FiatCurrencyService


class SettingsCog(AccountCog):

    PLATFORM_TYPE = PlatformType.DISCORD

    def __init__(
        self,
        account_lookup_service: AccountLookupService,
        fiat_currency_service: FiatCurrencyService,
    ):
        super().__init__(account_lookup_service)
        self._fiat_currency_service = fiat_currency_service

    @commands.command(name="get_fiat")
    async def _get_fiat_currency(self, ctx: CustomContext):
        answer: str = self._fiat_currency_service.get_fiat_currency(ctx.account)
        await ctx.send(answer)

    @commands.command(name="list_fiat")
    async def _list_fiat_currencies(self, ctx: CustomContext):
        message = self._fiat_currency_service.list_supported_fiat_currencies(ctx.db_session)
        await ctx.send(message)

    @commands.command(name="set_fiat")
    async def _set_fiat_currency(self, ctx: CustomContext, input: str):
        """Set preferred fiat currency."""
        answer: str = self._fiat_currency_service.set_fiat_currency(
            ctx.db_session, ctx.account, input
        )
        await ctx.send(answer)
