# Video Downloader with Miyuki Engine

This project integrates with the **Miyuki** (from [MissAV-Downloader](https://github.com/MiyukiQAQ/MissAV-Downloader/)) to download videos from various sources. It allows you to input video URLs, queue them for download, and track the progress in real-time.

## Features

- **Simple Interface**: Provides an easy-to-use interface via Streamlit for submitting video URLs and tracking download progress.
- **Real-Time Progress**: Displays download progress, including a progress bar for each download.
- **Multiple Tasks**: Allows multiple download tasks to be queued and executed sequentially.
- **Local Video Storage**: Downloads are saved locally to a configurable directory on your system.

## Requirements

- Python 3.6 or higher
- `ffmpeg` (installed via Docker or locally on your system)
- Docker (for containerization, optional)
- `requirements.txt` dependencies

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/cailurus/Miyuki-WebGUI
   cd Miyuki-WebGUI
   ```

2. **Install dependencies**:
   If you're not using Docker, install dependencies manually:

   ```bash
   pip install -r requirements.txt
   ```

3. **Install ffmpeg**:
   If not using Docker, make sure `ffmpeg` is installed on your system:
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt-get install ffmpeg`
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/).

## Usage

1. **Start the application**:
   Run the Streamlit app:

   ```bash
   streamlit run main.py
   ```

   Visit `http://localhost:8501`

2. **Submit URLs**:

   - Enter the video URL in the provided input field and click the "Submit" button.
   - The video will be added to the download queue, and the progress will be tracked.
   - You can submit additional URLs while the first download is in progress.

3. **Track Download Progress**:
   - The progress of each download will be displayed in a table.
   - The table updates in real-time, showing the status of each task.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

This project is based on the **Miyuki** from the [MissAV-Downloader](https://github.com/MiyukiQAQ/MissAV-Downloader/) project.
