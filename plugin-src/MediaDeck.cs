using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using BepInEx;
using Newtonsoft.Json;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.Video;

namespace Barros.PizzaCreator.AI
{
    public sealed class MediaTrack
    {
        public string Path = "";
        public string Title = "";
        public bool IsVideo;
    }

    public sealed class MediaDeck : MonoBehaviour
    {
        private readonly List<MediaTrack> tracks = new List<MediaTrack>();
        private readonly List<string> playlist = new List<string>();
        private AudioSource musicSource;
        private AudioSource videoAudioSource;
        private VideoPlayer videoPlayer;
        private RenderTexture videoTexture;
        private EvidenceRecorder evidence;
        private GameBridge game;
        private AudioClip loadedClip;
        private float[] cachedWaveform = new float[0];
        private int currentIndex = -1;
        private bool loading;
        private bool shuffle;
        private bool repeat;
        private bool autoImport = true;
        private bool paused;
        private bool audioReachedPlayback;
        private bool barrosReplacesStock = true;
        private bool playlistLoaded;
        private bool speechFocusActive;
        private bool resumeMusicAfterSpeech;
        private bool resumeVideoAfterSpeech;
        private bool pausedBeforeSpeech;
        private float playbackStartDeadline;
        private float volume = 0.75f;
        private float bassDb;
        private float midDb;
        private float trebleDb;
        private string status = "Drop OGG, MP3, WAV, or MP4 files into BarrosAI/assets/music.";

        public List<MediaTrack> Tracks { get { return tracks; } }
        public int CurrentIndex { get { return currentIndex; } }
        public int PlaylistCount { get { return playlist.Count; } }
        public bool Loading { get { return loading; } }
        public bool Shuffle { get { return shuffle; } set { shuffle = value; } }
        public bool Repeat { get { return repeat; } set { repeat = value; } }
        public bool AutoImport { get { return autoImport; } set { autoImport = value; } }
        public bool BarrosReplacesStock { get { return barrosReplacesStock; } }
        public string Status { get { return status; } }
        public void SetStatus(string value)
        {
            if (!string.IsNullOrEmpty(value)) status = value;
        }
        public string CurrentTitle
        {
            get
            {
                if (!barrosReplacesStock) return "Pizza Creator stock soundtrack";
                return currentIndex >= 0 && currentIndex < tracks.Count ? tracks[currentIndex].Title : "No track selected";
            }
        }
        public string ImportFolder { get { return Path.Combine(BepInEx.Paths.GameRootPath, "BarrosAI", "assets", "music", "imports"); } }
        public string PlaylistFile { get { return Path.Combine(BepInEx.Paths.GameRootPath, "BarrosAI", "data", "music-playlist.json"); } }
        public string ConversionReportFile { get { return Path.Combine(BepInEx.Paths.GameRootPath, "BarrosAI", "assets", "music", "conversion-report.json"); } }
        public string NextTitle
        {
            get
            {
                int next = NextPlaylistIndex(currentIndex, 1);
                return next >= 0 && next < tracks.Count ? tracks[next].Title : "None";
            }
        }
        public Texture VideoTexture { get { return videoTexture; } }
        public bool ShowingVideo { get { return barrosReplacesStock && videoPlayer != null && videoPlayer.isPrepared && videoPlayer.isPlaying; } }
        public bool IsPlaying
        {
            get
            {
                if (!barrosReplacesStock) return musicSource != null && musicSource.isPlaying;
                return (musicSource != null && loadedClip != null && musicSource.clip == loadedClip && musicSource.isPlaying)
                    || (videoPlayer != null && videoPlayer.isPlaying);
            }
        }
        public float Volume
        {
            get { return volume; }
            set
            {
                float next = Mathf.Clamp01(value);
                if (Mathf.Abs(next - volume) < 0.002f) return;
                volume = next;
                if (game != null) game.SetMusicVolume(volume);
            }
        }
        public float BassDb
        {
            get { return bassDb; }
            set { float next = Mathf.Clamp(value, -12f, 12f); if (Mathf.Abs(next - bassDb) < 0.02f) return; bassDb = next; ApplyTone(); }
        }
        public float MidDb
        {
            get { return midDb; }
            set { float next = Mathf.Clamp(value, -12f, 12f); if (Mathf.Abs(next - midDb) < 0.02f) return; midDb = next; ApplyTone(); }
        }
        public float TrebleDb
        {
            get { return trebleDb; }
            set { float next = Mathf.Clamp(value, -12f, 12f); if (Mathf.Abs(next - trebleDb) < 0.02f) return; trebleDb = next; ApplyTone(); }
        }
        public float Progress
        {
            get
            {
                if (videoPlayer != null && videoPlayer.isPrepared && videoPlayer.frameCount > 1)
                    return Mathf.Clamp01((float)videoPlayer.frame / (float)(videoPlayer.frameCount - 1));
                AudioClip active = barrosReplacesStock ? loadedClip : (musicSource == null ? null : musicSource.clip);
                if (musicSource != null && active != null && musicSource.clip == active && active.length > 0.01f)
                    return Mathf.Clamp01(musicSource.time / active.length);
                return 0f;
            }
            set
            {
                value = Mathf.Clamp01(value);
                if (videoPlayer != null && videoPlayer.isPrepared && videoPlayer.frameCount > 1)
                    videoPlayer.frame = (long)((videoPlayer.frameCount - 1) * value);
                else
                {
                    AudioClip active = barrosReplacesStock ? loadedClip : (musicSource == null ? null : musicSource.clip);
                    if (musicSource != null && active != null && musicSource.clip == active) musicSource.time = active.length * value;
                }
            }
        }

