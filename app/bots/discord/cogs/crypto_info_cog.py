import asyncio
import discord
from discord import app_commands
from app.bots.discord.cogs.base_cog import BaseCog
from app.bots.discord.custom.custom_bot import CustomDiscordBot
from app.bots.discord.utils.autocompletes import crypto_autocomplete
from app.models.dtos import CryptoPrice
from app.services.crypto_api_service import CryptoApiService
from app.bots.constants.commands import COMMAND_INDEX, COMMAND_TOP, COMMAND_LIST
from app.bots.discord.custom.custom_interaction import get_db_session, get_account
from app.utils.functions import format_price_info


class CrpytoInfoCog(BaseCog):

    def __init__(
        self,
        bot: CustomDiscordBot,
        crypto_api_service: CryptoApiService,
    ):
        super().__init__()
        self._bot = bot
        self._crypto_api_service = crypto_api_service

    @app_commands.command(name=COMMAND_INDEX, description="Get price/index of a cryptocurrency")
    @app_commands.describe(crypto_currency_input="The type of cryptocurrency")
    @app_commands.autocomplete(crypto_currency_input=crypto_autocomplete)
    async def _index(self, interaction: discord.Interaction, crypto_currency_input: str):
        db_session = get_db_session(interaction)
        account = get_account(interaction)
        cryptocurrency = self._bot.crypto_currency_service.find_by_name_or_symbol(
            db_session, crypto_currency_input
        )
        if not cryptocurrency or not cryptocurrency.symbol:
            await interaction.followup.send(
                f"❌ Cryptocurrency '{crypto_currency_input}' not found. Please check the name or symbol and try again."
            )
            return
        crypto_symbol = cryptocurrency.symbol
        vs_currency_symbol = "EUR"
        if account and account.selected_vs_currency:
            vs_currency_symbol = account.selected_vs_currency.symbol.lower()
        try:
            price: CryptoPrice = await asyncio.wait_for(
                self._crypto_api_service.fetch_ticker_price(
                    crypto_symbol=crypto_symbol, vs_currency_symbol=vs_currency_symbol
                ),
                timeout=3.0,
            )
            answer: str = format_price_info(
                crypto_symbol=crypto_symbol,
                vs_currency_symbol=vs_currency_symbol,
                price_info=price,
            )
            await interaction.followup.send(answer)
        except asyncio.TimeoutError:
            await interaction.followup.send(
                "⏱️ Request timed out. The API took too long to respond. Please try again later."
            )

    @app_commands.command(name=COMMAND_TOP, description="Get top cryptocurrencies by market cap")
    @app_commands.describe(amount="The number of top cryptocurrencies to display (default: 10)")
    async def _top(self, interaction: discord.Interaction, amount: int = 10):
        vs_currency = "EUR"
        account = get_account(interaction)
        if account and account.selected_vs_currency:
            vs_currency = account.selected_vs_currency.symbol.lower()
        answer: str = await self._crypto_api_service.get_top_crypto_currencies_str(
            amount=amount, vs_currency=vs_currency
        )
        await interaction.followup.send(answer)

    @app_commands.command(
        name=COMMAND_LIST, description="Get list of all supported cryptocurrencies"
    )
    async def _list(self, interaction: discord.Interaction):
        db_session = get_db_session(interaction)
        answer: str = self._bot.crypto_currency_service.get_list(db_session)
        if not answer:
            answer = "❌ No cryptocurrencies found in the system.\n Please try again later."
            await interaction.followup.send(answer)
            return
        max_length = 2000  # Discord Limit
        messages = []
        current_message = ""
        for line in answer.split("\n"):
            if len(current_message) + len(line) + 1 > max_length:
                if current_message:
                    messages.append(current_message)
                current_message = line
            else:
                current_message += ("\n" if current_message else "") + line
        if current_message:
            messages.append(current_message)
        for message in messages:
            if message.strip():
                await interaction.followup.send(message)
