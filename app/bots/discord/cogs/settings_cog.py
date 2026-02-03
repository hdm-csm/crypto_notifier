from discord.ext import commands
from app.services.bot_service import BotService


class SettingsCog(commands.Cog):
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
        message = "Choose one of the supported Currencies:\n"
        for currency in fiat_currencies:
            message += f"`{currency.short_name.upper()}` - {currency.full_name}\n"
        await ctx.send(message)

    # @commands.command(name="change_currency")
    # async def _change_currency(self, ctx: commands.Context, currency: str):
    #     """Change preferred fiat currency."""
    #     user_id = ctx.author.id
    #     input_currency = currency.upper()
    #     answer = self._bot_service.change_preferred_fiat_currency(
    #         platformType=self.platform_type,
    #         platform_user_id=str(user_id),
    #         input_currency=input_currency,
    #     )
    #     await ctx.send(answer)
