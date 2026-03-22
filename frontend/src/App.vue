<template>
  <div class="app-container">
    <audio ref="audioRef" :src="currentSong ? musicService.getAudioUrl(currentSong.path) : ''"
      @timeupdate="onTimeUpdate" @ended="onTrackEnded"></audio>

    <div class="app-background" :style="{ backgroundImage: `url(${currentAlbum?.cover})` }">
      <div class="overlay"></div>
    </div>

    <main class="music-app">
      <section class="concert-stage" @wheel.prevent="handleWheel">
        <div class="album-shelf">
          <div v-for="(album, index) in albums" :key="index" class="album-card"
            :class="{ 'is-active': getStatus(index) }" :style="getCardStyle(index)" @mouseenter="hoverIndex = index"
            @mouseleave="hoverIndex = -1" @click="handleAlbumClick(index, album)">
            <div class="cover-wrapper">
              <img :src="album.cover" alt="cover" />
            </div>
          </div>
        </div>
      </section>

      <section class="bottom-section">
        <!-- 左半部：歌曲信息 -->
        <div class="player-left">
          <div class="track-meta">
            <h1 class="title">{{ currentSong?.title || '未在播放' }}</h1>
            <p class="subtitle">{{ currentSong?.artist }} <span>『{{ currentSong?.album }}』</span></p>
            <p class="time">01:23 / 04:50</p>
          </div>

          <div class="track-btns">
            <div class="controls-view">
              <button class="btn btn-play" @click="togglePlay">
                <Play v-if="!isPlaying" />
                <Pause v-else />
              </button>
              <button class="btn btn-next" @click="nextSong">
                <SkipForward />
              </button>
              <button class="btn btn-view" @click="toggleRight" v-if="viewMode === 'lyrics'">
                <TextInitial />
              </button>
              <button class="btn btn-view" @click="toggleRight" v-else>
                <List />
              </button>
            </div>
            <div class="progress-container">
              <div class="progress-bar">
                <div class="progress-fill" style="width: 45%"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右半部：歌词或列表 -->
        <div class="player-right glass-card">
          <div v-if="viewMode === 'lyrics'" class="lyrics-view">
            <div class="lyrics-wrapper" ref="lyricsContainer">
              <!-- 内部长列表，通过 transform 实现滚动 -->
              <div class="lyrics-list" :style="{ transform: `translateY(${lyricOffset}px)` }">
                <p v-for="(line, index) in lyrics" :key="index"
                  :class="['lyric-line', { active: index === activeLyricIndex }]" :ref="(el) => setLyricRef(el, index)">
                  {{ line.text }}
                </p>
              </div>
            </div>
          </div>

          <div v-else class="playlist-container glass-panel">
            <!-- 歌曲列表 -->
            <ul class="song-list">
              <li v-for="(song, index) in currentAlbum?.songs" :key="song.id" class="song-item"
                :class="{ 'is-playing': currentSong?.id === song.id }" @dblclick="playSong(song)">
                <!-- 序号 / 播放动画 / Hover播放键 -->
                <div class="col-index">
                  <span class="index-num" v-if="currentSong?.id !== song.id">{{ index + 1 }}</span>
                  <!-- 播放时的动态频谱动画 -->
                  <div class="playing-anim" v-else>
                    <span></span><span></span><span></span><span></span>
                  </div>
                  <!-- Hover时显示的播放图标 -->
                  <Play class="hover-play-icon" @click.stop="playSong(song)" />
                </div>

                <!-- 歌曲信息 -->
                <div class="col-info">
                  <div class="song-name">{{ song.title }}</div>
                  <div class="song-artist">{{ song.artist }}</div>
                </div>

                <!-- 专辑信息 -->
                <div class="col-album">{{ song.album }}</div>

                <!-- 时长 & 隐藏的操作按钮 -->
                <div class="col-time">
                  <span class="duration">{{ formatTime(song.duration) }}</span>
                  <div class="actions">
                    <Heart class="btn-icon" />
                  </div>
                </div>
              </li>
            </ul>

            <div class="controls-view">
              <button class="btn btn-scan" @click="toggleMode">
                <Repeat1 v-if="playMode === 'single'" />
                <Shuffle v-else-if="playMode === 'shuffle'" />
                <Repeat v-else />
              </button>
              <button class="btn btn-play" @click="scan">
                <FileHeadphone />
              </button>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';

