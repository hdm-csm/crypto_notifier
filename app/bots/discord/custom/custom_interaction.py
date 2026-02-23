# custom_interaction.py
import discord
from sqlalchemy.orm import Session
from app.models.schemas import Account
from typing import cast


def get_db_session(interaction: discord.Interaction) -> Session:
    return cast(Session, interaction.extras["db_session"])


def get_account(interaction: discord.Interaction) -> Account:
    return cast(Account, interaction.extras["account"])
