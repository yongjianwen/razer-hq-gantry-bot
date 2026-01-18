import os
import sqlite3

from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DATA_PATH = os.environ.get("DATA_PATH")


def get_conn():
    conn = sqlite3.connect(
        f"{DATA_PATH}/app.db",
        timeout=30,
        check_same_thread=False
    )
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    return conn