import { Heart, Play, Pause, SkipForward, FileHeadphone, List, TextInitial, Shuffle, Repeat, Repeat1 } from 'lucide-vue-next';

import { musicService, type Album, type Song } from './services/musicService';

const audioRef = ref<HTMLAudioElement | null>(null);

// --- 状态变量 ---
const albums = ref<Album[]>([]);

const currentAlbumIndex = ref(0);
const currentAlbum = computed(() => albums.value[currentAlbumIndex.value]);

const playlist = ref<Song[]>([]);
const currentSongIndex = ref(-1);
const currentSong = computed(() => playlist.value[currentSongIndex.value] || null);
//
const isPlaying = ref(false);
const currentTime = ref(0);            // 当前播放秒数
const lyrics = ref<{ time: number, text: string }[]>([]);

// --- 初始化 ---
onMounted(async () => {
  loadSongs()
});

const hoverIndex = ref(-1);
const getStatus = (index: number) => {
  if (hoverIndex.value > -1) return false
  return currentAlbumIndex.value === index
}
const getCardStyle = (index: number) => {
  let pushX = 0; // 默认不偏移

  if (hoverIndex.value !== -1) {
    if (index < hoverIndex.value) {
      // 在悬浮元素左边的，往左挤开 30px
      pushX = -30;
    } else if (index > hoverIndex.value) {
      // 在悬浮元素右边的，往右挤开 30px
      pushX = 30;
    }
  }

  return {
    '--i': index,            // 用于计算 z-index (左边压盖右边)
    '--push-x': `${pushX}px` // 传递给 CSS 的挤开偏移量
  };
};
const handleAlbumClick = (index: number, album: any) => {
  // 点击即设为活跃专辑（抽出状态）
  currentAlbumIndex.value = index;

  // 执行播放逻辑
  playAlbum(album);
};
const wallOffset = ref(0);
const handleWheel = (e: WheelEvent) => {
  // 每次滚动移动墙面，实现丝滑浏览
  wallOffset.value += e.deltaY > 0 ? -100 : 100;
  // 限制滚动边界 (假设最多滚动长度)
  const maxScroll = -(albums.value.length * 50);
  if (wallOffset.value > 0) wallOffset.value = 0;
  if (wallOffset.value < maxScroll) wallOffset.value = maxScroll;
};

const scan = async () => {
  await musicService.triggerScan()
  loadSongs()
}
const loadSongs = async () => {
  albums.value = await musicService.getAlbumsWithSongs();
}

// 播放方式
const playMode = ref<'single' | 'loop' | 'shuffle'>('shuffle');
const toggleMode = () => {
  if (playMode.value === 'loop') { playMode.value = "shuffle"; return }
  if (playMode.value === 'shuffle') { playMode.value = "single"; return }
  if (playMode.value === 'single') { playMode.value = "loop"; return }
}

// --- 核心方法 ---
const playAlbum = (album: Album) => {
  playlist.value = [...album.songs];
  currentSongIndex.value = 0;
  startPlay();
};
const playSong = (song: Song) => {
  // A. 如果点击的是当前正在播放的歌，就执行 暂停/继续
  if (currentSong.value?.id === song.id) {
    togglePlay();
    return;
  }

  // B. 如果点击了新歌，重置播放列表为当前浏览的专辑
  const songIndex = playlist.value.findIndex(a => a.id == song.id)
  if (songIndex > -1) {
    currentSongIndex.value = songIndex;
    startPlay();
    return
  }

  // C. 如果点击了新歌，重置播放列表为当前浏览的专辑
  const albumIndex = albums.value.findIndex(a => a.name == song.album)
  if (albumIndex > -1) {
    currentAlbumIndex.value = albumIndex
    playlist.value = [...albums.value[albumIndex].songs]
    //
    const index = playlist.value.findIndex(a => a.id == song.id)
    currentSongIndex.value = index;
    startPlay();
    return
  }
};

