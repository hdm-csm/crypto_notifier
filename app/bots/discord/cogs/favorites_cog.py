from discord.ext import commands
from app.bots.discord.cogs.account_cog import AccountCog
from app.db import Session_Factory
from app.models.enums import PlatformType
from app.services.account_lookup_service import AccountLookupService
from app.services.favorites_service import FavoritesService
from app.bots.discord.custom_context import CustomContext


class FavoritesCog(AccountCog):

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
        answer = await self._favorites_service.list_favorites(account=ctx.account)
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
        answer = self._favorites_service.drop_favorites(account=ctx.account)
        await ctx.send(answer)
