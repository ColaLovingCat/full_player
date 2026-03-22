import os
import base64
import re
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from mutagen.mp3 import MP3
from mutagen.id3 import ID3

from core.database import init_db, save_songs_to_db, get_all_songs_from_db

app = FastAPI()

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    init_db()


# --- 工具函数 ---
def get_music_title(file_path, default_filename):
    """尝试从 ID3 标签获取歌名，获取不到则返回文件名"""
    try:
        audio = ID3(file_path)
        # TIT2 是 ID3v2 标准中的标题标签
        if "TIT2" in audio:
            return str(audio["TIT2"].text[0])
    except:
        pass
    return default_filename


def to_base64(file_path):
    """将物理路径图片转为 Base64"""
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
        except:
            return None
    return None


def parse_lrc(file_path):
    """解析 LRC 歌词文件为时间轴对象列表"""
    lyrics_data = []
    if not file_path or not os.path.exists(file_path):
        return lyrics_data

    pattern = re.compile(r"\[(\d+):(\d+\.\d+)\](.*)")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                match = pattern.match(line)
                if match:
                    minutes = int(match.group(1))
                    seconds = float(match.group(2))
                    text = match.group(3).strip()
                    lyrics_data.append({"time": minutes * 60 + seconds, "text": text})
    except Exception as e:
        print(f"LRC解析失败: {e}")
    return lyrics_data


# --- API 接口 ---


@app.get("/system/scan")
async def scan_endpoint(path: str = "./libs"):
    """扫描目录结构并存入数据库"""
    libs_path = Path(path).resolve()
    if not libs_path.exists():
        raise HTTPException(status_code=404, detail="Directory not found")

    songs_found = []
    # 结构：libs -> 歌手 -> 专辑 -> 歌曲
    for artist_dir in libs_path.iterdir():
        if not artist_dir.is_dir():
            continue

        # 歌手照片：libs/歌手/歌手.jpg
        artist_photo = next(artist_dir.glob(f"{artist_dir.name}.*"), None)

        for album_dir in artist_dir.iterdir():
            if not album_dir.is_dir():
                continue

            # 专辑封面：libs/歌手/专辑/cover.png
            album_cover = next(album_dir.glob("cover.*"), None)

            for file in album_dir.glob("*.mp3"):
                # 歌词：与歌曲同名但后缀为 .lrc 或 .txt
                lrc = file.with_suffix(".lrc")
                if not lrc.exists():
                    lrc = file.with_suffix(".txt")

                filename = file.stem 
                real_title = get_music_title(str(file), filename)

                try:
                    duration = MP3(file).info.length
                except:
                    duration = 0

                songs_found.append(
                    {
                        "file_path": str(file.absolute()),
                        "filename": filename,
                        "title": real_title,
                        "artist": artist_dir.name,
                        "album": album_dir.name,
                        "duration": duration,
                        "album_cover_path": (
                            str(album_cover.absolute()) if album_cover else None
                        ),
                        "artist_photo_path": (
                            str(artist_photo.absolute()) if artist_photo else None
                        ),
                        "lyrics_path": str(lrc.absolute()) if lrc.exists() else None,
                        "last_modified": os.path.getmtime(file),
                    }
                )

    save_songs_to_db(songs_found)
    return {"status": "success", "count": len(songs_found)}


@app.get("/songs/getList")
async def get_list():
    """获取所有歌曲，并在此处将图片转为 Base64 返回"""
    rows = get_all_songs_from_db()
    result = []
    for row in rows:
        result.append(
            {
                "id": row["id"],
                "title": row["title"],
                "artist": row["artist"],
                "album": row["album"],
                "duration": row["duration"],
                "path": row["file_path"],
                "album_cover": to_base64(row["album_cover_path"]),
                "artist_photo": to_base64(row["artist_photo_path"]),
                "lyrics_path": row["lyrics_path"],
            }
        )
    return {"songs": result}


@app.get("/songs/getFile")
async def get_file(song_path: str):
    """返回媒体文件流供播放"""
    if os.path.exists(song_path):
        return FileResponse(song_path)
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/songs/getLyrics")
async def get_lyrics(lyrics_path: str):
    """读取歌词文件并返回解析后的时间轴数据"""
    data = parse_lrc(lyrics_path)
    if not data:
        # 如果解析为空，尝试返回纯文本或错误
        return {"lyrics": [], "raw": "No lyrics found"}
    return {"lyrics": data}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
