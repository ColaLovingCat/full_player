<template>
  <div class="app-container">
    <audio ref="audioRef" :src="currentSong ? musicService.getAudioUrl(currentSong.path) : ''"
      @timeupdate="onTimeUpdate" @ended="onTrackEnded"></audio>

    <div class="app-background" :style="{ backgroundImage: `url(${currentAlbum?.cover})` }">
      <div class="overlay"></div>
    </div>

    <main class="music-app">
      <section class="concert-stage" @wheel.prevent="handleWheel">
        <!-- 专辑列表 -->
        <div class="album-shelf">
          <div v-for="(album, index) in albums" :key="index" class="album-card"
            :class="{ 'is-active': getStatus(index) }" :style="getCardStyle(index)" @mouseenter="hoverIndex = index"
            @mouseleave="hoverIndex = -1" @click="handleAlbumClick(index, album)" :ref="(el) => setAlbumRef(el, index)">
            <div class="cover-wrapper">
              <img :src="album.cover" alt="cover" />
            </div>
          </div>
        </div>
      </section>

      <section class="bottom-section">
        <div class="player-left">

          <!-- 歌曲信息 -->
          <div class="track-meta">
            <h1 class="title">{{ currentSong?.title || '未在播放' }}</h1>
            <p class="subtitle">{{ currentSong?.artist }} <span>『{{ currentSong?.album }}』</span></p>
            <p class="time">01:23 / 04:50</p>
          </div>

          <!-- 按钮组 -->
          <div class="track-btns">
            <div class="controls-view">
              <button class="btn btn-next" @click="prevSong()">
                <SkipBack />
              </button>
              <button class="btn btn-play" @click="togglePlay">
                <Play v-if="!isPlaying" />
                <Pause v-else />
              </button>
              <button class="btn btn-next" @click="nextSong(false)">
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

        <div class="player-right glass-card">

          <!-- 歌词 -->
          <div v-if="viewMode === 'lyrics'" class="lyrics-view">
            <div class="lyrics-wrapper" ref="lyricsContainer">
              <div class="lyrics-list" :style="{ transform: `translateY(${lyricOffset}px)` }">
                <p v-for="(line, index) in lyrics" :key="index"
                  :class="['lyric-line', { active: index === activeLyricIndex }]" :ref="(el) => setLyricRef(el, index)">
                  {{ line.text }}
                </p>
              </div>
            </div>
          </div>

          <!-- 歌曲列表 -->
          <div v-else class="playlist-container glass-panel">
            <ul class="song-list">
              <li v-for="(song, index) in currentAlbum?.songs" :key="song.id" class="song-item"
                :class="{ 'is-playing': currentSong?.id === song.id }" @dblclick="playSong(song)">
                <div class="col-index">
                  <span class="index-num" v-if="currentSong?.id !== song.id">{{ index + 1 }}</span>
                  <div class="playing-anim" v-else>
                    <span></span><span></span><span></span><span></span>
                  </div>
                  <Play class="hover-play-icon" @click.stop="playSong(song)" />
                </div>

                <!-- 歌曲信息 -->
                <div class="col-info">
                  <div class="song-name">{{ song.title }}</div>
                  <div class="song-artist">{{ song.artist }}</div>
                </div>

                <!-- 专辑信息 -->
                <div class="col-album">{{ song.album }}</div>

                <div class="col-time">
                  <span class="duration">{{ formatTime(song.duration) }}</span>
                  <div class="actions">
                    <Heart class="btn-icon heart-icon" :class="{ 'is-liked': song.isFavorite }"
                      :fill="song.isFavorite ? 'var(--accent-color)' : 'none'"
                      :color="song.isFavorite ? 'var(--accent-color)' : 'currentColor'"
                      @click.stop="toggleLike(song)" />
                  </div>
                </div>
              </li>
            </ul>

            <div class="controls-view">
              <!-- 播放模式 -->
              <button class="btn btn-scan" @click="toggleMode">
                <Repeat1 v-if="playMode === 'single'" />
                <Shuffle v-else-if="playMode === 'shuffle'" />
                <Repeat v-else />
              </button>

              <!-- 扫描 -->
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
import { ref, onMounted, computed, watch, nextTick, onBeforeUnmount } from 'vue';

