from discord.ext import commands
from app.db import session_scope
from app.models.enums import PlatformType
from app.models.schemas import Account
from app.services.account_lookup_service import AccountLookupService
from app.services.favorites_service import FavoritesService
from app.bots.discord.context import CustomContext


class AccountConverter(commands.Converter):
    PLATFORM_TYPE = PlatformType.DISCORD

    async def convert(self, ctx, argument):
        user_id = str(ctx.author.id)
        try:
            with session_scope() as session:
                account: Account = ctx.bot.account_lookup_service.find_or_create_account(
                    session=session,
                    platform_type=self.PLATFORM_TYPE,
                    platform_user_id=user_id,
                )
                return account
        except Exception:
            raise commands.CommandError("⚠️ Could not load account.")


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

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        user_id = str(ctx.author.id)
        try:
            with session_scope() as session:
                account: Account = self._account_lookup_service.find_or_create_account(
                    session=session,
                    platform_type=self.PLATFORM_TYPE,
                    platform_user_id=user_id,
                )
                ctx.account = account
        except Exception:
            raise commands.CommandError("⚠️ Could not load account.")

    @commands.command(name="add_fav")
    async def _add_fav(self, ctx: CustomContext, currency: str) -> None:
        """Save cryptocurrency as favorite."""
        # user_id = ctx.author.id
        # input_crypto = currency.lower()
        # answer = self._favorites_service.add_favorite(
        #     platform_type=self.PLATFORM_TYPE,
        #     platform_user_id=str(user_id),
        #     input_crypto=input_crypto,
        # )
        # await ctx.send(answer)
        answer = self._favorites_service.add_favorite_2(
            account=ctx.account, input_crypto=currency.lower()
        )
        await ctx.send(answer)
        # await ctx.send(ctx.account.selected_fiat_currency_id)

    @commands.command(name="list_favs")
    async def _list_favs(self, ctx: CustomContext, account: AccountConverter):
        """List favorite cryptocurrencies."""
        # user_id = ctx.author.id
        # answer = await self._favorites_service.list_favorites(
        #     platform_type=self.PLATFORM_TYPE,
        #     platform_user_id=str(user_id),
        # )
        # await ctx.send(answer)
        await ctx.send(f"{account.id}, {account.selected_fiat_currency_id}")
        # await ctx.send(ctx.account.selected_fiat_currency_id)

    @commands.command(name="remove_fav")
    async def _remove_fav(self, ctx: CustomContext, currency: str):
        """Remove cryptocurrency from favorites."""
        user_id = ctx.author.id
        input_crypto = currency.lower()
        answer = self._favorites_service.remove_favorite(
            platform_type=self.PLATFORM_TYPE,
            platform_user_id=str(user_id),
            input_crypto=input_crypto,
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
