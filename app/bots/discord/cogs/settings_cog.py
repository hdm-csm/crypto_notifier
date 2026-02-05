from discord.ext import commands
from app.models.enums import PlatformType
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

    @commands.command(name="list_currencies")
    async def _list_currencies(self, ctx: commands.Context):
        fiat_currencies = self._bot_service.list_supported_fiat_currencies()
        message = "List of the supported currencies:\n"
        for currency in fiat_currencies:
            message += f"`{currency.short_name.upper()}` - {currency.full_name}\n"
        message += "\nTo change your preferred currency, use the command:\n`/change_currency <CURRENCY_CODE>`"
        await ctx.send(message)

    @commands.command(name="change_currency")
    async def _change_currency(self, ctx: commands.Context, input: str):
        """Change preferred fiat currency."""
        user_id = ctx.author.id
        answer = self._bot_service.set_currency(
            platformType=self.PLATFORM_TYPE,
            platform_user_id=str(user_id),
            input=input,
        )
        await ctx.send(answer)
