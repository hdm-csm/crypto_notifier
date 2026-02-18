import discord
from discord.ui import View, Button
from typing import Dict, Any, Callable


# 1. Create a Type-Safe Button Subclass
class TimeButton(Button["ChartView"]):
    def __init__(self, label: str, config: Dict[str, Any], is_selected: bool):
        style = discord.ButtonStyle.primary if is_selected else discord.ButtonStyle.secondary
        super().__init__(style=style, label=label, custom_id=label)
        self.config = config
        self.custom_label = label

    async def callback(self, interaction: discord.Interaction) -> None:
        """This replaces the monkey-patched create_callback logic."""
        assert self.view is not None
        await interaction.response.defer()
        for child in self.view.children:
            if isinstance(child, Button):
                # Set blue if it matches this button's label, else gray
                child.style = (
                    discord.ButtonStyle.primary
                    if child.label == self.custom_label
                    else discord.ButtonStyle.secondary
                )
        # Generate new chart
        buffer = await self.view.bot.loop.run_in_executor(
            None,
            self.view.get_chart_func,
            self.view.symbol,
            self.config["period"],
            self.config["interval"],
        )
        if buffer:
            file = discord.File(fp=buffer, filename=f"{self.view.symbol}_{self.custom_label}.png")
            await interaction.edit_original_response(attachments=[file], view=self.view)
        else:
            await interaction.followup.send("❌ Failed to fetch data.", ephemeral=True)


# 2. The View Class
class ChartView(View):
    def __init__(
        self, bot: Any, symbol: str, get_chart_func: Callable[..., Any], initial_label: str = "1D"
    ):
        super().__init__(timeout=180)
        self.bot = bot
        self.symbol = symbol
        self.get_chart_func = get_chart_func

        self.time_map: Dict[str, Dict[str, str]] = {
            "1D": {"period": "1d", "interval": "15m"},
            "5D": {"period": "5d", "interval": "30m"},
            "1M": {"period": "1mo", "interval": "1d"},
            "6M": {"period": "6mo", "interval": "1d"},
            "YTD": {"period": "ytd", "interval": "1d"},
            "1Y": {"period": "1y", "interval": "1wk"},
            "5Y": {"period": "5y", "interval": "1mo"},
            "All": {"period": "max", "interval": "3mo"},
        }

        # Create button instances and add them
        # for label, config in self.time_map.items():
        #     is_selected = label == initial_label
        #     button = TimeButton(label=label, config=config, is_selected=is_selected)
        #     self.add_item(button)
        for i, (label, config) in enumerate(self.time_map.items()):
            is_selected = label == initial_label

            button = TimeButton(label=label, config=config, is_selected=is_selected)

            # Integer division: 0//4 = 0, 1//4 = 0 ... 4//4 = 1
            # Indices 0-3 go to Row 0, Indices 4-7 go to Row 1
            button.row = i // 4

            self.add_item(button)
