from discord.ext import commands
from app.bots.discord.cogs.base import AccountCog
from app.models.enums import PlatformType
from app.services.account_lookup_service import AccountLookupService
from app.services.favorites_service import FavoritesService
from app.bots.discord.custom_context import CustomContext
from app.utils.command_constants import (
    COMMAND_ADD_FAV,
    COMMAND_ADD_FAVS,
    COMMAND_LIST_FAVS,
    COMMAND_REMOVE_FAV,
    COMMAND_DROP_FAVS,
)


class FavoritesCog(AccountCog):

    PLATFORM_TYPE = PlatformType.DISCORD

    def __init__(
        self,
        account_lookup_service: AccountLookupService,
        favorites_service: FavoritesService,
    ):
        super().__init__(account_lookup_service)
        self._favorites_service = favorites_service

    @commands.command(name=COMMAND_ADD_FAV)
    async def _add_fav(self, ctx: CustomContext, input_crypto: str) -> None:
        """Save cryptocurrency as favorite."""
        answer = self._favorites_service.add_favorite(
            db_session=ctx.db_session, account=ctx.account, input_crypto=input_crypto
        )
        await ctx.send(answer)

    @commands.command(name=COMMAND_ADD_FAVS)
    async def _add_favs(self, ctx: CustomContext, *input_cryptos: str) -> None:
        """Save multiple cryptocurrencies as favorites."""
        if not input_cryptos:
            await ctx.send("⚠️ Please provide at least one cryptocurrency symbol or name.")
            return

        results = []
        for crypto in input_cryptos:
            result = self._favorites_service.add_favorite(
                db_session=ctx.db_session, account=ctx.account, input_crypto=crypto
            )
            results.append(result)

        await ctx.send("\n".join(results))

    @commands.command(name=COMMAND_LIST_FAVS)
    async def _list_favs(self, ctx: CustomContext) -> None:
        """List favorite cryptocurrencies."""
        answer = await self._favorites_service.list_favorites(account=ctx.account)
        await ctx.send(answer)

    @commands.command(name=COMMAND_REMOVE_FAV)
    async def _remove_fav(self, ctx: CustomContext, input_crypto: str) -> None:
        """Remove cryptocurrency from favorites."""
        answer = self._favorites_service.remove_favorite(
            db_session=ctx.db_session, account=ctx.account, input_crypto=input_crypto.lower()
        )
        await ctx.send(answer)

    @commands.command(name=COMMAND_DROP_FAVS)
    async def _drop_favs(self, ctx: CustomContext) -> None:
        """Remove all favorite cryptocurrencies."""
        answer = self._favorites_service.drop_favorites(account=ctx.account)
        await ctx.send(answer)
