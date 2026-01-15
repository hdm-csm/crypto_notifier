import os
from dotenv import load_dotenv

ENV = os.getenv("ENV", "DEV")

if ENV == "DEV":
    load_dotenv(".env.dev")
elif ENV == "PROD":
    load_dotenv(".env.prod")
else:
    load_dotenv(".env.dev")  # default to dev


class Config:
    """Centralized configuration"""

    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        (f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@" f"{DB_HOST}:{DB_PORT}/{MYSQL_DATABASE}"),
    )
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
    DISCORD_GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0"))
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
