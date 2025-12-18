import os
import logging
import json
import asyncio
import httpx
import discord
from discord.ext import commands
from discord import app_commands

import app
from app.services.DataService import DataService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')
DISCORD_GUILD_ID = int(os.environ.get('DISCORD_GUILD_ID'))


class Crypto_Notifier(commands.Cog):
    def __init__(self, bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        self._last_member = None

    @commands.command(name='echo')
    async def _echo(self, ctx: commands.Context, *, arg: str):
        await ctx.channel.send(f"You said: {arg}")

    @commands.command(name='index')
    async def _index(self, ctx: commands.Context, *, arg: str):
        if not arg:
            await ctx.channel.send("Please provide a cryptocurrency name. Usage: /index btc")
            return
        result = await DataService.get_index(arg)
        if result is None:
            await ctx.channel.send(f"Could not find price for {arg}")
        else:
            await ctx.channel.send(f"{arg.capitalize()}: {result:.2f} €")

    @app_commands.command(name="index2", description="Get price/index of a cryptocurrency")
    @app_commands.describe(currency="The type of cryptocurrency")
    @app_commands.choices(currency=[
        app_commands.Choice(name="Bitcoin", value="bitcoin"),
        app_commands.Choice(name="Ethereum", value="ethereum"),
        app_commands.Choice(name="Litecoin", value="litecoin")
    ])
    async def _index2(self, interaction: discord.Interaction, currency: str):
        result = await DataService.get_index(currency)
        if result is None:
            await interaction.response.send_message(f"Could not find price for {currency}")
        else:
            await interaction.response.send_message(f"{currency.capitalize()}: {result:.2f} €")


    @commands.command(name='list')
    async def _list(self, ctx: commands.Context):
        result = await DataService.list_top_crypto_currencies(amount=10)
        message = "Top 10 Cryptocurrencies by Market Cap:\n\n"
        for coin in result:
            message += f"{coin.market_cap_rank}. {coin.name} ({coin.symbol.upper()})\n"
            message += f"   Price: ${coin.current_price:.2f} €\n"
            message += f"   Market Cap: ${coin.market_cap:,} €\n\n"
        await ctx.channel.send(message)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return
        if message.content.startswith(self.bot.command_prefix):
            return
        await message.channel.send(f"I heard you say: {message.content}")


class DiscordBot:
    def __init__(self, token: str, client_id: int, guild_id: int, channel_id: int):
        self.token = token
        self.client_id = client_id
        self.guild_id = guild_id # guild = server
        self.channel_id = channel_id
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
                await ctx.send(f"Command not found. Use `/echo`, `/index`, or `/list`")
            else:
                logging.error(f"Command error: {error}")

    async def start(self):
        """Start the Discord bot."""
        await self.bot.add_cog(Crypto_Notifier(self.bot))
        await self.bot.start(self.token)
        logging.info("DiscordBot has started!")

    async def stop(self):
        """Stop the Discord bot."""
        await self.bot.close()
