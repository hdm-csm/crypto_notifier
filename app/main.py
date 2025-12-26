import asyncio
import os
import logging
import httpx
from dotenv import load_dotenv
from app.bots.DiscordBot import DiscordBot
from app.bots.TelegramBot import TelegramBot
from app.repository.account_repository import AccountRepository
from app.repository.favorite_repository import FavoriteRepository
from app.repository.cryptocurrency_repository import CryptocurrencyRepository
from app.services.crypto_api_service import CryptoApiService

load_dotenv(dotenv_path='.env.dev')
DISCORD_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
DISCORD_GUILD_ID = int(os.environ.get('DISCORD_GUILD_ID'))
DISCORD_CLIENT_ID = int(os.environ.get('DISCORD_CLIENT_ID'))
DISCORD_CHANNEL_ID = int(os.environ.get('DISCORD_CHANNEL_ID'))


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')

async def initialize_crypto_data(crypto_repository: CryptocurrencyRepository, crypto_api_service: CryptoApiService):
    if crypto_repository.is_empty():
        crypto_currencies = await crypto_api_service.list_top_crypto_currencies(amount=100)
        crypto_repository.store_cryptocurrencies(crypto_currencies)
    else:
        logging.info("Cryptocurrency data already initialized.")

async def async_main():

    account_repository = AccountRepository()
    favorite_repository = FavoriteRepository()
    cryptocurrency_repository = CryptocurrencyRepository()
    http_client = httpx.AsyncClient()
    crypto_api_service = CryptoApiService(http_client)  

    await initialize_crypto_data(cryptocurrency_repository, crypto_api_service)

    discord_bot = DiscordBot(
        DISCORD_TOKEN, 
        DISCORD_CLIENT_ID, 
        DISCORD_GUILD_ID, 
        DISCORD_CHANNEL_ID,
        crypto_api_service,
        account_repository,
        cryptocurrency_repository,
        favorite_repository
    )
    telegram_bot = TelegramBot(
        TELEGRAM_TOKEN,
        crypto_api_service,
        account_repository,
        favorite_repository
    )
    try:
        await asyncio.gather(
            discord_bot.start(),
            telegram_bot.start()
        )
    except KeyboardInterrupt:
        logging.info("Shutting down bots...")
    finally:
        await discord_bot.stop()
        await telegram_bot.stop()
        await http_client.aclose()


if __name__ == '__main__':
    asyncio.run(async_main())
