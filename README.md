# MrJet WebGUI

> An enhanced batch video download manager with a clean web interface, automated FFmpeg repair, and intelligent queue management.

[中文说明](README_zh.md)

---

## ✨ Features

- **Modern Web Interface** — Built with Streamlit for an intuitive, responsive experience.
- **Batch Submission** — Add multiple video IDs or URLs at once (comma, space, or newline delimiters).
- **Smart ID Recognition** — Enter an ID like `SSIS-001` and the full URL is constructed automatically.
- **Duplicate Prevention** — Scans your download folder before adding tasks to avoid re-downloads.
- **Sequential Processing** — Downloads one file at a time to prevent IP bans and system overload.
- **Automated Video Repair** — Every completed video is **losslessly remuxed** with FFmpeg (`-movflags faststart`), fixing seek issues in `mrjet` output.
- **Intelligent Takeover** — When a download stalls near completion (≥95%), FFmpeg automatically merges cached segments so you don't lose progress.
- **Robust Progress Tracking** — Monitors both log output and process state to prevent tasks getting stuck at 99%.
- **Queue Management** — Add, start, clean, and monitor tasks in real-time.
- **Per-Task Logging** — Each download generates a separate log file for easy diagnostics.

## 📦 Project Structure

```
MrJet-WebGUI/
├── app/                          # Core application package
│   ├── config.py                 # Centralized configuration & constants
│   ├── queue_manager.py          # Persistent JSON queue (add/remove/save/load)
│   ├── ffmpeg_utils.py           # Video repair & takeover via FFmpeg
│   ├── downloader.py             # mrjet launch, progress monitor, stall detection
│   └── ui.py                     # Streamlit UI & interaction handlers
├── scripts/                      # Standalone helper utilities
│   ├── merge.py                  # Merge video segments manually
│   └── batch_mp4_ffmpeg_move.py  # Batch faststart + move to destination
├── main.py                       # Entry point (3 lines)
├── Dockerfile                    # Containerized deployment
└── requirements.txt              # Python dependencies
```

## 📋 Prerequisites

- **Python 3.10+**
- **[MrJet](https://github.com/cailurus/mrjet)** — The core download engine (install via `npm install -g @cailurus/mrjet` or follow the [official guide](https://github.com/cailurus/mrjet)).
- **[FFmpeg](https://ffmpeg.org/download.html)** — Must be installed and available in your system PATH.
- Python packages listed in `requirements.txt`.

## 🚀 Installation

```bash
# 1. Install MrJet core engine
npm install -g @cailurus/mrjet

# 2. Install FFmpeg (download from ffmpeg.org, add bin/ to PATH)

# 3. Clone the repository
git clone https://github.com/Evergreentreejxc/MrJet-WebGUI
cd MrJet-WebGUI

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. ⚠️ Configure your download directory
#    Open app/config.py and set DOWNLOAD_DIR to your desired path
```

## 💡 Usage

```bash
streamlit run main.py
```

Open your browser to `http://localhost:8501`.

1. Enter video IDs or URLs in the text area (e.g., `waaa-361, ssis-001`).
2. Click **Add** to queue them.
3. Click **Start next queued task** to begin downloading.
4. Watch real-time progress — the next task starts automatically when one finishes.
5. Use **Utils → Clean finished tasks** to remove completed entries.

## 🐳 Docker

```bash
docker build -t mrjet-webgui .
docker run -p 8501:8501 -v /path/to/downloads:/app/downloads mrjet-webgui
```

## 🛠️ Key Improvements Over v1

| Area | Before | After |
|------|--------|-------|
| Structure | Single 397-line `main.py` | Modular `app/` package (6 files) |
| Code Duplication | Manual vs auto-start logic duplicated | Shared `_start_task()` helper |
| Status Strings | Hardcoded everywhere | Centralized `Status` class in `config.py` |
| Type Safety | No type hints | Full type annotations |
| UI Blocking | `time.sleep()` blocking the UI | Non-blocking `st.rerun()` pattern |
| Docker | No layer caching, no healthcheck | Optimized layers + HEALTHCHECK |
| Requirements | Included non-PyPI `mrjet>=0.1.3` | Only PyPI packages listed |

## 📄 License

MIT — see [LICENSE](LICENSE).

## 🙏 Acknowledgements

- [cailurus](https://github.com/cailurus) for the excellent `mrjet` download engine.