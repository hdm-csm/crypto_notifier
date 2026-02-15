import logging
from discord.ext import commands
from app.db import Session_Factory
from app.bots.discord.custom_context import CustomContext
from app.models.enums import PlatformType
from app.services.account_lookup_service import AccountLookupService
from app.utils.exceptions import (
    InvokeSetupError,
    InvalidNotificationArguments,
)
from app.utils.functions import get_command_example


class AccountCog(commands.Cog):

    PLATFORM_TYPE = PlatformType.DISCORD

    def __init__(self, account_lookup_service: AccountLookupService):
        self._account_lookup_service = account_lookup_service

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        """
        Called before the command is invoked, after the command checks have been made.
        Loads the account from the database.
        """
        assert isinstance(ctx, CustomContext)

        try:
            ctx.db_session = Session_Factory()

            ctx.account = self._account_lookup_service.find_or_create_account(
                db_session=ctx.db_session,
                platform_type=self.PLATFORM_TYPE,
                platform_user_id=str(ctx.author.id),
            )

        except Exception:
            if ctx.db_session:
                ctx.db_session.rollback()
                ctx.db_session.close()

            logging.exception("Error in cog_before_invoke")
            await ctx.send("❌ An error occurred (internally).")
            raise InvokeSetupError()  # Re-raise to stop execution --> ugly stacktrace sadly...

        await super().cog_before_invoke(ctx)

    async def cog_after_invoke(self, ctx: commands.Context) -> None:
        """
        Called after the command is invoked, regardless of whether it succeeded or raised an exception.
        Called before cog_command_error.
        """
        assert isinstance(ctx, CustomContext)

        if ctx.db_session and not ctx.command_failed:
            try:
                logging.info("Committing current db session.")
                ctx.db_session.commit()
            finally:
                ctx.db_session.close()

        await super().cog_after_invoke(ctx)

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

        logging.error(
            "Command error in %s: %s - %s",
            ctx.command.name if ctx.command else "unknown",
            type(error).__name__,
            error,
        )

        # Build error message with command-specific hints
        error_message = f"❌ An error occurred: {error}"

        if isinstance(error, commands.MissingRequiredArgument):
            command_name = ctx.command.name if ctx.command else None
            if command_name:
                error_message += get_command_example(command_name)
            else:
                error_message += "\nMissing required arguments."

        elif isinstance(error, InvalidNotificationArguments):
            error_message = str(error)
            if error.usage_hint:
                error_message += f"\n{error.usage_hint}"

        await ctx.send(error_message)

        await super().cog_command_error(ctx, error)
