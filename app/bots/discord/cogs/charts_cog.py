import discord
from discord.ext import commands
from discord import app_commands

from app.bots.discord.charts.chart_view import ChartView
from app.bots.discord.charts.choices import ChartConfig
from app.bots.discord.cogs.base_cog import BaseCog
from app.services.account_lookup_service import AccountLookupService
from app.services.chart_service import ChartService
from app.services.crypto_currency_service import CryptoCurrencyService


class ChartsCog(BaseCog):
    """Cryptocurrency charts cog for displaying price charts."""

    def __init__(
        self,
        bot: commands.Bot,
        chart_service: ChartService,
        account_lookup_service: AccountLookupService,
        crypto_currency_service: CryptoCurrencyService,
    ):
        super().__init__(account_lookup_service, crypto_currency_service)
        self.bot = bot
        self._chart_service = chart_service

    @app_commands.command(name="chart", description="Display a cryptocurrency price chart")
    @app_commands.describe(
        crypto_symbol="Cryptocurrency symbol (e.g., BTC, ETH)",
        time_choice="Time period",
    )
    @app_commands.choices(time_choice=ChartConfig.get_choices())
    async def chart(
        self, interaction: discord.Interaction, crypto_symbol: str, time_choice: str = "1D"
    ):
        """Display a cryptocurrency price chart with interactive buttons."""
        await interaction.response.defer()

        crypto_symbol = crypto_symbol.upper()
        time_choice = time_choice.upper()

        # Instantiate the view with the service's async method
        view = ChartView(
            symbol=crypto_symbol,
            generate_chart_async=self._chart_service.generate_chart_async,
            initial_label=time_choice,
        )

        config = view.time_map.get(time_choice, view.time_map["1D"])

        # Fetch the initial chart
        buffer = await self._chart_service.generate_chart_async(
            crypto_symbol, config["period"], config["interval"]
        )

        if buffer:
            file = discord.File(fp=buffer, filename=f"{crypto_symbol}_chart.png")
            await interaction.followup.send(file=file, view=view)
        else:
            await interaction.followup.send(f"❌ Could not find data for symbol: {crypto_symbol}")
