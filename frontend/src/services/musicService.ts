import axios from "axios";
const API_BASE = import.meta.env.VITE_API_BASE;

export interface Song {
  id: number;
  title: string;
  artist: string;
  album: string;
  duration: number;
  path: string;
  albumCover: string;
  artistPhoto: string;
  lyricsPath: string;
  isFavorite: boolean;
}

export interface Album {
  name: string;
  artist: string;
  cover: string;
  artistPhoto: string;
  songs: Song[];
}

export const musicService = {
  // 手动触发扫描音乐库
  async triggerScan(path?: string): Promise<{ status: string; count: number }> {
    try {
      const params = path ? { path } : {};

      const response = await axios.get(`${API_BASE}/system/scan`, { params });
      return response.data;
    } catch (error) {
      console.error("扫描音乐库失败:", error);
      throw error;
    }
  },

  // 获取并转换数据
  async getAlbumsWithSongs(): Promise<Album[]> {
    const res = await axios.get(`${API_BASE}/songs/getList`);
    const allSongs: any[] = res.data.songs;

    const albumMap = new Map<string, Album>();
    const favoriteSongs: Song[] = [];

    allSongs.forEach((s) => {
      const key = `${s.album}-${s.artist}`;
      if (!albumMap.has(key)) {
        albumMap.set(key, {
          name: s.album,
          artist: s.artist,
          cover: s.album_cover,
          artistPhoto: s.artist_photo,
          songs: [],
        });
      }
      albumMap.get(key)?.songs.push({
        id: s.id,
        title: s.title,
        artist: s.artist,
        album: s.album,
        duration: s.duration,
        path: s.path,
        albumCover: s.album_cover,
        artistPhoto: s.artist_photo,
        lyricsPath: s.lyrics_path,
        isFavorite: s.isFavorite,
      });

      if (s.isFavorite) {
        favoriteSongs.push(s);
      }
    });

    const standardAlbums = Array.from(albumMap.values());
    const favAlbum = {
      name: "我的最爱",
      artist: "My Favorites",
      cover:
        favoriteSongs.length > 0
          ? favoriteSongs[0].albumCover
          : "/default-heart-cover.png",
      artistPhoto: "",
      songs: favoriteSongs,
    };

    return [favAlbum, ...standardAlbums];
  },

  // 获取解析后的歌词
  async getLyrics(path: string) {
    const res = await axios.get(`${API_BASE}/songs/getLyrics`, {
      params: { lyrics_path: path },
    });
    return res.data.lyrics;
  },

  // 获取播放地址
  getAudioUrl(path: string) {
    return `${API_BASE}/songs/getFile?song_path=${encodeURIComponent(path)}`;
  },

  // 喜爱
  async toggleFavorite(songId: number) {
    const res = await axios.post(
      `${API_BASE}/songs/toggleFavorite?song_id=${songId}`,
    );
    return res.data.isFavorite;
  },
};
