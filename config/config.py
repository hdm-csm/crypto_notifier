import os

from dotenv import load_dotenv

# Load .env file depending on environment
# defaults to DEV if not set, needs to be set like : "export ENV=PRD"

ENV = os.getenv("ENV", "dev").lower()
load_dotenv(f".env.{ENV}")


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
