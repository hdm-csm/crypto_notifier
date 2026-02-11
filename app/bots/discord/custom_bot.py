from app.bots.discord.custom_context import CustomContext
from discord.ext import commands


class CustomDiscordBot(commands.Bot):
    """Custom bot that uses CustomContext for all commands."""

    async def get_context(self, message, *, cls=CustomContext):
        return await super().get_context(message, cls=cls)
