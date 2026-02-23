import discord
from discord import app_commands
from app.bots.discord.cogs.base_cog import BaseCog
from app.models.enums import PlatformType
from app.services.account_lookup_service import AccountLookupService
from app.services.crypto_currency_service import CryptoCurrencyService
from app.services.favorites_service import FavoritesService
from app.bots.discord.custom.custom_interaction import get_db_session, get_account
from app.bots.constants.commands import (
    COMMAND_ADD_FAV,
    COMMAND_ADD_FAVS,
    COMMAND_LIST_FAVS,
    COMMAND_REMOVE_FAV,
    COMMAND_DROP_FAVS,
)


class FavoritesCog(BaseCog):

    PLATFORM_TYPE = PlatformType.DISCORD

    def __init__(
        self,
        account_lookup_service: AccountLookupService,
        favorites_service: FavoritesService,
        crypto_currency_service: CryptoCurrencyService,
    ):
        super().__init__(account_lookup_service, crypto_currency_service)
        self._favorites_service = favorites_service

    @app_commands.command(
        name=COMMAND_ADD_FAV, description="Add a cryptocurrency to your favorites"
    )
    @app_commands.describe(crypto_currency_input="The cryptocurrency symbol or name")
    @app_commands.autocomplete(crypto_currency_input=BaseCog.crypto_autocomplete)
    async def _add_fav(self, interaction: discord.Interaction, crypto_currency_input: str) -> None:
        """Save cryptocurrency as favorite."""
        db_session = get_db_session(interaction)
        account = get_account(interaction)
        answer = self._favorites_service.add_favorite(
            db_session=db_session, account=account, input_crypto=crypto_currency_input
        )
        await interaction.response.send_message(answer)

    @app_commands.command(
        name=COMMAND_ADD_FAVS, description="Add multiple cryptocurrencies to favorites"
    )
    @app_commands.describe(input_cryptos="Space-separated cryptocurrency symbols or names")
    async def _add_favs(self, interaction: discord.Interaction, input_cryptos: str) -> None:
        """Save multiple cryptocurrencies as favorites."""
        cryptos = input_cryptos.split()
        if not cryptos:
            await interaction.response.send_message(
                "⚠️ Please provide at least one cryptocurrency symbol or name."
            )
            return

        db_session = get_db_session(interaction)
        account = get_account(interaction)
        results = []
        for crypto in cryptos:
            result = self._favorites_service.add_favorite(
                db_session=db_session, account=account, input_crypto=crypto
            )
            results.append(result)

        await interaction.response.send_message("\n".join(results))

    @app_commands.command(name=COMMAND_LIST_FAVS, description="List your favorite cryptocurrencies")
    async def _list_favs(self, interaction: discord.Interaction) -> None:
        """List favorite cryptocurrencies."""
        account = get_account(interaction)
        answer = await self._favorites_service.list_favorites(account=account)
        await interaction.response.send_message(answer)

    @app_commands.command(
        name=COMMAND_REMOVE_FAV, description="Remove a cryptocurrency from your favorites"
    )
    @app_commands.describe(input_crypto="The cryptocurrency symbol or name")
    async def _remove_fav(self, interaction: discord.Interaction, input_crypto: str) -> None:
        """Remove cryptocurrency from favorites."""
        db_session = get_db_session(interaction)
        account = get_account(interaction)
        answer = self._favorites_service.remove_favorite(
            db_session=db_session, account=account, input_crypto=input_crypto.lower()
        )
        await interaction.response.send_message(answer)

    @app_commands.command(
        name=COMMAND_DROP_FAVS, description="Remove all your favorite cryptocurrencies"
    )
    async def _drop_favs(self, interaction: discord.Interaction) -> None:
        """Remove all favorite cryptocurrencies."""
        account = get_account(interaction)
        answer = self._favorites_service.drop_favorites(account=account)
        await interaction.response.send_message(answer)
