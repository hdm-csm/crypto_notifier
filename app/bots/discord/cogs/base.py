import logging
from discord.ext import commands
from app.db import Session_Factory
from app.bots.discord.custom_context import CustomContext
from app.models.enums import PlatformType
from app.services.account_lookup_service import AccountLookupService
from app.utils.exceptions import InvokeSetupError


class AccountCog(commands.Cog):

    PLATFORM_TYPE = PlatformType.DISCORD

    def __init__(self, _account_lookup_service: AccountLookupService):
        self._account_lookup_service = _account_lookup_service

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
        except Exception as e:
            if hasattr(ctx, "db_session"):
                ctx.db_session.rollback()
                ctx.db_session.close()
            logging.error(f"Error in cog_before_invoke: {e}")
            await ctx.send(f"❌ An error occurred: {str(e)}")
            raise InvokeSetupError()  # Re-raise to stop execution --> ugly stacktrace sadly...
        return await super().cog_before_invoke(ctx)

    async def cog_after_invoke(self, ctx: commands.Context) -> None:
        """
        Called after the command is invoked, regardless of whether it succeeded or raised an exception.
        Called before cog_command_error.
        """
        assert isinstance(ctx, CustomContext)
        if hasattr(ctx, "db_session") and not ctx.command_failed:
            try:
                logging.info("Committing current db session.")
                ctx.db_session.commit()
            finally:
                ctx.db_session.close()
        return await super().cog_after_invoke(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """
        Called after cog_after_invoke if an exception was raised in the command or in cog_after_invoke.
        """
        assert isinstance(ctx, CustomContext)
        if hasattr(ctx, "db_session"):
            try:
                logging.error("Rolling back current db session.")
                ctx.db_session.rollback()
            finally:
                ctx.db_session.close()

        logging.error(f"Command error in {ctx.command}: {error}")

        # if not getattr(ctx, "command_failed", False): CANNOT DO THIS BC IT IGNORES REAL ERRORS DURING COMMANDS
        await ctx.send(f"❌ An error occurred: {str(error)}")

        return await super().cog_command_error(ctx, error)
