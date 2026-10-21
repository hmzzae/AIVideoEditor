# 🎬 AI-Powered Short Video Generator & Dynamic Cropper

An autonomous, multi-threaded desktop application that converts long-form widescreen videos (podcasts, interviews, lectures) into engaging, mobile-ready vertical shorts (TikTok, Reels, Shorts) using local AI models and computer vision pipelines.

---

## 🚀 Key Features

* **Local Audio Transcription:** Utilizes CTranslate2-optimized `faster-whisper` for fast, offline speech-to-text generation with exact timestamps.
* **Semantic Hook Selection:** Integrates Google’s **Gemini** LLM to contextually analyze transcripts and extract the most engaging, logically complete 60-second narrative clip.
* **Dynamic Facial Tracking:** Re-engineered **MediaPipe Face Mesh** to track lip movement variance, identify active speakers, and execute smooth camera panning to keep subjects centered in a 9:16 mobile crop.
* **Automated Subtitle & Audio Compositing:** Orchestrates **FFmpeg** to cut clips, synchronize original audio, and burn dynamic, word-level TikTok-style subtitles directly onto the final render.
* **Asynchronous Desktop UI:** Built with CustomTkinter and Python `threading` to keep the user interface responsive during heavy computational workloads.

