import asyncio
import os
import logging
import httpx
from dotenv import load_dotenv
from app.bots.discord_bot import DiscordBot
from app.bots.telegram_bot import TelegramBot
from app.repository.account_repository import AccountRepository
from app.repository.favorite_repository import FavoriteRepository
from app.repository.cryptocurrency_repository import CryptocurrencyRepository
from app.services.bot_service import BotService
from app.services.crypto_api_service import CryptoApiService
from app.services.general_service import GeneralService
from scripts.init_db import init_db

load_dotenv(dotenv_path=".env.dev")
DISCORD_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
DISCORD_GUILD_IDS = [
    int(gid.strip()) for gid in os.getenv("DISCORD_GUILD_IDS", "").split(",") if gid.strip()
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(threadName)s - %(levelname)s - %(message)s",
)


async def async_main():

    # TODO: Remove this in production; only for initial setup; Use Alembic for DB migrations
    init_db()

    account_repository = AccountRepository()
    favorite_repository = FavoriteRepository()
    cryptocurrency_repository = CryptocurrencyRepository()

    http_client = httpx.AsyncClient()
    crypto_api_service = CryptoApiService(http_client)

    general_service = GeneralService(cryptocurrency_repository, crypto_api_service)
    bot_service = BotService(
        account_repository, favorite_repository, cryptocurrency_repository, crypto_api_service
    )

    await general_service.initialize_crypto_currencies()

    discord_bot = DiscordBot(
        DISCORD_TOKEN,
        DISCORD_GUILD_IDS,
        bot_service,
        crypto_api_service,
    )
    telegram_bot = TelegramBot(
        TELEGRAM_TOKEN,
        crypto_api_service,
        account_repository,
        favorite_repository,
        bot_service,
    )
    try:
        await asyncio.gather(discord_bot.start(), telegram_bot.start())
    except KeyboardInterrupt:
        logging.info("Shutting down bots...")
    finally:
        await discord_bot.stop()
        await telegram_bot.stop()
        await http_client.aclose()


if __name__ == "__main__":
    asyncio.run(async_main())
