from discord.ext import commands
from app.bots.discord.cogs.base import AccountCog
from app.bots.discord.custom_context import CustomContext
from app.models.enums import PlatformType
from app.services.account_lookup_service import AccountLookupService
from app.services.vs_currency_service import VsCurrencyService
from app.utils.command_constants import (
    COMMAND_GET_VS,
    COMMAND_LIST_VS,
    COMMAND_SET_VS,
)


class SettingsCog(AccountCog):

    PLATFORM_TYPE = PlatformType.DISCORD

    def __init__(
        self,
        account_lookup_service: AccountLookupService,
        vs_currency_service: VsCurrencyService,
    ):
        super().__init__(account_lookup_service)
        self._vs_currency_service = vs_currency_service

    @commands.command(name=COMMAND_GET_VS)
    async def _get_vs_currency(self, ctx: CustomContext):
        answer: str = self._vs_currency_service.get_vs_currency(ctx.account)
        await ctx.send(answer)

    @commands.command(name=COMMAND_LIST_VS)
    async def _list_vs_currencies(self, ctx: CustomContext):
        message = self._vs_currency_service.list_supported_vs_currencies(ctx.db_session)
        await ctx.send(message)

    @commands.command(name=COMMAND_SET_VS)
    async def _set_vs_currency(self, ctx: CustomContext, input: str):
        """Set preferred vs currency."""
        answer: str = self._vs_currency_service.set_vs_currency(ctx.db_session, ctx.account, input)
        await ctx.send(answer)
