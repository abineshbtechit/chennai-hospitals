import os
import sys
import socket
import mysql.connector
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()


def get_connection_settings():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        parsed = urlparse(database_url)
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 3306,
            "user": parsed.username or "root",
            "password": parsed.password or "",
            "database": (parsed.path or "/").lstrip("/") or None,
        }

    host = os.getenv("MYSQLHOST", os.getenv("DB_HOST", "localhost"))
    port_str = os.getenv("MYSQLPORT", os.getenv("DB_PORT", "3306"))
    try:
        port = int(port_str)
    except (TypeError, ValueError):
        print(f"Invalid port value: {port_str!r}. It must be an integer.")
        sys.exit(1)

    return {
        "host": host,
        "port": port,
        "user": os.getenv("MYSQLUSER", os.getenv("DB_USER", "root")),
        "password": os.getenv("MYSQLPASSWORD", os.getenv("DB_PASSWORD", "")),
        "database": os.getenv("MYSQLDATABASE", os.getenv("DB_NAME", None)),
    }


settings = get_connection_settings()
print("Connecting with:")
print("  host:", settings["host"])
print("  port:", settings["port"])
print("  user:", settings["user"])
print("  database:", settings["database"])

try:
    socket.getaddrinfo(settings["host"], settings["port"], socket.AF_UNSPEC, socket.SOCK_STREAM)
except socket.gaierror as e:
    print(f"DNS resolution failed for host {settings['host']!r}: {e}")
    sys.exit(1)

try:
    conn = mysql.connector.connect(
        host=settings["host"],
        port=settings["port"],
        user=settings["user"],
        password=settings["password"],
        database=settings["database"],
    )
    cursor = conn.cursor()
    cursor.execute("SELECT DATABASE();")
    print("Connected DB:", cursor.fetchone()[0])

    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()
    if tables:
        print("Tables:", ", ".join(table[0] for table in tables))
    else:
        print("No tables found")

    cursor.close()
    conn.close()
    print("Test completed successfully")
except mysql.connector.Error as e:
    print("MySQL connection failed:")
    print(e)