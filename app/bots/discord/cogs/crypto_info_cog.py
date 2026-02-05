import discord
from discord.ext import commands
from discord import app_commands
from app.services.crypto_api_service import CryptoApiService


class CrpytoInfoCog(commands.Cog):
    def __init__(
        self,
        bot,
        crypto_api_service: CryptoApiService,
    ):
        self.bot = bot
        self._crypto_api_service = crypto_api_service

    @app_commands.command(name="index", description="Get price/index of a cryptocurrency")
    @app_commands.describe(currency="The type of cryptocurrency")
    async def _index(self, interaction: discord.Interaction, currency: str):
        result = await self._crypto_api_service.get_index(currency)
        if result is None:
            await interaction.response.send_message(
                f'Could not find price for "{currency}".\nPlease enter correct id.'
            )
        else:
            await interaction.response.send_message(f"{currency.capitalize()}: {result:.2f} €")

    @commands.command(name="list")
    async def _list(self, ctx: commands.Context):
        result = await self._crypto_api_service.list_top_crypto_currencies(amount=10)
        message = "Top 10 Cryptocurrencies by Market Cap:\n\n"
        for coin in result:
            message += f"{coin.market_cap_rank}. {coin.name} ({coin.symbol.upper()})\n"
            message += f"   Price: ${coin.current_price:.2f} €\n"
            message += f"   Market Cap: ${coin.market_cap:,} €\n"
            message += f"   Index ID: {coin.id}\n\n"
        await ctx.send(message)
