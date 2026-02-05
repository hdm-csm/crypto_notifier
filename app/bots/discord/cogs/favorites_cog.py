from discord.ext import commands
from app.models.enums import PlatformType
from app.services.favorites_service import FavoritesService


class FavoritesCog(commands.Cog):

    PLATFORM_TYPE = PlatformType.DISCORD

    def __init__(
        self,
        bot,
        favorites_service: FavoritesService,
    ):
        self.bot = bot
        self._favorites_service = favorites_service

    @commands.command(name="add_fav")
    async def _add_fav(self, ctx: commands.Context, currency: str):
        """Save cryptocurrency as favorite."""
        user_id = ctx.author.id
        input_crypto = currency.lower()
        answer = self._bot_service.add_favorite(
            platform_type=self.PLATFORM_TYPE,
            platform_user_id=str(user_id),
            input_crypto=input_crypto,
        )
        await ctx.send(answer)

    @commands.command(name="list_favs")
    async def _list_favs(self, ctx: commands.Context):
        """List favorite cryptocurrencies."""
        user_id = ctx.author.id
        answer = await self._bot_service.list_favorites(
            platform_type=self.PLATFORM_TYPE,
            platform_user_id=str(user_id),
        )
        await ctx.send(answer)

    @commands.command(name="remove_fav")
    async def _remove_fav(self, ctx: commands.Context, currency: str):
        """Remove cryptocurrency from favorites."""
        user_id = ctx.author.id
        input_crypto = currency.lower()
        answer = self._bot_service.remove_favorite(
            platform_type=self.PLATFORM_TYPE,
            platform_user_id=str(user_id),
            input_crypto=input_crypto,
        )
        await ctx.send(answer)

    @commands.command(name="drop_favs")
    async def _drop_favs(self, ctx: commands.Context):
        """Remove all favorite cryptocurrencies."""
        user_id = ctx.author.id
        answer = self._bot_service.drop_favorites(
            platform_type=self.PLATFORM_TYPE,
            platform_user_id=str(user_id),
        )
        await ctx.send(answer)
