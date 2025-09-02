# Video Downloader with MrJet Engine

This project integrates with the **MrJet** (from [MrJet](https://github.com/cailurus/mrjet)) to download videos from MissAV. It allows you to input video URLs, queue them for download, and track the progress in real-time.

## Features

- **Simple Interface**: Provides an easy-to-use interface via Streamlit for submitting video URLs and tracking download progress.
- **Real-Time Progress**: Displays download progress, including a progress bar for each download.
- **Multiple Tasks**: Allows multiple download tasks to be queued and executed sequentially.
- **Local Video Storage**: Downloads are saved locally to a configurable directory on your system.

## Requirements

- Python 3.10 or higher
- Docker (for containerization, optional)
- `requirements.txt` dependencies

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/Evergreentreejxc/MrJet-WebGUI
   cd MrJet-WebGUI
   ```

2. **Install dependencies**:
   If you're not using Docker, install dependencies manually:

   ```bash
   pip install -r requirements.txt
   ```

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