import { Heart, Play, Pause, SkipForward, SkipBack, FileHeadphone, List, TextInitial, Shuffle, Repeat, Repeat1 } from 'lucide-vue-next';

import { musicService, type Album, type Song } from './services/musicService';

// 容器
const shelfRef = ref<HTMLElement | null>(null);
const albumRefs = ref<HTMLElement[]>([]);
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
  //
  window.addEventListener('keydown', onKeyPress);
});
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeyPress);
});

const onKeyPress = (e: KeyboardEvent) => {
  if (e.code === 'Space') {
    e.preventDefault();
    togglePlay()
  }
};

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

const setAlbumRef = (el: any, index: number) => {
  if (el) albumRefs.value[index] = el;
};
// 监听歌曲变化，自动滑动 Swiper 专辑列表
watch(currentAlbumIndex, async (newIndex) => {
  if (newIndex === -1 || !shelfRef.value || !albumRefs.value[newIndex]) return;

  await nextTick(); // 确保 DOM 已经更新

  const container = shelfRef.value;
  const targetCard = albumRefs.value[newIndex];

  // 计算：卡片距离容器左侧的距离 - 容器宽度的一半 + 卡片自身宽度的一半
  // 这样就能刚好让这卡片显示在容器正中间
  const scrollPosition = targetCard.offsetLeft - (container.clientWidth / 2) + (targetCard.clientWidth / 2);

  // 执行平滑滚动
  container.scrollTo({
    left: scrollPosition,
    behavior: 'smooth'
  });
});

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
const nextSong = (isAuto: boolean = false) => {
  if (playlist.value.length === 0) return;

  // 只有 1 首歌时，永远是单曲循环
  if (playlist.value.length === 1) {
    replayCurrentSong();
    return;
  }

  // 模式：单曲循环 且 是自然播完 -> 重新播放当前歌曲
  if (playMode.value === 'single' && isAuto) {
    replayCurrentSong();
  }
  // 模式：随机播放 -> 找一个不是当前索引的随机数
  else if (playMode.value === 'shuffle') {
    let randomIndex = Math.floor(Math.random() * playlist.value.length);
    while (randomIndex === currentSongIndex.value) {
      randomIndex = Math.floor(Math.random() * playlist.value.length);
    }
    currentSongIndex.value = randomIndex;
  }
  // 模式：列表循环 (或者单曲循环下手动点击下一首) -> 顺序 +1
  else {
    currentSongIndex.value = (currentSongIndex.value + 1) % playlist.value.length;
  }
};

// 5. 上一首
let isBacking = false; // 用于标记当前是否是在执行“回退(上一首)”操作
const historyStack = ref<number[]>([]);
const prevSong = () => {
  if (playlist.value.length === 0) return;

  // 1. 尝试从历史栈中弹出最后一个走过的索引
  if (historyStack.value.length > 0) {
    const prevIndex = historyStack.value.pop(); // 拿到真正的“上一首”

    // 如果这个索引有效
    if (prevIndex !== undefined && prevIndex >= 0 && prevIndex < playlist.value.length) {
      isBacking = true; // 告诉 watch：这是在回退，不要往历史里记当前歌了
      currentSongIndex.value = prevIndex;
      return;
    }
  }

  // 2. 兜底方案：如果历史栈为空（刚开软件），退化为默认的向前推一首
  if (playMode.value === 'shuffle') {
    // 随机模式下如果没有历史，就随便跳一首
    let randomIndex = Math.floor(Math.random() * playlist.value.length);
    while (randomIndex === currentSongIndex.value && playlist.value.length > 1) {
      randomIndex = Math.floor(Math.random() * playlist.value.length);
    }
    currentSongIndex.value = randomIndex;
  } else {
    // 顺序或循环模式，正常 -1
    currentSongIndex.value = (currentSongIndex.value - 1 + playlist.value.length) % playlist.value.length;
  }
};

