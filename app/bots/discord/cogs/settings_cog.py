from discord.ext import commands
from app.models.enums import PlatformType
from app.models.schemas import FiatCurrency
from app.services.bot_service import BotService


class SettingsCog(commands.Cog):

    PLATFORM_TYPE = PlatformType.DISCORD

    def __init__(
        self,
        bot,
        bot_service: BotService,
    ):
        self.bot = bot
        self._bot_service = bot_service

    @commands.command(name="list_fiat")
    async def _list_fiat_currencies(self, ctx: commands.Context):
        fiat_currencies: list[FiatCurrency] = self._bot_service.list_supported_fiat_currencies()
        message: str = "List of the supported currencies:\n"
        for currency in fiat_currencies:
            message += f"`{currency.short_name.upper()}` - {currency.full_name}\n"
        message += (
            "\nTo change your preferred currency, use the command:\n`/set_fiat <CURRENCY_CODE>`"
        )
        await ctx.send(message)

    @commands.command(name="set_fiat")
    async def _set_fiat_currency(self, ctx: commands.Context, input: str):
        """Set preferred fiat currency."""
        user_id: str = str(ctx.author.id)
        answer: str = self._bot_service.set_fiat_currency(
            platformType=self.PLATFORM_TYPE,
            platform_user_id=user_id,
            input=input,
        )
        await ctx.send(answer)