        public void Configure(EvidenceRecorder recorder, GameBridge bridge)
        {
            evidence = recorder;
            game = bridge;
            musicSource = game == null ? null : game.GetMusicSource();
            videoAudioSource = GetComponent<AudioSource>();
            if (videoAudioSource == null) videoAudioSource = gameObject.AddComponent<AudioSource>();
            videoAudioSource.playOnAwake = false;
            videoAudioSource.volume = volume;
            videoPlayer = GetComponent<VideoPlayer>();
            if (videoPlayer == null) videoPlayer = gameObject.AddComponent<VideoPlayer>();
            videoPlayer.playOnAwake = false;
            videoPlayer.audioOutputMode = VideoAudioOutputMode.AudioSource;
            videoPlayer.SetTargetAudioSource(0, videoAudioSource);
            videoPlayer.errorReceived += OnVideoError;
            videoPlayer.loopPointReached += OnVideoEnded;
            videoTexture = new RenderTexture(640, 360, 0, RenderTextureFormat.ARGB32);
            videoTexture.name = "Barros Media Deck Video";
            videoPlayer.renderMode = VideoRenderMode.RenderTexture;
            videoPlayer.targetTexture = videoTexture;
            Refresh();
            if (tracks.Count > 0) StartCoroutine(AutoStartBackground());
        }

        public void Refresh()
        {
            tracks.Clear();
            string root = Path.Combine(BepInEx.Paths.GameRootPath, "BarrosAI", "assets", "music");
            try
            {
                Directory.CreateDirectory(root);
                Directory.CreateDirectory(ImportFolder);
                string[] files = Directory.GetFiles(root, "*.*", SearchOption.TopDirectoryOnly);
                Array.Sort(files, StringComparer.OrdinalIgnoreCase);
                for (int i = 0; i < files.Length; i++)
                {
                    string extension = Path.GetExtension(files[i]).ToLowerInvariant();
                    if (extension != ".ogg" && extension != ".mp3" && extension != ".wav" && extension != ".mp4") continue;
                    if (extension == ".mp3" && File.Exists(Path.ChangeExtension(files[i], ".ogg"))) continue;
                    MediaTrack track = new MediaTrack();
                    track.Path = files[i];
                    track.Title = FriendlyTitle(Path.GetFileNameWithoutExtension(files[i]));
                    track.IsVideo = extension == ".mp4";
                    tracks.Add(track);
                }
                if (!playlistLoaded) LoadPlaylistInternal();
                else RemoveMissingPlaylistEntries();
                status = tracks.Count == 0
                    ? "The media folder is ready. Add OGG, MP3, WAV, or MP4 files, then press Refresh."
                    : tracks.Count + " Barro's track" + (tracks.Count == 1 ? "" : "s") + " ready.";
            }
            catch (Exception exception) { status = "Music scan failed: " + exception.Message; }
        }

        public void Select(int index)
        {
            if (index < 0 || index >= tracks.Count || loading) return;
            barrosReplacesStock = true;
            StartCoroutine(LoadAndPlay(index));
        }

        private IEnumerator AutoStartBackground()
        {
            yield return new WaitForSeconds(2.5f);
            if (barrosReplacesStock && currentIndex < 0 && tracks.Count > 0) PlayBarrosPlaylist();
        }

