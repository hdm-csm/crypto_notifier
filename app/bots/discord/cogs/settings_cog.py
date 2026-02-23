import discord
from discord import app_commands
from app.bots.discord.cogs.base import AccountCog
from app.bots.discord.custom.custom_interaction import get_db_session, get_account
from app.db import session_scope
from app.models.enums import PlatformType
from app.models.schemas import VsCurrency
from app.services.account_lookup_service import AccountLookupService
from app.services.crypto_currency_service import CryptoCurrencyService
from app.services.vs_currency_service import VsCurrencyService
from app.bots.constants.commands import (
    COMMAND_ADD_FAV,
    COMMAND_ADD_FAVS,
    COMMAND_LIST_FAVS,
    COMMAND_REMOVE_FAV,
    COMMAND_DROP_FAVS,
    COMMAND_ADD_NOTIF,
    COMMAND_LIST_NOTIFS,
    COMMAND_REMOVE_NOTIF,
    COMMAND_DROP_NOTIFS,
    COMMAND_GET_VS,
    COMMAND_LIST_VS,
    COMMAND_SET_VS,
    COMMAND_INDEX,
    COMMAND_TOP,
    COMMAND_LIST,
)


class SettingsCog(AccountCog):

    PLATFORM_TYPE = PlatformType.DISCORD

    def __init__(
        self,
        account_lookup_service: AccountLookupService,
        vs_currency_service: VsCurrencyService,
        crypto_currency_service: CryptoCurrencyService,
    ):
        super().__init__(account_lookup_service, crypto_currency_service)
        self._vs_currency_service = vs_currency_service

    @app_commands.command(
        name=COMMAND_GET_VS, description="Get your current quote currency setting"
    )
    async def _get_vs_currency(self, interaction: discord.Interaction):
        account = get_account(interaction)
        answer: str = self._vs_currency_service.get_vs_currency(account)
        await interaction.response.send_message(answer)

    @app_commands.command(name=COMMAND_LIST_VS, description="List all supported quote currencies")
    async def _list_vs_currencies(self, interaction: discord.Interaction):
        db_session = get_db_session(interaction)
        message = self._vs_currency_service.list_supported_vs_currencies(db_session)
        await interaction.response.send_message(message)

    @app_commands.command(name=COMMAND_SET_VS, description="Set your preferred quote currency")
    @app_commands.describe(vs_currency_input="The currency symbol or name")
    async def _set_vs_currency(self, interaction: discord.Interaction, vs_currency_input: str):
        """Set preferred vs currency."""
        db_session = get_db_session(interaction)
        account = get_account(interaction)
        answer: str = self._vs_currency_service.set_vs_currency(
            db_session, account, vs_currency_input
        )
        await interaction.response.send_message(answer)

    @app_commands.command(name="help", description="Show all available bot commands")
    async def _help(self, interaction: discord.Interaction):
        """Display a help embed with all available commands."""

        embed = discord.Embed(
            title="📖 Crypto Notifier — Command Reference",
            description="Here's everything you can do with this bot. Use `/` to get autocomplete suggestions for any command.",
            color=discord.Color.gold(),
        )
        # ── Crypto Info ──────────────────────────────────────────────────────
        embed.add_field(
            name="📊  Crypto Info",
            value=(
                f"**`/{COMMAND_INDEX} <coin>`** — Get the current price of a cryptocurrency\n"
                f"　 *Example:* `/{COMMAND_INDEX} bitcoin`\n\n\n"
                f"**`/{COMMAND_TOP} [amount]`** — Top N coins by market cap *(default: 10)*\n"
                f"　 *Example:* `/{COMMAND_TOP} 5`\n\n\n"
                f"**`/{COMMAND_LIST}`** — List all supported cryptocurrencies\n"
                f"　 *Example:* `/{COMMAND_LIST}`\n"
            ),
            inline=False,
        )
        # ── Favorites ─────────────────────────────────────────────────────────
        embed.add_field(
            name="⭐  Favorites",
            value=(
                "\n"
                f"**`/{COMMAND_ADD_FAV} <coin>`** — Add a coin to your favorites\n"
                f"　 *Example:* `/{COMMAND_ADD_FAV} ethereum`\n\n\n"
                f"**`/{COMMAND_ADD_FAVS} <coins…>`** — Add multiple coins at once *(space-separated)*\n"
                f"　 *Example:* `/{COMMAND_ADD_FAVS} bitcoin ethereum solana`\n\n\n"
                f"**`/{COMMAND_LIST_FAVS}`** — Show your favorite coins\n"
                f"　 *Example:* `/{COMMAND_LIST_FAVS}`\n\n\n"
                f"**`/{COMMAND_REMOVE_FAV} <coin>`** — Remove a coin from favorites\n"
                f"　 *Example:* `/{COMMAND_REMOVE_FAV} bitcoin`\n\n\n"
                f"**`/{COMMAND_DROP_FAVS}`** — Clear all your favorites\n"
                f"　 *Example:* `/{COMMAND_DROP_FAVS}`\n"
            ),
            inline=False,
        )
        # ── Notifications ─────────────────────────────────────────────────────
        embed.add_field(
            name="🔔  Price Notifications",
            value=(
                "\n"
                f"**`/{COMMAND_ADD_NOTIF} <coin> <quote> <above|below> <price>`** — Set a price alert\n"
                f"　 *Example:* `/{COMMAND_ADD_NOTIF} bitcoin eur above 90000`\n\n\n"
                f"**`/{COMMAND_LIST_NOTIFS}`** — List all your active notifications\n"
                f"　 *Example:* `/{COMMAND_LIST_NOTIFS}`\n\n\n"
                f"**`/{COMMAND_REMOVE_NOTIF} <id>`** — Remove a notification by its ID\n"
                f"　 *Example:* `/{COMMAND_REMOVE_NOTIF} 3`\n\n\n"
                f"**`/{COMMAND_DROP_NOTIFS}`** — Delete all your notifications\n"
                f"　 *Example:* `/{COMMAND_DROP_NOTIFS}`\n"
            ),
            inline=False,
        )
        # ── Charts ────────────────────────────────────────────────────────────
        embed.add_field(
            name="📈  Charts",
            value=(
                "\n"
                "**`/chart <coin> [period]`** — Show a candlestick chart *(periods: 1D · 5D · 1MO · 3MO · 1Y)*\n"
                "　 *Example:* `/chart btc 1MO`\n"
            ),
            inline=False,
        )
        # ── Settings ──────────────────────────────────────────────────────────
        embed.add_field(
            name="⚙️  Settings",
            value=(
                "\n"
                f"**`/{COMMAND_GET_VS}`** — Show your current quote currency\n"
                f"　 *Example:* `/{COMMAND_GET_VS}`\n\n\n"
                f"**`/{COMMAND_LIST_VS}`** — List all supported quote currencies\n"
                f"　 *Example:* `/{COMMAND_LIST_VS}`\n\n\n"
                f"**`/{COMMAND_SET_VS} <currency>`** — Change your preferred quote currency\n"
                f"　 *Example:* `/{COMMAND_SET_VS} usd`\n\n\n"
                "**`/help`** — Show this help message"
            ),
            inline=False,
        )
        embed.set_footer(
            text="💡 Tip: all coin inputs accept both the symbol (e.g. BTC) and the full name (e.g. Bitcoin)."
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @_set_vs_currency.autocomplete("vs_currency_input")
    async def _set_vs_currency_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        with session_scope() as db_session:
            all_vs_currencies: list[VsCurrency] = self._vs_currency_service.get_all(db_session)
            filtered = [
                c
                for c in all_vs_currencies
                if current.lower() in c.symbol.lower() or current.lower() in c.name.lower()
            ]
            return [
                app_commands.Choice(name=f"{c.name} ({c.symbol})", value=f"{c.symbol}")
                for c in filtered
            ][:25]
