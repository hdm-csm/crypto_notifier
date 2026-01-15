import os

from dotenv import load_dotenv

# Load .env file depending on environment
# defaults to DEV if not set, needs to be set like : "export ENV=PRD"
ENV = os.getenv("ENV", "DEV")
# print("ENV =", ENV)

if ENV == "DEV":
    load_dotenv(".env.dev")
elif ENV == "PROD":
    load_dotenv(".env.prod")
else:
    load_dotenv(".env.dev")  # default to dev


class Config:
    """Centralized configuration"""

    # USED ALREADY!!!
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
    # mysqlconnector
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        (f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@" f"{DB_HOST}:{DB_PORT}/{MYSQL_DATABASE}"),
    )
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
    DISCORD_GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0"))
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
