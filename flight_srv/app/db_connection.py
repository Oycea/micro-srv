import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

# Получение переменных окружения
POSTGRES_NAME = os.getenv('DB_NAME')
POSTGRES_USER = os.getenv('DB_USER')
POSTGRES_PASSWORD = os.getenv('DB_PASSWORD')
POSTGRES_HOST = os.getenv('DB_HOST')
POSTGRES_PORT = os.getenv('DB_PORT')


def check_conn_vars():
    # Проверка наличия всех необходимых переменных
    required_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']
    missing_vars = [var for var in required_vars if os.getenv(var) is None]

    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: "
                               f"{', '.join(missing_vars)}")


def get_connection():
    check_conn_vars()

    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
