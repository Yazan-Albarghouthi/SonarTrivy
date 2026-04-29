import sqlite3

DATABASE_PATH = "notes.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            owner TEXT NOT NULL,
            is_private INTEGER DEFAULT 0
        )
        """
    )

    connection.commit()
    connection.close()