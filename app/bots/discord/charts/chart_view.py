import discord
from discord.ui import View, Button
from typing import Dict, Any, Callable, Awaitable
import io

from app.bots.discord.charts.choices import ChartConfig


class TimeButton(Button["ChartView"]):
    def __init__(self, label: str, config: Dict[str, Any], is_selected: bool):
        style = discord.ButtonStyle.primary if is_selected else discord.ButtonStyle.secondary
        super().__init__(style=style, label=label, custom_id=label)
        self.config = config
        self.custom_label = label

    async def callback(self, interaction: discord.Interaction) -> None:
        assert self.view is not None
        await interaction.response.defer()

        for child in self.view.children:
            if isinstance(child, Button):
                child.style = (
                    discord.ButtonStyle.primary
                    if child.label == self.custom_label
                    else discord.ButtonStyle.secondary
                )

        buffer = await self.view.generate_chart_async(
            self.view.symbol,
            self.config["period"],
            self.config["interval"],
        )

        if buffer:
            file = discord.File(fp=buffer, filename=f"{self.view.symbol}_{self.custom_label}.png")
            await interaction.edit_original_response(attachments=[file], view=self.view)
        else:
            await interaction.followup.send("❌ Failed to fetch data.", ephemeral=True)


class ChartView(View):
    def __init__(
        self,
        symbol: str,
        generate_chart_async: Callable[[str, str, str], Awaitable[io.BytesIO | None]],
        initial_label: str = "1D",
    ):
        super().__init__(timeout=180)
        self.symbol = symbol
        self.generate_chart_async = generate_chart_async
        self.time_map: Dict[str, Dict[str, str]] = ChartConfig.get_map()

        for i, (label, config) in enumerate(self.time_map.items()):
            is_selected = label == initial_label
            button = TimeButton(label=label, config=config, is_selected=is_selected)
            button.row = i // 4
            self.add_item(button)
