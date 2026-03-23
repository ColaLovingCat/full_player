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
            last_modified REAL,
            is_favorite INTEGER DEFAULT 0
        )
    """
    )
    conn.commit()
    conn.close()


def save_songs_to_db(songs_list):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT file_path FROM songs WHERE is_favorite = 1")
    favorite_paths = {row[0] for row in cursor.fetchall()}

    cursor.execute("DELETE FROM songs")

    for s in songs_list:
        is_fav = 1 if s["file_path"] in favorite_paths else 0

        cursor.execute(
            """
            INSERT INTO songs 
            (file_path, filename, title, artist, album, duration, album_cover_path, artist_photo_path, lyrics_path, last_modified, is_favorite)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                is_fav,
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


def toggle_favorite_in_db(song_id: int):
    """切换歌曲的喜欢状态并返回最新状态"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 先查询当前状态
    cursor.execute("SELECT is_favorite FROM songs WHERE id = ?", (song_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    new_status = 0 if row[0] == 1 else 1
    # 更新状态
    cursor.execute(
        "UPDATE songs SET is_favorite = ? WHERE id = ?", (new_status, song_id)
    )
    conn.commit()
    conn.close()
    return new_status == 1
