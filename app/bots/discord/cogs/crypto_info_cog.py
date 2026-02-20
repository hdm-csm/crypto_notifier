import asyncio
from typing import Dict, List
import discord
from discord import app_commands
from app.bots.discord.cogs.base import AccountCog
from app.db import session_scope
from app.models.schemas import Cryptocurrency
from app.services.account_lookup_service import AccountLookupService
from app.services.crypto_api_service import CryptoApiService
from app.services.crypto_currency_service import CryptoCurrencyService
from app.utils.command_constants import COMMAND_INDEX, COMMAND_TOP, COMMAND_LIST
from app.bots.discord.custom_interaction import get_db_session, get_account


class CrpytoInfoCog(AccountCog):

    def __init__(
        self,
        account_lookup_service: AccountLookupService,
        crypto_api_service: CryptoApiService,
        crypto_currency_service: CryptoCurrencyService,
    ):
        super().__init__(account_lookup_service)
        self._account_lookup_service = account_lookup_service
        self._crypto_api_service = crypto_api_service
        self._crypto_currency_service = crypto_currency_service

    @app_commands.command(name=COMMAND_INDEX, description="Get price/index of a cryptocurrency")
    @app_commands.describe(crypto_currency_input="The type of cryptocurrency")
    async def _index(self, interaction: discord.Interaction, crypto_currency_input: str):
        await interaction.response.defer()

        # account = getattr(interaction, "account", None)
        # db_session = getattr(interaction, "db_session", None)
        db_session = get_db_session(interaction)
        account = get_account(interaction)

        cryptocurrency = self._crypto_currency_service.find_by_name_or_symbol(
            db_session, crypto_currency_input
        )
        if not cryptocurrency or not cryptocurrency.symbol:
            await interaction.followup.send(
                f"❌ Cryptocurrency '{crypto_currency_input}' not found. Please check the name or symbol and try again."
            )
            return
        vs_currency_symbol = "EUR"
        if account and account.selected_vs_currency:
            vs_currency_symbol = account.selected_vs_currency.symbol.lower()
        try:
            # Wait maximum 3 seconds for the API call
            # ticker = f"{cryptocurrency.symbol.upper()}-{vs_currency_symbol.upper()}"
            price: str = await asyncio.wait_for(
                # self._crypto_api_service.get_index(
                #     crypto_symbol=cryptocurrency.symbol,
                #     vs_currency_symbol=vs_currency_symbol,
                # ),
                self._crypto_api_service.fetch_formatted_ticker_price(
                    cryptocurrency.symbol, vs_currency_symbol
                ),
                timeout=3.0,
            )
            if not price:
                await interaction.followup.send(
                    f"❌ No price data found for {cryptocurrency.symbol.upper()} in {vs_currency_symbol.upper()}."
                )
                return
            else:
                await interaction.followup.send(price)
        except asyncio.TimeoutError:
            await interaction.followup.send(
                "⏱️ Request timed out. The API took too long to respond. Please try again later."
            )

    @_index.autocomplete("crypto_currency_input")
    async def _index_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        with session_scope() as db_session:
            all_cryptos: list[Cryptocurrency] = self._crypto_currency_service.get_all(db_session)
            filtered = [
                c
                for c in all_cryptos
                if current.lower() in c.symbol.lower() or current.lower() in c.name.lower()
            ]
            return [app_commands.Choice(name=c.name, value=c.symbol) for c in filtered][:25]

    @app_commands.command(name=COMMAND_TOP, description="Get top cryptocurrencies by market cap")
    @app_commands.describe(amount="The number of top cryptocurrencies to display (default: 10)")
    async def _top(self, interaction: discord.Interaction, amount: int):
        await interaction.response.defer()
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
        await interaction.response.defer()
        db_session = get_db_session(interaction)
        answer: str = self._crypto_currency_service.get_list(db_session)
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
