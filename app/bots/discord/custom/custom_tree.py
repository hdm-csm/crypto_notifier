import logging
import discord
from discord import app_commands
from app.db import get_session
from app.models.enums import PlatformType
from app.services.account_lookup_service import AccountLookupService
from app.utils.exceptions import InvalidNotificationArguments


class CustomTree(app_commands.CommandTree):
    """
    This class acts as a middleware, that adds "account" and "db_session" to each @app_commands.command() invocation.
    Goal: Avoid duplicate data fetching/session starting code
    For the equivalent middeware for @commands.command, check out app/bots/discord/cogs/base.py
    """

    def __init__(self, bot, account_lookup_service: AccountLookupService):
        super().__init__(bot)
        self._account_lookup_service = account_lookup_service

    async def _call(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.application_command:
            await super()._call(interaction)
            return
        db_session = get_session()
        interaction.extras["db_session"] = db_session
        try:
            account = self._account_lookup_service.find_or_create_account(
                db_session=db_session,
                platform_type=PlatformType.DISCORD,
                platform_user_id=str(interaction.user.id),
            )
            interaction.extras["account"] = account
            await interaction.response.defer()  # get more time to process command
            await super()._call(interaction)
            db_session.commit()
            logging.info("Committed current db session.")
        except Exception as e:
            logging.error(f"Rolling back current db session. Error: {type(e).__name__} - {e}")
            db_session.rollback()
            raise
        finally:
            db_session.close()

    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandInvokeError):
            logging.error(f"App command error: {type(error).__name__} - {error}")
            inner = error.original
            if isinstance(inner, InvalidNotificationArguments):
                message = str(inner)
                if inner.usage_hint:
                    message += f"\n{inner.usage_hint}"
            else:

                message = f"❌ An error occurred: {str(inner)}"
        elif isinstance(error, app_commands.MissingPermissions):
            message = "❌ You don't have permission to use this command."
        elif isinstance(error, app_commands.BotMissingPermissions):
            message = "❌ I don't have the required permissions to do that."
        else:
            message = f"❌ An error occurred: {str(error)}"

        try:
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
        except Exception as e:
            logging.error(f"Failed to send error message to user: {e}")

        await super().on_error(interaction, error)
