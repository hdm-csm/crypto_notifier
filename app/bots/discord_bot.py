import logging
import discord
from discord.ext import commands
from app.bots.discord.cogs.settings_cog import SettingsCog
from app.bots.discord.cogs.crypto_info_cog import CrpytoInfoCog
from app.bots.discord.cogs.favorites_cog import FavoritesCog
from app.models.schemas import PlatformType
from app.services.account_lookup_service import AccountLookupService
from app.services.crypto_api_service import CryptoApiService
from app.services.favorites_service import FavoritesService
from app.services.fiat_currency_service import FiatCurrencyService


class DiscordBot:

    PLATFORM_TYPE = PlatformType.DISCORD

    def __init__(
        self,
        token: str,
        guild_id: int,
        crypto_api_service: CryptoApiService,
        favorites_service: FavoritesService,
        _account_lookup_service: AccountLookupService,
        _fiat_currency_service: FiatCurrencyService,
    ):

        self.token = token
        self.guild_id = guild_id  # guild = server
        self._crypto_api_service = crypto_api_service
        self._favorites_service = favorites_service
        self._account_lookup_service = _account_lookup_service
        self._fiat_currency_service = _fiat_currency_service

        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix="/", intents=intents)

        @self.bot.event
        async def on_ready():
            logging.info(f"Bot logged in as {self.bot.user}")

            try:
                guild_obj = discord.Object(id=self.guild_id)
                self.bot.tree.copy_global_to(guild=guild_obj)  # Takes 1 hour to register
                synced = await self.bot.tree.sync(guild=guild_obj)
                logging.info(f"Synced {len(synced)} commands to Server ID: {self.guild_id}")
            except Exception as e:
                logging.error(f"Failed to sync for guild {self.guild_id}: {e}")

        @self.bot.event
        async def on_command_error(ctx, error):
            if isinstance(error, commands.CommandNotFound):
                await ctx.send("Command not found.")
            else:
                logging.error(f"Command error: {error}")

    async def start(self):
        settings_cog = SettingsCog(
            self.bot, self._account_lookup_service, self._fiat_currency_service
        )
        crypto_info_cog = CrpytoInfoCog(self.bot, self._crypto_api_service)
        favorites_cog = FavoritesCog(
            self.bot, self._favorites_service, self._account_lookup_service
        )

        await self.bot.add_cog(settings_cog)
        await self.bot.add_cog(crypto_info_cog)
        await self.bot.add_cog(favorites_cog)

        # TODO: Make it work
        # Build choices from cryptocurrency repository
        # crypto_names = self.cryptocurrency_repository.get_all_cryptocurrency_names()
        # choices = [
        #     app_commands.Choice(name=name, value=name.lower())
        #     for name in crypto_names[:25]  # Discord limit is 25 choices
        # ]
        # cog._index.choices = choices

        try:
            await self.bot.start(self.token)
        except Exception as e:
            logging.error(f"Error starting Discord bot: {e}")

    async def stop(self):
        """Stop the Discord bot."""
        await self.bot.close()
