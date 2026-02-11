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
from app.repository.notification_repository import NotificationRepository
from app.services.crypto_api_service import CryptoApiService
from app.services.account_lookup_service import AccountLookupService
from app.services.crypto_currency_service import CryptoCurrencyService
from app.services.favorites_service import FavoritesService
from app.services.notification_service import NotificationService
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

    _account_repository = AccountRepository()
    _favorite_repository = FavoritesRepository()
    _cryptocurrency_repository = CryptocurrencyRepository()
    _vs_currency_repository = VsCurrencyRepository()
    _notification_repository = NotificationRepository()

    _http_client = httpx.AsyncClient()
    _crypto_api_service = CryptoApiService(_http_client)

    _account_lookup_service = AccountLookupService(
        account_repository=_account_repository, vs_currency_repository=_vs_currency_repository
    )
    _vs_currency_service = VsCurrencyService(
        vs_currency_repository=_vs_currency_repository,
        account_lookup_service=_account_lookup_service,
        crypto_api_service=_crypto_api_service,
    )
    _crypto_currency_service = CryptoCurrencyService(
        crypto_currency_repository=_cryptocurrency_repository,
        crypto_api_service=_crypto_api_service,
    )
    _favorites_service = FavoritesService(
        favorite_repository=_favorite_repository,
        cryptocurrency_repository=_cryptocurrency_repository,
        crypto_api_service=_crypto_api_service,
    )
    _notification_service = NotificationService(
        notification_repository=_notification_repository, crypto_api_service=_crypto_api_service
    )

    await _vs_currency_service.init_vs_currencies()
    await _crypto_currency_service.init_crypto_currencies()

    _discord_bot = DiscordBot(
        token=DISCORD_BOT_TOKEN,
        guild_id=DISCORD_GUILD_ID,
        crypto_api_service=_crypto_api_service,
        favorites_service=_favorites_service,
        notification_service=_notification_service,
        account_lookup_service=_account_lookup_service,
        vs_currency_service=_vs_currency_service,
    )
    print("Telegram Bot Token:", TELEGRAM_BOT_TOKEN)
    _telegram_bot = TelegramBot(
        token=TELEGRAM_BOT_TOKEN,
        account_lookup_service=_account_lookup_service,
        crypto_api_service=_crypto_api_service,
        favorites_service=_favorites_service,
        notification_service=_notification_service,
        vs_currency_service=_vs_currency_service,
    )
    try:
        await asyncio.gather(_discord_bot.start(), _telegram_bot.start())
    except KeyboardInterrupt:
        logging.info("Shutting down bots...")
    finally:
        await _discord_bot.stop()
        await _telegram_bot.stop()
        await _http_client.aclose()


if __name__ == "__main__":
    asyncio.run(async_main())
