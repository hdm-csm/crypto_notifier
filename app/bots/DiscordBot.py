from math import e
import os
import logging
import discord
from discord.ext import commands
from discord import app_commands
from app.models import PlatformType
from app.repository import account_repository
from app.repository.account_repository import AccountRepository
from app.repository.cryptocurrency_repository import CryptocurrencyRepository
from app.repository.favorite_repository import FavoriteRepository
from app.services.crypto_api_service import CryptoApiService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')
DISCORD_GUILD_ID = int(os.environ.get('DISCORD_GUILD_ID'))


class Crypto_Notifier_Cog(commands.Cog):
    def __init__(
            self, 
            platform_type: PlatformType,
            bot, 
            crypto_service: CryptoApiService,
            account_repository: AccountRepository,
            cryptocurrency_repository: CryptocurrencyRepository,
            favorite_repository: FavoriteRepository):
        self.platform_type = platform_type
        self.bot = bot
        self.crypto_service = crypto_service
        self.account_repository = account_repository
        self.cryptocurrency_repository = cryptocurrency_repository
        self.favorite_repository = favorite_repository
        self._last_member = None

    async def cog_load(self):
        """Called when the cog is loaded."""
        return await super().cog_load()

    @app_commands.command(name="index", description="Get price/index of a cryptocurrency")
    @app_commands.describe(currency="The type of cryptocurrency")
    @app_commands.guilds(discord.Object(id=DISCORD_GUILD_ID))
    async def _index(self, interaction: discord.Interaction, currency: str):
        result = await self.crypto_service.get_index(currency)
        if result is None:
            await interaction.response.send_message(f"Could not find price for {currency}")
        else:
            await interaction.response.send_message(f"{currency.capitalize()}: {result:.2f} €")


    @commands.command(name='list')
    async def _list(self, ctx: commands.Context):
        result = await self.crypto_service.list_top_crypto_currencies(amount=10)
        message = "Top 10 Cryptocurrencies by Market Cap:\n\n"
        for coin in result:
            message += f"{coin.market_cap_rank}. {coin.name} ({coin.symbol.upper()})\n"
            message += f"   Price: ${coin.current_price:.2f} €\n"
            message += f"   Market Cap: ${coin.market_cap:,} €\n\n"
        await ctx.channel.send(message)

    @commands.command(name='save_fav')
    async def _save_fav(self, ctx: commands.Context, currency: str):
        """Save cryptocurrency as favorite."""
        user_id = ctx.author.id
        input_crypto = currency.lower()

        account = self.account_repository.find_by_platform_and_id(
            platform=self.platform_type,
            platform_id=str(user_id)
        )
        if account is None:
            account = self.account_repository.create(
                platform=self.platform_type,
                platformId=str(user_id)
            )
        cryptocurrency = self.cryptocurrency_repository.find_by_name_or_symbol(input_crypto)
        if cryptocurrency is None:
            return False

        if not account:
            await ctx.send(f"⚠️ Could not find or create account for user ID {user_id}.")
            return

        if not cryptocurrency:
            await ctx.send(f"⚠️ Cryptocurrency '{input_crypto}' not found. Please check the name/symbol and try again.")
            return

        success = self.favorite_repository.add_favorite(
            account=account,
            crypto=cryptocurrency
        )
        
        if success:
            await ctx.send(f"✅ Saved {input_crypto} as your favorite cryptocurrency!")
        else:
            await ctx.send(f"⚠️ {input_crypto} is already in your favorites.")



class DiscordBot:

    PLATFORM_TYPE = PlatformType.Discord

    def __init__(
            self, 
            token: str, 
            client_id: int, 
            guild_id: int, 
            channel_id: int,
            crypto_api_service: CryptoApiService,
            account_repository: AccountRepository,
            cryptocurrency_repository: CryptocurrencyRepository,
            favorite_repository: FavoriteRepository):
        
        self.token = token
        self.client_id = client_id
        self.guild_id = guild_id # guild = server
        self.channel_id = channel_id
        self.crypto_api_service = crypto_api_service
        self.account_repository = account_repository
        self.cryptocurrency_repository = cryptocurrency_repository
        self.favorite_repository = favorite_repository

        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix='/', intents=intents)

        @self.bot.event
        async def on_ready():
            logging.info(f"Bot logged in as {self.bot.user}")
            
            # Sync app_commands to guild (no global commands)
            try:
                # First copy global commands to the guild
                # self.bot.tree.copy_global_to(guild=discord.Object(id=self.guild_id))
                # Then sync to the guild
                synced = await self.bot.tree.sync(guild=discord.Object(id=self.guild_id))
                logging.info(f"Synced {len(synced)} app_commands to guild")
            except Exception as e:
                logging.error(f"Failed to sync app_commands: {e}")

        @self.bot.event
        async def on_command_error(ctx, error):
            if isinstance(error, commands.CommandNotFound):
                await ctx.send(f"Command not found.")
            else:
                logging.error(f"Command error: {error}")

    async def start(self):        
        cog = Crypto_Notifier_Cog(
            self.PLATFORM_TYPE,
            self.bot, 
            self.crypto_api_service, 
            self.account_repository,
            self.cryptocurrency_repository,
            self.favorite_repository)
        await self.bot.add_cog(cog)
        
        # Build choices from cryptocurrency repository
        crypto_names = self.cryptocurrency_repository.get_all_cryptocurrency_names()
        choices = [
            app_commands.Choice(name=name, value=name.lower())
            for name in crypto_names[:25]  # Discord limit is 25 choices
        ]
        cog._index.choices = choices
        
        await self.bot.start(self.token)
        logging.info("DiscordBot has started!")

    async def stop(self):
        """Stop the Discord bot."""
        await self.bot.close()
