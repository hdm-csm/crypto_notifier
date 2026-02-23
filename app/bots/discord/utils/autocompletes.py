# app/bots/discord/utils/autocompletes.py
from typing import cast
import discord
from discord import app_commands
from app.bots.discord.custom.custom_bot import CustomDiscordBot
from app.db import session_scope


async def crypto_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    # Get service from Bot Instance
    bot = cast(CustomDiscordBot, interaction.client)
    crypto_service = bot.crypto_currency_service
    with session_scope() as db_session:
        all_cryptos = crypto_service.get_all(db_session)
        filtered = [
            c
            for c in all_cryptos
            if current.lower() in c.symbol.lower() or current.lower() in c.name.lower()
        ]
        return [
            app_commands.Choice(name=f"{c.name} ({c.symbol})", value=c.symbol) for c in filtered
        ][:25]


async def vs_currency_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    # Get service from Bot Instance
    bot = cast(CustomDiscordBot, interaction.client)
    vs_currency_service = bot.vs_currency_service
    with session_scope() as db_session:
        all_vs_currencies = vs_currency_service.get_all(db_session)
        filtered = [
            c
            for c in all_vs_currencies
            if current.lower() in c.symbol.lower() or current.lower() in c.name.lower()
        ]
        return [
            app_commands.Choice(name=f"{c.name} ({c.symbol})", value=c.symbol) for c in filtered
        ][:25]
