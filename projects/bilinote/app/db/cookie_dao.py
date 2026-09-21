from app.db.sqlite_client import get_connection
from app.utils.logger import get_logger

logger = get_logger(__name__)


def init_cookie_table():
    conn = get_connection()
    if conn is None:
        logger.error("Failed to connect to the database.")
        return
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS platform_cookies (
            platform TEXT PRIMARY KEY,
            cookie_text TEXT NOT NULL,
            enabled INTEGER DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        conn.commit()
        conn.close()
        logger.info("platform_cookies table ready.")
    except Exception as e:
        logger.error(f"Failed to create platform_cookies table: {e}")


def get_cookie_row(platform: str):
    conn = get_connection()
    if conn is None:
        logger.error("Failed to connect to the database.")
        return None
    cursor = conn.cursor()
    cursor.execute(
        "SELECT platform, cookie_text, enabled, updated_at FROM platform_cookies WHERE platform = ?",
        (platform,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def upsert_cookie(platform: str, cookie_text: str, enabled: int = 1):
    conn = get_connection()
    if conn is None:
        logger.error("Failed to connect to the database.")
        return False
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO platform_cookies (platform, cookie_text, enabled, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(platform) DO UPDATE SET
            cookie_text = excluded.cookie_text,
            enabled = excluded.enabled,
            updated_at = CURRENT_TIMESTAMP
        """,
        (platform, cookie_text, enabled),
    )
    try:
        conn.commit()
        conn.close()
        logger.info(f"Cookie saved for platform={platform}")
        return True
    except Exception as e:
        logger.error(f"Failed to upsert cookie: {e}")
        conn.close()
        return False


def delete_cookie(platform: str):
    conn = get_connection()
    if conn is None:
        logger.error("Failed to connect to the database.")
        return False
    cursor = conn.cursor()
    cursor.execute("DELETE FROM platform_cookies WHERE platform = ?", (platform,))
    try:
        conn.commit()
        conn.close()
        logger.info(f"Cookie deleted for platform={platform}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete cookie: {e}")
        conn.close()
        return False
