import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from app.bots.discord.cogs.base import AccountCog
from app.bots.discord.custom_context import CustomContext
from app.services.account_lookup_service import AccountLookupService
from app.services.crypto_api_service import CryptoApiService


class CrpytoInfoCog(AccountCog):

    def __init__(
        self,
        account_lookup_service: AccountLookupService,
        crypto_api_service: CryptoApiService,
    ):
        super().__init__(account_lookup_service)
        self._crypto_api_service = crypto_api_service

    @app_commands.command(name="index", description="Get price/index of a cryptocurrency")
    @app_commands.describe(crypto_currency="The type of cryptocurrency")
    async def _index(self, interaction: discord.Interaction, crypto_currency: str):
        await interaction.response.defer()
        try:
            # Wait maximum 3 seconds for the API call
            result = await asyncio.wait_for(
                self._crypto_api_service.get_index(crypto_currency), timeout=3.0
            )
            if result is None:
                await interaction.followup.send(
                    f'Could not find price for "{crypto_currency}".\nPlease enter correct id.'
                )
            else:
                await interaction.followup.send(f"{crypto_currency.capitalize()}: {result:.2f} €")
        except asyncio.TimeoutError:
            await interaction.followup.send(
                "⏱️ Request timed out. The API took too long to respond. Please try again later."
            )

    @commands.command(name="list")
    async def _list(self, ctx: CustomContext):
        vs_currency = "eur"
        if ctx.account and ctx.account.selected_vs_currency:
            vs_currency = ctx.account.selected_vs_currency.short_name.lower()

        result = await self._crypto_api_service.list_top_crypto_currencies(
            amount=10, vs_currency=vs_currency
        )
        message = "Top 10 Cryptocurrencies by Market Cap:\n\n"
        for coin in result:
            message += f"{coin.market_cap_rank}. {coin.name} ({coin.symbol.upper()})\n"
            message += f"   Price: ${coin.current_price:.2f} €\n"
            message += f"   Market Cap: ${coin.market_cap:,} €\n"
            message += f"   Index ID: {coin.id}\n\n"
        await ctx.send(message)
