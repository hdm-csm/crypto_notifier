import os

from dotenv import load_dotenv

# Load .env file depending on environment
ENV = os.getenv("ENV", "DEV")  # defaults to DEV if not set, needs to be set like : "export ENV=PRD"
# print("ENV =", ENV)

if ENV == "DEV":
    load_dotenv(".env.dev")
elif ENV == "PROD":
    load_dotenv(".env.prod")
else:
    load_dotenv(".env.dev")  # default to dev

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")

# mysqlconnector
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{DB_HOST}:{DB_PORT}/{MYSQL_DATABASE}",
)
