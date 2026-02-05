from discord.ext import commands
from app.db import session_scope
from app.models.enums import PlatformType
from app.models.schemas import Account, FiatCurrency
from app.services.account_lookup_service import AccountLookupService
from app.services.fiat_currency_service import FiatCurrencyService


class SettingsCog(commands.Cog):

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
    async def _get_fiat_currency(self, ctx: commands.Context):
        with session_scope() as session:
            account: Account = self._account_lookup_service.find_or_create_account(
                session=session,
                platform_type=self.PLATFORM_TYPE,
                platform_user_id=str(ctx.author.id),
            )
        message: str = "Your current fiat currency: "
        message += f"`{account.selected_fiat_currency.short_name.upper()}` - {account.selected_fiat_currency.full_name}\n"
        message += (
            "\nTo change your preferred currency, use the command:\n`/set_fiat <CURRENCY_CODE>`"
        )
        await ctx.send(message)

    @commands.command(name="list_fiat")
    async def _list_fiat_currencies(self, ctx: commands.Context):
        message = self._fiat_currency_service.list_supported_fiat_currencies()
        await ctx.send(message)

    @commands.command(name="set_fiat")
    async def _set_fiat_currency(self, ctx: commands.Context, input: str):
        """Set preferred fiat currency."""
        user_id: str = str(ctx.author.id)
        answer: str = self._bot_service.set_fiat_currency(
            platform_type=self.PLATFORM_TYPE,
            platform_user_id=user_id,
            input=input,
        )
        await ctx.send(answer)