// 2. 播放/暂停 切换
const togglePlay = () => {
  if (!audioRef.value) return;
  if (isPlaying.value) {
    audioRef.value.pause();
  } else {
    audioRef.value.play();
  }
  isPlaying.value = !isPlaying.value;
};

// 3. 播放指定索引的歌曲
const startPlay = async () => {
  isPlaying.value = true;
  // 获取歌词
  if (currentSong.value?.lyricsPath) {
    lyrics.value = await musicService.getLyrics(currentSong.value.lyricsPath);
  } else {
    lyrics.value = [];
  }
  // 在 DOM 更新后自动播放
  setTimeout(() => audioRef.value?.play(), 100);
};

// 4. 下一首
const nextSong = () => {
  if (currentSongIndex.value < playlist.value.length - 1) {
    currentSongIndex.value++;
  } else {
    currentSongIndex.value = 0; // 列表循环
  }
  startPlay();
};

// 5. 上一首
const prevSong = () => {
  if (currentSongIndex.value > 0) {
    currentSongIndex.value--;
  } else {
    currentSongIndex.value = playlist.value.length - 1;
  }
  startPlay();
};

// --- 音频事件处理 ---
const onTimeUpdate = () => {
  if (audioRef.value) {
    currentTime.value = audioRef.value.currentTime;
    //
    let index = -1
    for (let i = lyrics.value.length - 1; i >= 0; i--) {
      const time: any = lyrics.value[i].time
      if (time <= currentTime.value) {
        index = i
        break
      }
    }
    if (index !== -1 && index !== activeLyricIndex.value) {
      activeLyricIndex.value = index;
    }
  }
};

const onTrackEnded = () => {
  nextSong();
};

//
const viewMode = ref<'lyrics' | 'list'>('lyrics');
const toggleRight = () => { viewMode.value = viewMode.value == 'list' ? 'lyrics' : 'list' }

// --- 歌词高亮逻辑 ---
const lyricRefs = ref<HTMLElement[]>([]);
const setLyricRef = (el: any, index: number) => {
  if (el) lyricRefs.value[index] = el;
};

const lyricOffset = ref(0);
const activeLyricIndex = ref(0);

// 监听索引变化，精准计算偏移
watch(activeLyricIndex, (newIdx) => {
  if (newIdx >= 0 && lyricRefs.value[newIdx]) {
    const activeElement = lyricRefs.value[newIdx];
    // 计算该元素距离列表顶部的距离
    const offsetTop = activeElement.offsetTop;
    // 列表向上移动该距离
    lyricOffset.value = -offsetTop + 200;
  }
});

// 监听歌曲变化，自动滑动 Swiper 专辑列表
watch(currentSong, (newSong) => {
  if (newSong) {
    const albumIdx = albums.value.findIndex(a => a.name === newSong.album);
    if (albumIdx !== -1 && albumIdx !== currentAlbumIndex.value) {
      currentAlbumIndex.value = albumIdx;
    }
  }
});

const formatTime = (seconds: number | undefined | null): string => {
  if (!seconds || isNaN(seconds) || seconds < 0) return '00:00';

  const MathFloor = Math.floor(seconds);

  const h = Math.floor(MathFloor / 3600); // 3600秒 = 1小时
  const m = Math.floor((MathFloor % 3600) / 60);
  const s = MathFloor % 60;

  const mStr = m.toString().padStart(2, '0');
  const sStr = s.toString().padStart(2, '0');

  // 如果有小时，才拼上小时
  if (h > 0) {
    const hStr = h.toString().padStart(2, '0');
    return `${hStr}:${mStr}:${sStr}`;
  }

  // 普通歌曲只显示分:秒
  return `${mStr}:${sStr}`;
};
</script>

<style lang="scss" scoped>
@import "./assets/main.scss";
</style>