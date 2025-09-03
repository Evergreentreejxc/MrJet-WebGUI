[中文说明](README_zh.md)

---
# MrJet WebGUI - An Enhanced Batch Video Download Manager

This project provides a graphical web interface for the **MrJet** engine (from [cailurus/mrjet](https://github.com/cailurus/mrjet)), designed to streamline the process of downloading videos from MissAV. With this tool, you can easily batch-submit Video IDs, manage a download queue, and enjoy a fully automated download and repair workflow.

## ✨ Core Features

-   **User-Friendly Web Interface**: Built with Streamlit for intuitive operation, eliminating the need for complex command-line usage.
-   **Powerful Batch Processing**: Submit multiple Video IDs or full URLs at once. Use commas, spaces, or newlines as delimiters.
-   **Smart ID Recognition**: Simply enter a Video ID (e.g., `SSIS-001`), and the application will automatically construct the full download URL.
-   **✅ Prevents Duplicate Downloads**: Before adding a new task, the tool automatically scans your designated download folder to prevent re-downloading files that already exist, saving you time and disk space.
-   **Stable Sequential Downloading**: Processes one download at a time to prevent IP bans and system overload, significantly increasing success rates.
-   **🤖 Automated Video Repair (FFmpeg Integration)**: Every completed video is **automatically** post-processed with FFmpeg (lossless remux). This permanently solves the common issue where videos built by `mrjet` **cannot be seeked** (i.e., dragging the progress bar doesn't work), ensuring every file is perfectly playable.
-   **Robust Progress Tracking**: Fixes the issue where tasks could get stuck at 99%. The application now monitors both the log file and the `mrjet` process itself for accurate completion detection.
-   **Comprehensive Queue Management**:
    -   **Add Tasks**: Add new items to the download queue.
    -   **Start All**: Begin all tasks currently marked as "Not Started" with a single click.
    -   **Clean Finished**: Quickly remove completed or failed tasks and their associated log files from the interface.
-   **Detailed Logging**: Every download task generates a separate log file, making it easy to diagnose issues if they arise.

## 📋 Prerequisites

-   Python 3.10 or higher.
-   **MrJet**: The core engine must be installed and executable from your system's terminal or command prompt.
-   **FFmpeg**: Must be installed and accessible from your system's PATH. It is used for the automated video repair feature.
-   All Python packages listed in `requirements.txt`.

## 🚀 Installation & Setup

1.  **Install the MrJet Core Engine**:
    First, you must follow the [official MrJet guide](https://github.com/cailurus/mrjet) to install the engine. Ensure that the `mrjet` command is accessible in your system's environment path.

2.  **Install FFmpeg**:
    -   Go to the [FFmpeg official download page](https://ffmpeg.org/download.html).
    -   Download the appropriate version for your OS and extract it.
    -   **[IMPORTANT]** Add the path to FFmpeg's `bin` folder to your system's **environment variables (PATH)**. This ensures the `ffmpeg` command can be run from any directory.

3.  **Clone This Repository**:
    ```bash
    git clone https://github.com/Evergreentreejxc/MrJet-WebGUI
    cd MrJet-WebGUI
    ```

4.  **Install Python Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

5.  **⚠️【IMPORTANT】Configure Your Download Path**:
    Open the `main.py` file. Locate the following line and change the path to your desired video storage directory.
    ```python
    # Set your video download folder here
    DOWNLOAD_DIR = "D:\IDM Download" 
    ```

## 💡 Usage

1.  **Launch the Application**:
    Run the following command in the project's root directory:
    ```bash
    streamlit run main.py
    ```

2.  **Open Your Browser**:
    Navigate to the `Network URL` provided in the terminal output (usually `http://localhost:8501`).

3.  **Add Download Tasks**:
    -   In the text area, enter one or more Video IDs (e.g., `waaa-361, ssis-001`) or full URLs.
    -   Click the **"Add"** button. The application will check for duplicates and add valid items to the queue below.

4.  **Start Downloading**:
    -   Click the **"Start All Queued"** button. Tasks in the queue will now be executed **one by one** automatically.

5.  **Monitor and Manage**:
    -   The interface will auto-refresh to show real-time progress, including new statuses like `Downloading`, `Fixing`, and `Completed`.
    -   Once tasks are finished, you can clear them by expanding the **"Utils"** section and clicking **"Clean finished tasks"**.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

-   A special thank you to [cailurus](https://github.com/cailurus) for developing the powerful `mrjet` download tool.