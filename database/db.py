import sqlite3
import os

from config import DATABASE_PATH


def get_connection():
    """
    Create and return a SQLite database connection.
    """
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    # Enable foreign key support
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database():
    """
    Create all required database tables.
    """

    connection = get_connection()

    try:
        schema_path = os.path.join(
            os.path.dirname(__file__),
            "schema.sql"
        )

        with open(schema_path, "r", encoding="utf-8") as file:
            schema = file.read()

        connection.executescript(schema)
        connection.commit()

        print("Database initialized successfully.")

    finally:
        connection.close()


def clear_database():
    """
    Delete all records from the database.

    Useful during development when we want
    to regenerate fresh sample data.
    """

    connection = get_connection()

    try:
        tables = [
            "interviews",
            "shortlists",
            "students",
            "companies",
            "rooms",
            "disruptions"
        ]

        for table in tables:
            connection.execute(
                f"DELETE FROM {table}"
            )

        connection.commit()

        print("Database cleared successfully.")

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()