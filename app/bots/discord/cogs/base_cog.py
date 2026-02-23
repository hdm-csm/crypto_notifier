import logging
from discord.ext import commands
from app.bots.discord.custom.custom_bot import CustomDiscordBot
from app.db import get_session
from app.bots.discord.custom.custom_context import CustomContext
from app.models.enums import PlatformType
from app.utils.exceptions import (
    InvokeSetupError,
    InvalidNotificationArguments,
)
from app.utils.functions import get_command_example


class BaseCog(commands.Cog):
    """
    This class acts as a middleware, that adds "account" and "db_session" to each @commands.command() invocation.
    Goal: Avoid duplicate data fetching/session starting code
    For the equivalent middeware for @app_commands.command, check out app/bots/discord/custom_tree.py
    """

    PLATFORM_TYPE = PlatformType.DISCORD

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        """
        Called before the command is invoked, after the command checks have been made.
        Loads the account from the database.
        """
        assert isinstance(ctx, CustomContext)
        try:
            ctx.db_session = get_session()
            bot: CustomDiscordBot = ctx.bot
            ctx.account = bot.account_lookup_service.find_or_create_account(
                db_session=ctx.db_session,
                platform_type=self.PLATFORM_TYPE,
                platform_user_id=str(ctx.author.id),
            )
        except Exception as e:
            if ctx.db_session:
                ctx.db_session.rollback()
                ctx.db_session.close()
            logging.error(f"Error in cog_before_invoke: {e}")
            await ctx.send(f"❌ An error occurred (internally): {str(e)}")
            raise InvokeSetupError()  # Re-raise to stop execution --> ugly stacktrace sadly...
        return await super().cog_before_invoke(ctx)  # no return ?

    async def cog_after_invoke(self, ctx: commands.Context) -> None:
        """
        Called after the command is invoked, regardless of whether it succeeded or raised an exception.
        Called before cog_command_error.
        """
        assert isinstance(ctx, CustomContext)
        if ctx.db_session and not ctx.command_failed:
            try:
                ctx.db_session.commit()
                logging.info("Committed current db session.")
            finally:
                ctx.db_session.close()
        return await super().cog_after_invoke(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """
        Called after cog_after_invoke if an exception was raised in the command or in cog_after_invoke.
        """
        assert isinstance(ctx, CustomContext)
        if ctx.db_session:
            try:
                logging.error("Rolling back current db session.")
                ctx.db_session.rollback()
            finally:
                ctx.db_session.close()
        logging.error(f"Command error in {ctx.command}: {type(error).__name__} - {error}")

        error_message = f"❌ An error occurred: {str(error)}"
        if isinstance(error, commands.MissingRequiredArgument):
            command_name: str | None = ctx.command.name if ctx.command else None
            if command_name:
                error_message += get_command_example(command_name)
            else:
                error_message += "\nMissing required arguments."
        elif isinstance(error, InvalidNotificationArguments):
            error_message = str(error)
            if error.usage_hint:
                error_message += f"\n{error.usage_hint}"

        await ctx.send(error_message)
        return await super().cog_command_error(ctx, error)
