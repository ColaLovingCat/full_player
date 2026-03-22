import axios from "axios";
const API_BASE = import.meta.env.VITE_API_BASE;

export interface Song {
  id: number;
  title: string;
  artist: string;
  album: string;
  duration: number;
  path: string; // 对应后端的 file_path
  albumCover: string; // Base64
  artistPhoto: string; // Base64
  lyricsPath: string;
}

export interface Album {
  name: string;
  artist: string;
  cover: string;
  artistPhoto: string;
  songs: Song[];
}

export const musicService = {
  /**
   * 手动触发扫描音乐库
   * @param path 要扫描的绝对或相对路径，如果不传，后端默认扫描 './libs'
   * @returns 返回扫描结果 { status: "success", count: number }
   */
  async triggerScan(path?: string): Promise<{ status: string; count: number }> {
    try {
      // 构造请求参数，如果传入了 path 则带上
      const params = path ? { path } : {};

      const response = await axios.get(`${API_BASE}/system/scan`, { params });
      return response.data;
    } catch (error) {
      console.error("扫描音乐库失败:", error);
      throw error; // 将错误抛出，以便在 UI 层显示错误提示（如 Toast）
    }
  },

  // 获取并转换数据
  async getAlbumsWithSongs(): Promise<Album[]> {
    const res = await axios.get(`${API_BASE}/songs/getList`);
    const allSongs: any[] = res.data.songs;
    const albumMap = new Map<string, Album>();

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
      });
    });
    return Array.from(albumMap.values());
  },

  // 获取解析后的歌词
  async getLyrics(path: string) {
    const res = await axios.get(`${API_BASE}/songs/getLyrics`, {
      params: { lyrics_path: path },
    });
    return res.data.lyrics; // [{time: 12.3, text: '...'}, ...]
  },

  // 获取播放地址
  getAudioUrl(path: string) {
    return `${API_BASE}/songs/getFile?song_path=${encodeURIComponent(path)}`;
  },
};
