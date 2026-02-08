import logging
from discord.ext import commands
from app.db import Session_Factory
from app.bots.discord.custom_context import CustomContext


class AccountCog(commands.Cog):
    async def cog_before_invoke(self, ctx: CustomContext) -> None:
        """
        Called before the command is invoked, after the command checks have been made.
        Loads the account from the database.
        """
        try:
            ctx.db_session = Session_Factory()
            ctx.account = self._account_lookup_service.find_or_create_account(
                db_session=ctx.db_session,
                platform_type=self.PLATFORM_TYPE,
                platform_user_id=str(ctx.author.id),
            )
        except Exception:
            if hasattr(ctx, "db_session"):
                ctx.db_session.rollback()
                ctx.db_session.close()
            raise
        return await super().cog_before_invoke(ctx)

    async def cog_after_invoke(self, ctx: CustomContext) -> None:
        """
        Called after the command is invoked, regardless of whether it succeeded or raised an exception.
        Called before cog_command_error.
        """
        if hasattr(ctx, "db_session") and not ctx.command_failed:
            try:
                logging.info("Committing current db session.")
                ctx.db_session.commit()
            finally:
                ctx.db_session.close()
        return await super().cog_after_invoke(ctx)

    async def cog_command_error(self, ctx: CustomContext, error: Exception) -> None:
        """
        Called after cog_after_invoke if an exception was raised in the command or in cog_after_invoke.
        """
        if hasattr(ctx, "db_session"):
            try:
                logging.error("Rolling back current db session.")
                ctx.db_session.rollback()
            finally:
                ctx.db_session.close()

        logging.error(f"Command error in {ctx.command}: {error}")

        # Send error message to user
        await ctx.send(f"❌ An error occurred: {str(error)}")

        return await super().cog_command_error(ctx, error)
