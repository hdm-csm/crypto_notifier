import logging
import discord
from discord.ext import commands
from app.db import get_session, session_scope
from app.bots.discord.custom.custom_context import CustomContext
from app.models.enums import PlatformType
from app.models.schemas import Cryptocurrency
from app.services.account_lookup_service import AccountLookupService
from app.services.crypto_currency_service import CryptoCurrencyService
from app.utils.exceptions import (
    InvokeSetupError,
    InvalidNotificationArguments,
)
from app.utils.functions import get_command_example
from discord import app_commands


class AccountCog(commands.Cog):
    """
    This class acts as a middleware, that adds "account" and "db_session" to each @commands.command() invocation.
    Goal: Avoid duplicate data fetching/session starting code
    For the equivalent middeware for @app_commands.command, check out app/bots/discord/custom_tree.py
    """

    PLATFORM_TYPE = PlatformType.DISCORD

    def __init__(
        self,
        account_lookup_service: AccountLookupService,
        crypto_currency_service: CryptoCurrencyService,
    ):
        self._account_lookup_service = account_lookup_service
        self._crypto_currency_service = crypto_currency_service

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        """
        Called before the command is invoked, after the command checks have been made.
        Loads the account from the database.
        """
        assert isinstance(ctx, CustomContext)
        try:
            ctx.db_session = get_session()
            ctx.account = self._account_lookup_service.find_or_create_account(
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

    async def crypto_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        with session_scope() as db_session:
            all_cryptos: list[Cryptocurrency] = self._crypto_currency_service.get_all(db_session)
            filtered = [
                c
                for c in all_cryptos
                if current.lower() in c.symbol.lower() or current.lower() in c.name.lower()
            ]
            return [
                app_commands.Choice(name=f"{c.name} ({c.symbol})", value=c.symbol) for c in filtered
            ][:25]
