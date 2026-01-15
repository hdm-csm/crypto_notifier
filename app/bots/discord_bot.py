import logging
import discord
from discord.ext import commands
from discord import app_commands
from config import Config
from app.models import PlatformType
from app.services.bot_service import BotService
from app.services.crypto_api_service import CryptoApiService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(threadName)s - %(levelname)s - %(message)s",
)
# TODO: Load dynamically
DISCORD_GUILD_ID = Config.DISCORD_GUILD_ID


class Crypto_Notifier_Cog(commands.Cog):
    def __init__(
        self,
        platform_type: PlatformType,
        bot,
        bot_service: BotService,
        crypto_api_service: CryptoApiService,
    ):
        self.platform_type = platform_type
        self.bot = bot
        self._bot_service = bot_service
        self._crypto_api_service = crypto_api_service

    # @commands.Cog.listener()
    # async def on_ready(self):
    #     logging.info("Crypto_Notifier_Cog: Syncing for guilds...")
    #     for guild_id in DISCORD_GUILD_IDS:
    #         guild_obj = discord.Object(id=guild_id)
    #         self.bot.tree.copy_global_to(guild=guild_obj)
    #         await self.bot.tree.sync(guild=guild_obj)

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

    @commands.command(name="add_fav")
    async def _add_fav(self, ctx: commands.Context, currency: str):
        """Save cryptocurrency as favorite."""
        user_id = ctx.author.id
        input_crypto = currency.lower()
        answer = self._bot_service.add_favorite(
            platformType=self.platform_type,
            user_id=str(user_id),
            input_crypto=input_crypto,
        )
        await ctx.send(answer)

    @commands.command(name="remove_fav")
    async def _remove_fav(self, ctx: commands.Context, currency: str):
        """Remove cryptocurrency from favorites."""
        user_id = ctx.author.id
        input_crypto = currency.lower()
        answer = self._bot_service.remove_favorite(
            platformType=self.platform_type,
            user_id=str(user_id),
            input_crypto=input_crypto,
        )
        await ctx.send(answer)

    @commands.command(name="list_favs")
    async def _list_favs(self, ctx: commands.Context):
        """List favorite cryptocurrencies."""
        user_id = ctx.author.id
        answer = await self._bot_service.list_favorites(
            platformType=self.platform_type,
            user_id=str(user_id),
        )
        await ctx.send(answer)

    @commands.command(name="drop_favs")
    async def _drop_favs(self, ctx: commands.Context):
        """Remove all favorite cryptocurrencies."""
        user_id = ctx.author.id
        answer = self._bot_service.drop_favorites(
            platformType=self.platform_type,
            user_id=str(user_id),
        )
        await ctx.send(answer)


class DiscordBot:

    PLATFORM_TYPE = PlatformType.Discord

    def __init__(
        self,
        token: str,
        guild_id: int,
        bot_service: BotService,
        crypto_api_service: CryptoApiService,
    ):

        self.token = token
        self.guild_id = guild_id  # guild = server
        self._bot_service = bot_service
        self._crypto_api_service = crypto_api_service

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
        cog = Crypto_Notifier_Cog(
            self.PLATFORM_TYPE, self.bot, self._bot_service, self._crypto_api_service
        )
        await self.bot.add_cog(cog)

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