        public void PlayBarrosPlaylist()
        {
            if (loading || tracks.Count == 0 || playlist.Count == 0)
            {
                status = tracks.Count == 0 ? "No music files are available." : "The saved play queue is empty. Add a song from the library first.";
                return;
            }
            barrosReplacesStock = true;
            int selected = currentIndex >= 0 && currentIndex < tracks.Count && IsQueued(currentIndex)
                ? currentIndex
                : NextPlaylistIndex(-1, 1);
            if (selected >= 0) Select(selected);
        }

        public bool IsQueued(int index)
        {
            if (index < 0 || index >= tracks.Count) return false;
            return playlist.Contains(Path.GetFileName(tracks[index].Path));
        }

        public int QueuePosition(int index)
        {
            if (index < 0 || index >= tracks.Count) return -1;
            return playlist.IndexOf(Path.GetFileName(tracks[index].Path));
        }

        public void ToggleQueued(int index)
        {
            if (index < 0 || index >= tracks.Count) return;
            string file = Path.GetFileName(tracks[index].Path);
            int existing = playlist.IndexOf(file);
            if (existing >= 0)
            {
                playlist.RemoveAt(existing);
                status = "Removed " + tracks[index].Title + " from the startup queue. The file remains in the library.";
            }
            else
            {
                playlist.Add(file);
                status = "Added " + tracks[index].Title + " to the end of the startup queue.";
            }
        }

        public void MoveQueued(int index, int direction)
        {
            int position = QueuePosition(index);
            if (position < 0 || playlist.Count < 2) return;
            int destination = Mathf.Clamp(position + direction, 0, playlist.Count - 1);
            if (destination == position) return;
            string value = playlist[position];
            playlist.RemoveAt(position);
            playlist.Insert(destination, value);
            status = "Moved " + tracks[index].Title + " to queue position " + (destination + 1) + ".";
        }

        public void SelectAll()
        {
            playlist.Clear();
            for (int i = 0; i < tracks.Count; i++) playlist.Add(Path.GetFileName(tracks[i].Path));
            status = "All " + playlist.Count + " tracks are in the startup queue.";
        }

        public void ClearPlaylist()
        {
            playlist.Clear();
            status = "The startup queue is empty. Music files remain safely in the library.";
        }

