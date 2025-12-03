import asyncio
import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters, CommandHandler, ApplicationBuilder

load_dotenv(dotenv_path='.env.dev')
DISCORD_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
DISCORD_GUILD_ID = int(os.environ.get('DISCORD_GUILD_ID'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("List!")

class Tracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command(name='echo')
    async def _echo(self, ctx: commands.Context, *, arg: str):
        await ctx.channel.send(f"You said: {arg}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return
        if message.content.startswith(self.bot.command_prefix):
            return
        await message.channel.send(f"I heard you say: {message.content}")

async def run_discord():
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='/', intents=intents)
    await bot.add_cog(Tracker(bot))
    await bot.start(DISCORD_TOKEN)
    try:
        await asyncio.Future() # wait indefinitely until future is resolved/canceled (in pending state)
    except asyncio.CancelledError: # when future is explicitly canceled, await raises this exception
        pass # do nothing, continue program flow
    await bot.close()

async def run_telegram():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("list", list_command, block=False))
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,echo, block=False))
    await application.initialize()
    await application.start()
    await application.updater.start_polling(
        poll_interval=0.0,
        timeout=60,
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True
    )
    await run_discord()
    await application.updater.stop()
    await application.stop()
    await application.shutdown()

if __name__ == '__main__':
    asyncio.run(run_telegram())
