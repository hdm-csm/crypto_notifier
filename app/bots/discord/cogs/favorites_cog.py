from discord.ext import commands
from app.db import Session_Factory
from app.models.enums import PlatformType
from app.services.account_lookup_service import AccountLookupService
from app.services.favorites_service import FavoritesService
from app.bots.discord.custom_context import CustomContext
import logging


class FavoritesCog(commands.Cog):

    PLATFORM_TYPE = PlatformType.DISCORD

    def __init__(
        self,
        bot,
        favorites_service: FavoritesService,
        account_lookup_service: AccountLookupService,
    ):
        self.bot = bot
        self._favorites_service = favorites_service
        self._account_lookup_service = account_lookup_service

    async def cog_before_invoke(self, ctx: CustomContext) -> None:
        """
        Called before the command is invoked, after the command checks have been made.
        Loads the account from the database.
        """
        try:
            ctx.db_session = Session_Factory()
            ctx.account = self._account_lookup_service.find_or_create_account(
                session=ctx.db_session,
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

    @commands.command(name="add_fav")
    async def _add_fav(self, ctx: CustomContext, input_crypto: str) -> None:
        """Save cryptocurrency as favorite."""
        answer = self._favorites_service.add_favorite(
            db_session=ctx.db_session, account=ctx.account, input_crypto=input_crypto.lower()
        )
        await ctx.send(answer)

    @commands.command(name="list_favs")
    async def _list_favs(self, ctx: CustomContext) -> None:
        """List favorite cryptocurrencies."""
        answer = await self._favorites_service.list_favorites(
            platform_type=self.PLATFORM_TYPE,
            platform_user_id=str(ctx.author.id),
        )
        await ctx.send(answer)

    @commands.command(name="remove_fav")
    async def _remove_fav(self, ctx: CustomContext, input_crypto: str):
        """Remove cryptocurrency from favorites."""
        answer = self._favorites_service.remove_favorite(
            db_session=ctx.db_session, account=ctx.account, input_crypto=input_crypto.lower()
        )
        await ctx.send(answer)

    @commands.command(name="drop_favs")
    async def _drop_favs(self, ctx: CustomContext):
        """Remove all favorite cryptocurrencies."""
        user_id = ctx.author.id
        answer = self._favorites_service.drop_favorites(
            platform_type=self.PLATFORM_TYPE,
            platform_user_id=str(user_id),
        )
        await ctx.send(answer)