const replayCurrentSong = () => {
  if (audioRef.value) {
    audioRef.value.currentTime = 0; // 进度条归零
    audioRef.value.play();          // 重新开始播放
  }
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
  nextSong(true);
};

watch(currentSong, async (newSong, oldSong) => {
  if (!newSong) return;

  // --- 重点：记录历史 ---
  // 1. 如果不是回退操作，且之前有歌，就把“上一首歌”的索引压入历史栈
  // 注意：存的是 oldSong 在当前 playlist 里的索引（可以通过 oldSong.id 找）
  if (!isBacking && oldSong) {
    const oldIndex = playlist.value.findIndex(s => s.id === oldSong.id);
    if (oldIndex !== -1) {
      historyStack.value.push(oldIndex);
      // 限制历史长度，比如最多记 50 首，防止内存泄漏
      if (historyStack.value.length > 50) historyStack.value.shift();
    }
  }

  // 重置标志位
  isBacking = false;

  // --- 获取歌词和播放的逻辑 (保持不变) ---
  if (newSong.lyricsPath) {
    try { lyrics.value = await musicService.getLyrics(newSong.lyricsPath); }
    catch { lyrics.value = []; }
  } else {
    lyrics.value = [];
  }

  await nextTick();

  if (audioRef.value) {
    audioRef.value.play().then(() => isPlaying.value = true).catch(() => isPlaying.value = false);
  }
});

// --- Toggle ---
const viewMode = ref<'lyrics' | 'list'>('lyrics');
const toggleRight = () => { viewMode.value = viewMode.value == 'list' ? 'lyrics' : 'list' }

// --- 喜欢/点赞 交互逻辑 ---
const toggleLike = async (song: Song) => {
  try {
    // 1. 调用后端接口
    const newStatus = await musicService.toggleFavorite(song.id);

    // 2. 更新当前列表里这首歌的状态 (让红心变色)
    song.isFavorite = newStatus;

    // 3. 动态维护“我的最爱”专辑 (索引 0)
    const favAlbum = albums.value[0];
    if (newStatus) {
      // 喜欢：如果列表里没有，就加进去
      if (!favAlbum.songs.find((s: Song) => s.id === song.id)) {
        favAlbum.songs.push(song);
        // 如果是第一首歌，顺便更新封面
        if (favAlbum.songs.length === 1) favAlbum.cover = song.albumCover;
      }
    } else {
      // 取消喜欢：从列表里移除
      favAlbum.songs = favAlbum.songs.filter((s: Song) => s.id !== song.id);
      // 如果没歌了，恢复默认封面
      if (favAlbum.songs.length === 0) favAlbum.cover = '/default-heart-cover.png';
    }
  } catch (error) {
    console.error("点赞失败:", error);
  }
};

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
    const offsetTop = activeElement.offsetTop;
    lyricOffset.value = -offsetTop + 200;
  }
});

const formatTime = (seconds: number | undefined | null): string => {
  if (!seconds || isNaN(seconds) || seconds < 0) return '00:00';

  const MathFloor = Math.floor(seconds);

  const h = Math.floor(MathFloor / 3600);
  const m = Math.floor((MathFloor % 3600) / 60);
  const s = MathFloor % 60;

  const mStr = m.toString().padStart(2, '0');
  const sStr = s.toString().padStart(2, '0');

  if (h > 0) {
    const hStr = h.toString().padStart(2, '0');
    return `${hStr}:${mStr}:${sStr}`;
  }

  return `${mStr}:${sStr}`;
};
</script>

<style lang="scss" scoped>
@import "./assets/main.scss";
</style>