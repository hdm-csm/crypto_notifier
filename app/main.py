import asyncio
import logging
import httpx
from config import Config
from app.bots.discord.discord_bot import DiscordBot
from app.bots.telegram.telegram_bot import TelegramBot
from app.repository.account_repository import AccountRepository
from app.repository.favorites_repository import FavoritesRepository
from app.repository.crypto_currency_repository import CryptocurrencyRepository
from app.repository.vs_currency_repository import VsCurrencyRepository
from app.services.crypto_api_service import CryptoApiService
from app.services.account_lookup_service import AccountLookupService
from app.services.crypto_currency_service import CryptoCurrencyService
from app.services.favorites_service import FavoritesService
from app.services.vs_currency_service import VsCurrencyService
from scripts.init_db import init_db

DISCORD_BOT_TOKEN = Config.DISCORD_BOT_TOKEN
TELEGRAM_BOT_TOKEN = Config.TELEGRAM_BOT_TOKEN
DISCORD_GUILD_ID = Config.DISCORD_GUILD_ID

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(threadName)s - %(levelname)s - %(message)s",
)


async def async_main():

    # TODO: Remove this in production; only for initial setup; Use Alembic for DB migrations
    init_db()

    account_repository = AccountRepository()
    favorite_repository = FavoritesRepository()
    cryptocurrency_repository = CryptocurrencyRepository()
    vs_currency_repository = VsCurrencyRepository()

    http_client = httpx.AsyncClient()
    crypto_api_service = CryptoApiService(http_client)

    account_lookup_service = AccountLookupService(
        account_repository=account_repository, vs_currency_repository=vs_currency_repository
    )
    vs_currency_service = VsCurrencyService(
        vs_currency_repository=vs_currency_repository,
        account_lookup_service=account_lookup_service,
        crypto_api_service=crypto_api_service,
    )
    _crypto_currency_service = CryptoCurrencyService(
        crypto_currency_repository=cryptocurrency_repository,
        crypto_api_service=crypto_api_service,
    )
    favorites_service = FavoritesService(
        favorite_repository=favorite_repository,
        cryptocurrency_repository=cryptocurrency_repository,
        crypto_api_service=crypto_api_service,
    )

    await vs_currency_service.init_vs_currencies()
    await _crypto_currency_service.init_crypto_currencies()

    discord_bot = DiscordBot(
        token=DISCORD_BOT_TOKEN,
        guild_id=DISCORD_GUILD_ID,
        crypto_api_service=crypto_api_service,
        favorites_service=favorites_service,
        account_lookup_service=account_lookup_service,
        vs_currency_service=vs_currency_service,
    )
    print("Telegram Bot Token:", TELEGRAM_BOT_TOKEN)
    telegram_bot = TelegramBot(
        token=TELEGRAM_BOT_TOKEN,
        account_lookup_service=account_lookup_service,
        crypto_api_service=crypto_api_service,
        favorites_service=favorites_service,
        vs_currency_service=vs_currency_service,
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
