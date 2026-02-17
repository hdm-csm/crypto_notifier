import asyncio
import logging
import discord
from discord.ext import commands
from discord import app_commands
from app.bots.discord.cogs.base import AccountCog
from app.bots.discord.custom_context import CustomContext
from app.db import session_scope
from app.services.account_lookup_service import AccountLookupService
from app.services.crypto_api_service import CryptoApiService
from app.services.crypto_currency_service import CryptoCurrencyService
from app.utils.command_constants import (
    COMMAND_INDEX,
    COMMAND_LIST,
)


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
        try:
            with session_scope() as db_session:
                account = self._account_lookup_service.find_or_create_account(
                    db_session=db_session,
                    platform_type=self.PLATFORM_TYPE,
                    platform_user_id=str(interaction.user.id),
                )
                cryptocurrency = await self._crypto_currency_service.find_by_name_or_symbol(
                    db_session, crypto_currency_input
                )
                if not cryptocurrency or not cryptocurrency.symbol:
                    await interaction.followup.send(
                        f"❌ Cryptocurrency '{crypto_currency_input}' not found. Please check the name or symbol and try again."
                    )
                    return
                vs_currency_symbol = "eur"
                if account and account.selected_vs_currency:
                    vs_currency_symbol = account.selected_vs_currency.symbol.lower()
                try:
                    # Wait maximum 3 seconds for the API call
                    answer = await asyncio.wait_for(
                        self._crypto_api_service.get_index_2(
                            crypto_symbol=cryptocurrency.symbol,
                            vs_currency_symbol=vs_currency_symbol,
                        ),
                        timeout=3.0,
                    )
                    await interaction.followup.send(answer)
                except asyncio.TimeoutError:
                    await interaction.followup.send(
                        "⏱️ Request timed out. The API took too long to respond. Please try again later."
                    )
        except Exception as e:
            logging.error(f"Command error in /index: {e}")
            await interaction.followup.send(
                f"❌ An error occurred while retrieving your account: {str(e)}"
            )
            return

    @commands.command(name=COMMAND_LIST)
    async def _list(self, ctx: CustomContext):
        vs_currency = "eur"
        if ctx.account and ctx.account.selected_vs_currency:
            vs_currency = ctx.account.selected_vs_currency.symbol.lower()
        answer: str = await self._crypto_api_service.list_top_crypto_currencies_str(
            amount=10, vs_currency=vs_currency
        )
        await ctx.send(answer)
