import sqlite3
import os

DB_PATH = "music_cache.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE,
            filename TEXT,
            title TEXT,
            artist TEXT,
            album TEXT,
            duration REAL,
            album_cover_path TEXT,
            artist_photo_path TEXT,
            lyrics_path TEXT,
            last_modified REAL
        )
    """
    )
    conn.commit()
    conn.close()


def save_songs_to_db(songs_list):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM songs")
    for s in songs_list:
        cursor.execute(
            """
            INSERT INTO songs 
            (file_path, filename, title, artist, album, duration, album_cover_path, artist_photo_path, lyrics_path, last_modified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                s["file_path"],
                s["filename"],
                s["title"],
                s["artist"],
                s["album"],
                s["duration"],
                s["album_cover_path"],
                s["artist_photo_path"],
                s["lyrics_path"],
                s["last_modified"],
            ),
        )
    conn.commit()
    conn.close()


def get_all_songs_from_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM songs")
    rows = cursor.fetchall()
    conn.close()
    return rows
