import asyncio
import logging
import httpx
from config import Config
from app.bots.discord.discord_bot import DiscordBot
from app.bots.telegram.telegram_bot import TelegramBot
from app.repository.account_repository import AccountRepository
from app.repository.favorite_repository import FavoriteRepository
from app.repository.cryptocurrency_repository import CryptocurrencyRepository
from app.repository.fiat_currency_repository import FiatCurrencyRepository
from app.services.crypto_api_service import CryptoApiService
from app.services.account_lookup_service import AccountLookupService
from app.services.crypto_currency_service import CryptoCurrencyService
from app.services.favorites_service import FavoritesService
from app.services.fiat_currency_service import FiatCurrencyService
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
    favorite_repository = FavoriteRepository()
    cryptocurrency_repository = CryptocurrencyRepository()
    fiat_currency_repository = FiatCurrencyRepository()

    http_client = httpx.AsyncClient()
    crypto_api_service = CryptoApiService(http_client)

    account_lookup_service = AccountLookupService(
        account_repository=account_repository, fiat_currency_repository=fiat_currency_repository
    )
    # account_service = AccountService(account_repository)
    fiat_currency_service = FiatCurrencyService(
        fiat_currency_repository=fiat_currency_repository,
        account_lookup_service=account_lookup_service,
        _crypto_api_service=crypto_api_service,
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

    await fiat_currency_service.init_fiat_currencies()
    await _crypto_currency_service.init_crypto_currencies()

    discord_bot = DiscordBot(
        token=DISCORD_BOT_TOKEN,
        guild_id=DISCORD_GUILD_ID,
        crypto_api_service=crypto_api_service,
        favorites_service=favorites_service,
        _account_lookup_service=account_lookup_service,
        _fiat_currency_service=fiat_currency_service,
    )
    print("Telegram Bot Token:", TELEGRAM_BOT_TOKEN)
    telegram_bot = TelegramBot(
        token=TELEGRAM_BOT_TOKEN,
        account_lookup_service=account_lookup_service,
        crypto_api_service=crypto_api_service,
        favorites_service=favorites_service,
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
