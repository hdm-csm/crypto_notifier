import discord
from discord import app_commands
from app.bots.discord.cogs.base_cog import BaseCog
from app.bots.discord.utils.autocompletes import crypto_autocomplete
from app.models.enums import PlatformType
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
        favorites_service: FavoritesService,
    ):
        super().__init__()
        self._favorites_service = favorites_service

    @app_commands.command(
        name=COMMAND_ADD_FAV, description="Add a cryptocurrency to your favorites"
    )
    @app_commands.describe(crypto_currency_input="The cryptocurrency symbol or name")
    @app_commands.autocomplete(crypto_currency_input=crypto_autocomplete)
    async def _add_fav(self, interaction: discord.Interaction, crypto_currency_input: str) -> None:
        """Save cryptocurrency as favorite."""
        db_session = get_db_session(interaction)
        account = get_account(interaction)
        answer = self._favorites_service.add_favorite(
            db_session=db_session, account=account, input_crypto=crypto_currency_input
        )
        await interaction.followup.send(answer)

    @app_commands.command(
        name=COMMAND_ADD_FAVS, description="Add multiple cryptocurrencies to favorites"
    )
    @app_commands.describe(
        crypto1="First crypto",
        crypto2="Second crypto (optional)",
        crypto3="Third crypto (optional)",
        crypto4="Fourth crypto (optional)",
        crypto5="Fifth crypto (optional)",
    )
    # Apply your existing single-crypto autocomplete to all of them
    @app_commands.autocomplete(
        crypto1=crypto_autocomplete,
        crypto2=crypto_autocomplete,
        crypto3=crypto_autocomplete,
        crypto4=crypto_autocomplete,
        crypto5=crypto_autocomplete,
    )
    async def _add_favs(
        self,
        interaction: discord.Interaction,
        crypto1: str,
        crypto2: str = "",
        crypto3: str = "",
        crypto4: str = "",
        crypto5: str = "",
    ) -> None:
        """Save multiple cryptocurrencies as favorites."""
        cryptos = [c for c in [crypto1, crypto2, crypto3, crypto4, crypto5] if c.strip()]
        if not cryptos:
            await interaction.followup.send(
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

        await interaction.followup.send("\n".join(results))

    @app_commands.command(name=COMMAND_LIST_FAVS, description="List your favorite cryptocurrencies")
    async def _list_favs(self, interaction: discord.Interaction) -> None:
        """List favorite cryptocurrencies."""
        account = get_account(interaction)
        answer = await self._favorites_service.list_favorites(account=account)
        await interaction.followup.send(answer)

    @app_commands.command(
        name=COMMAND_REMOVE_FAV, description="Remove a cryptocurrency from your favorites"
    )
    @app_commands.describe(crypto_currency_input="The cryptocurrency symbol or name")
    @app_commands.autocomplete(crypto_currency_input=crypto_autocomplete)
    async def _remove_fav(
        self, interaction: discord.Interaction, crypto_currency_input: str
    ) -> None:
        """Remove cryptocurrency from favorites."""
        db_session = get_db_session(interaction)
        account = get_account(interaction)
        answer = self._favorites_service.remove_favorite(
            db_session=db_session, account=account, input_crypto=crypto_currency_input.lower()
        )
        await interaction.followup.send(answer)

    @app_commands.command(
        name=COMMAND_DROP_FAVS, description="Remove all your favorite cryptocurrencies"
    )
    async def _drop_favs(self, interaction: discord.Interaction) -> None:
        """Remove all favorite cryptocurrencies."""
        account = get_account(interaction)
        answer = self._favorites_service.drop_favorites(account=account)
        await interaction.followup.send(answer)