        public void SavePlaylist()
        {
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(PlaylistFile));
                MediaPlaylistState state = new MediaPlaylistState();
                state.Queue.AddRange(playlist);
                state.Shuffle = shuffle;
                state.Repeat = repeat;
                state.Volume = volume;
                state.BassDb = bassDb;
                state.MidDb = midDb;
                state.TrebleDb = trebleDb;
                state.AutoImport = autoImport;
                state.UseBarros = barrosReplacesStock;
                File.WriteAllText(PlaylistFile, JsonConvert.SerializeObject(state, Formatting.Indented));
                status = "Saved this play order for Pizza Creator startup.";
                if (evidence != null) evidence.Record("media.playlist_saved", "tracks=" + playlist.Count + "; shuffle=" + shuffle + "; repeat=" + repeat);
            }
            catch (Exception exception) { status = "Playlist save failed: " + exception.Message; }
        }

        public void LoadPlaylist()
        {
            playlistLoaded = false;
            playlist.Clear();
            LoadPlaylistInternal();
            status = "Reloaded the saved startup queue with " + playlist.Count + " track" + (playlist.Count == 1 ? "" : "s") + ".";
        }

        public long InboxRevision()
        {
            try
            {
                Directory.CreateDirectory(ImportFolder);
                long revision = 17;
                string[] files = Directory.GetFiles(ImportFolder, "*.*", SearchOption.TopDirectoryOnly);
                Array.Sort(files, StringComparer.OrdinalIgnoreCase);
                for (int i = 0; i < files.Length; i++)
                {
                    string extension = Path.GetExtension(files[i]).ToLowerInvariant();
                    if (extension != ".ogg" && extension != ".mp3" && extension != ".wav" && extension != ".flac" && extension != ".m4a" && extension != ".aac" && extension != ".wma") continue;
                    FileInfo info = new FileInfo(files[i]);
                    unchecked { revision = revision * 31 + info.Length + info.LastWriteTimeUtc.Ticks; }
                }
                return revision;
            }
            catch { return 0; }
        }

        public void PlayStockMusic()
        {
            if (loading || game == null) return;
            StopPlayback();
            ReleaseLoadedClip();
            barrosReplacesStock = false;
            game.PlayStockCreatorMusic();
            musicSource = game.GetMusicSource();
            status = "Playing the original Pizza Creator soundtrack.";
        }

        public void TogglePlay()
        {
            if (loading) return;
            if (currentIndex < 0)
            {
                if (tracks.Count > 0) Select(0);
                return;
            }
            if (videoPlayer != null && videoPlayer.isPrepared && tracks[currentIndex].IsVideo)
            {
                if (videoPlayer.isPlaying) videoPlayer.Pause(); else videoPlayer.Play();
            }
            else if (musicSource != null && game != null)
            {
                if (musicSource.isPlaying)
                {
                    game.PauseMusic();
                    paused = true;
                    status = "Paused " + CurrentTitle;
                }
                else
                {
                    game.ResumeMusic();
                    paused = false;
                    if (barrosReplacesStock)
                    {
                        audioReachedPlayback = false;
                        playbackStartDeadline = Time.realtimeSinceStartup + 4f;
                        status = "Starting " + CurrentTitle + "…";
                    }
                    else status = "Playing " + CurrentTitle + ".";
                }
            }
        }

        public void StopPlayback()
        {
            if (barrosReplacesStock && game != null) game.StopMusic();
            if (videoAudioSource != null) videoAudioSource.Stop();
            if (videoPlayer != null) videoPlayer.Stop();
            paused = false;
            audioReachedPlayback = false;
            status = currentIndex >= 0 ? "Stopped " + tracks[currentIndex].Title : "Stopped.";
        }

        public void BeginSpeechFocus()
        {
            if (speechFocusActive) return;
            speechFocusActive = true;
            pausedBeforeSpeech = paused;
            paused = true;
            resumeMusicAfterSpeech = musicSource != null && musicSource.isPlaying;
            resumeVideoAfterSpeech = videoPlayer != null && videoPlayer.isPlaying;
            if (resumeMusicAfterSpeech && game != null) game.PauseMusic();
            if (resumeVideoAfterSpeech) videoPlayer.Pause();
            status = "Music paused for agent voice.";
            if (evidence != null) evidence.Record("media.speech_focus_started", "resume_music=" + resumeMusicAfterSpeech + "; resume_video=" + resumeVideoAfterSpeech);
        }

        public void EndSpeechFocus()
        {
            if (!speechFocusActive) return;
            speechFocusActive = false;
            if (resumeMusicAfterSpeech && game != null) game.ResumeMusic();
            if (resumeVideoAfterSpeech && videoPlayer != null && videoPlayer.isPrepared) videoPlayer.Play();
            bool resumed = resumeMusicAfterSpeech || resumeVideoAfterSpeech;
            resumeMusicAfterSpeech = false;
            resumeVideoAfterSpeech = false;
            paused = pausedBeforeSpeech;
            status = resumed ? "Agent finished · background music resumed." : "Agent finished · music remains stopped.";
            if (evidence != null) evidence.Record("media.speech_focus_ended", "resumed=" + resumed);
        }

        public void Previous() { Move(-1); }
        public void Next() { Move(1); }

        public float[] GetWaveform(int bins)
        {
            bins = Mathf.Clamp(bins, 16, 128);
            if (cachedWaveform.Length == bins) return cachedWaveform;
            float[] waveform = new float[bins];
            if (!barrosReplacesStock || cachedWaveform.Length == 0) return waveform;
            for (int bin = 0; bin < bins; bin++)
            {
                int source = Mathf.Clamp(bin * cachedWaveform.Length / bins, 0, cachedWaveform.Length - 1);
                waveform[bin] = cachedWaveform[source];
            }
            return waveform;
        }

        private void CacheWaveform(int bins)
        {
            bins = Mathf.Clamp(bins, 16, 128);
            float[] waveform = new float[bins];
            cachedWaveform = waveform;
            AudioClip waveformClip = loadedClip;
            if (waveformClip == null || waveformClip.loadState != AudioDataLoadState.Loaded) return;
            int channels = Mathf.Max(1, waveformClip.channels);
            float[] sample = new float[256 * channels];
            for (int bin = 0; bin < bins; bin++)
            {
                int offset = Mathf.Clamp((waveformClip.samples - 257) * bin / Mathf.Max(1, bins - 1), 0, Mathf.Max(0, waveformClip.samples - 257));
                if (!waveformClip.GetData(sample, offset)) break;
                float peak = 0f;
                for (int i = 0; i < sample.Length; i++) peak = Mathf.Max(peak, Mathf.Abs(sample[i]));
                waveform[bin] = peak;
            }
        }

        private IEnumerator LoadAndPlay(int index)
        {
            loading = true;
            StopPlayback();
            ReleaseLoadedClip();
            currentIndex = index;
            cachedWaveform = new float[0];
            MediaTrack track = tracks[index];
            status = "Loading " + track.Title + "…";
            if (track.IsVideo)
            {
                if (game != null) game.StopMusic();
                videoPlayer.source = VideoSource.Url;
                videoPlayer.url = new Uri(track.Path).AbsoluteUri;
                videoPlayer.EnableAudioTrack(0, true);
                videoPlayer.Prepare();
                float started = Time.realtimeSinceStartup;
                while (!videoPlayer.isPrepared && Time.realtimeSinceStartup - started < 20f) yield return null;
                loading = false;
                if (!videoPlayer.isPrepared)
                {
                    status = "This MP4 could not be prepared by the Unity 2017 video decoder.";
                    yield break;
                }
                videoPlayer.Play();
            }
            else
            {
                string audioUrl = "http://127.0.0.1:48173/music/playback/" + Uri.EscapeDataString(Path.GetFileName(track.Path));
                using (WWW request = new WWW(audioUrl))
                {
                    // Unity 2017's WWW compatibility API exposes the stream
                    // choice omitted by DownloadHandlerAudioClip in this exact
                    // build. Both flags are false: 2D and non-streaming.
                    yield return request;
                    if (!string.IsNullOrEmpty(request.error))
                    {
                        loading = false;
                        status = "Audio load failed: " + request.error;
                        yield break;
                    }
                    loadedClip = request.GetAudioClip(false, false, AudioType.WAV);
                }
                if (loadedClip == null || loadedClip.length <= 0.01f)
                {
                    loading = false;
                    status = "Unity could not decode " + Path.GetExtension(track.Path).ToUpperInvariant() + ".";
                    yield break;
                }
                if (loadedClip.loadState == AudioDataLoadState.Unloaded) loadedClip.LoadAudioData();
                float loadStarted = Time.realtimeSinceStartup;
                while (loadedClip != null && loadedClip.loadState == AudioDataLoadState.Loading && Time.realtimeSinceStartup - loadStarted < 20f)
                    yield return null;
                if (loadedClip == null || loadedClip.loadState != AudioDataLoadState.Loaded)
                {
                    loading = false;
                    status = "The soundtrack could not be fully loaded into memory.";
                    ReleaseLoadedClip();
                    yield break;
                }
                loadedClip.name = track.Title;
                CacheWaveform(52);
                if (game == null)
                {
                    loading = false;
                    status = "The native Pizza Creator music service is unavailable.";
                    ReleaseLoadedClip();
                    yield break;
                }
                loading = false;
                game.StartBarrosMusic(loadedClip, volume);
                game.SetMusicTone(bassDb, midDb, trebleDb);
                musicSource = game.GetMusicSource();
                paused = false;
                audioReachedPlayback = false;
                playbackStartDeadline = Time.realtimeSinceStartup + 8f;
            }
            status = "Playing " + track.Title;
            if (evidence != null) evidence.Record("media.play", "title=" + track.Title + "; type=" + Path.GetExtension(track.Path).ToLowerInvariant());
        }

        private void Update()
        {
            if (loading || !barrosReplacesStock || currentIndex < 0 || tracks[currentIndex].IsVideo || loadedClip == null) return;
            if (game != null) musicSource = game.GetMusicSource();
            if (musicSource == null || musicSource.clip != loadedClip) return;
            if (musicSource.isPlaying)
            {
                if (!audioReachedPlayback)
                {
                    status = "Playing " + tracks[currentIndex].Title;
                }
                audioReachedPlayback = true;
                return;
            }
            if (!audioReachedPlayback)
            {
                if (!paused && Time.realtimeSinceStartup >= playbackStartDeadline)
                {
                    paused = true;
                    status = "Playback could not start. Press Play to retry this track.";
                    if (evidence != null) evidence.Record("media.start_failed", "title=" + tracks[currentIndex].Title);
                }
                return;
            }
            if (!paused)
            {
                audioReachedPlayback = false;
                if (repeat) Select(currentIndex); else Next();
            }
        }

        private void Move(int direction)
        {
            if (tracks.Count == 0 || playlist.Count == 0) return;
            int next = shuffle ? RandomPlaylistIndex() : NextPlaylistIndex(currentIndex, direction);
            if (next < 0) return;
            Select(next);
        }

        private int RandomPlaylistIndex()
        {
            if (playlist.Count == 0) return -1;
            int position = UnityEngine.Random.Range(0, playlist.Count);
            return TrackIndexForFile(playlist[position]);
        }

        private int NextPlaylistIndex(int fromTrackIndex, int direction)
        {
            if (playlist.Count == 0) return -1;
            string currentFile = fromTrackIndex >= 0 && fromTrackIndex < tracks.Count ? Path.GetFileName(tracks[fromTrackIndex].Path) : "";
            int position = playlist.IndexOf(currentFile);
            if (position < 0) position = direction >= 0 ? -1 : 0;
            position = (position + direction + playlist.Count) % playlist.Count;
            return TrackIndexForFile(playlist[position]);
        }

        private int TrackIndexForFile(string file)
        {
            for (int i = 0; i < tracks.Count; i++)
                if (string.Equals(Path.GetFileName(tracks[i].Path), file, StringComparison.OrdinalIgnoreCase)) return i;
            return -1;
        }

        private void LoadPlaylistInternal()
        {
            playlistLoaded = true;
            if (File.Exists(PlaylistFile))
            {
                try
                {
                    MediaPlaylistState saved = JsonConvert.DeserializeObject<MediaPlaylistState>(File.ReadAllText(PlaylistFile));
                    if (saved != null)
                    {
                        for (int i = 0; i < saved.Queue.Count; i++)
                            if (TrackIndexForFile(saved.Queue[i]) >= 0 && !playlist.Contains(saved.Queue[i])) playlist.Add(saved.Queue[i]);
                        shuffle = saved.Shuffle;
                        repeat = saved.Repeat;
                        volume = Mathf.Clamp01(saved.Volume);
                        bassDb = Mathf.Clamp(saved.BassDb, -12f, 12f);
                        midDb = Mathf.Clamp(saved.MidDb, -12f, 12f);
                        trebleDb = Mathf.Clamp(saved.TrebleDb, -12f, 12f);
                        autoImport = saved.AutoImport;
                        barrosReplacesStock = saved.UseBarros;
                        if (game != null) game.SetMusicVolume(volume);
                        ApplyTone();
                        return;
                    }
                }
                catch (Exception exception) { status = "Saved playlist could not be read: " + exception.Message; }
            }
            for (int i = 0; i < tracks.Count; i++) playlist.Add(Path.GetFileName(tracks[i].Path));
        }

        private void RemoveMissingPlaylistEntries()
        {
            for (int i = playlist.Count - 1; i >= 0; i--)
                if (TrackIndexForFile(playlist[i]) < 0) playlist.RemoveAt(i);
        }

        private void OnVideoEnded(VideoPlayer player)
        {
            if (repeat) Select(currentIndex); else Next();
        }

        private void OnVideoError(VideoPlayer player, string message)
        {
            loading = false;
            status = "Video playback failed: " + message;
        }

        private static string FriendlyTitle(string value)
        {
            string title = value.TrimStart('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-', '_');
            return title.Replace('-', ' ').Replace('_', ' ').Trim();
        }

        private void ApplyTone()
        {
            if (game != null) game.SetMusicTone(bassDb, midDb, trebleDb);
        }

        private void ReleaseLoadedClip()
        {
            if (musicSource != null && musicSource.clip == loadedClip) musicSource.clip = null;
            if (loadedClip != null) Destroy(loadedClip);
            loadedClip = null;
            cachedWaveform = new float[0];
        }

        private void OnDestroy()
        {
            if (videoPlayer != null)
            {
                videoPlayer.errorReceived -= OnVideoError;
                videoPlayer.loopPointReached -= OnVideoEnded;
            }
            if (videoTexture != null) videoTexture.Release();
            ReleaseLoadedClip();
        }

        [Serializable]
        private sealed class MediaPlaylistState
        {
            [JsonProperty("version")] public int Version = 1;
            [JsonProperty("queue")] public List<string> Queue = new List<string>();
            [JsonProperty("shuffle")] public bool Shuffle;
            [JsonProperty("repeat")] public bool Repeat;
            [JsonProperty("volume")] public float Volume = 0.75f;
            [JsonProperty("bass_db")] public float BassDb;
            [JsonProperty("mid_db")] public float MidDb;
            [JsonProperty("treble_db")] public float TrebleDb;
            [JsonProperty("auto_import")] public bool AutoImport = true;
            [JsonProperty("use_barros")] public bool UseBarros = true;
        }
    }
}
