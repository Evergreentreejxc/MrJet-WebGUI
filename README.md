
[中文说明](README_zh.md)

---
# MrJet WebGUI - A Batch Video Download Manager

This project provides a graphical web interface for the **MrJet** engine (from [cailurus/mrjet](https://github.com/cailurus/mrjet)), designed to streamline the process of downloading videos from MissAV. With this tool, you can easily batch-submit Video IDs, manage a download queue, and track the progress of each task in real-time.

*(It is recommended to replace this text with a screenshot of your application's interface)*

## ✨ Core Features

-   **User-Friendly Web Interface**: Built with Streamlit for intuitive operation, eliminating the need for complex command-line usage.
-   **Powerful Batch Processing**: Submit multiple Video IDs or full URLs at once. Use commas, spaces, or newlines as delimiters.
-   **Smart ID Recognition**: Simply enter a Video ID (e.g., `SSIS-001`), and the application will automatically construct the full download URL.
-   **✅ Prevents Duplicate Downloads**: Before adding a new task, the tool automatically scans your designated download folder to prevent re-downloading files that already exist, saving you time and disk space.
-   **Real-Time Progress Tracking**: Each task in the queue has its own set of progress bars, clearly displaying the status of the `Verify`, `Download`, and `Build` stages.
-   **Comprehensive Queue Management**:
    -   **Add Tasks**: Add new items to the download queue.
    -   **Start All**: Begin all tasks currently marked as "Not Started" with a single click.
    -   **Clean Finished**: Quickly remove completed or failed tasks and their associated log files from the interface.
-   **Detailed Logging**: Every download task generates a separate log file, making it easy to diagnose issues if they arise.

## 📋 Prerequisites

-   Python 3.10 or higher.
-   **MrJet**: The core engine must be installed and executable from your system's terminal or command prompt.
-   All Python packages listed in `requirements.txt`.

## 🚀 Installation & Setup

1.  **Install the MrJet Core Engine**:
    First, you must follow the [official MrJet guide](https://github.com/cailurus/mrjet) to install the engine. Ensure that the `mrjet` command is accessible in your system's environment path.

2.  **Clone This Repository**:
    ```bash
    git clone https://github.com/Evergreentreejxc/MrJet-WebGUI
    cd MrJet-WebGUI
    ```

3.  **Install Python Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **⚠️【IMPORTANT】Configure Your Download Path**:
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
    -   Click the **"Start All Queued"** button to begin processing all tasks marked as "Not Started".

5.  **Monitor and Manage**:
    -   The interface will auto-refresh to show real-time progress.
    -   Once tasks are finished (either successfully or failed), you can clear them by expanding the **"Utils"** section and clicking **"Clean finished tasks"**.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

-   A special thank you to [cailurus](https://github.com/cailurus) for developing the powerful `mrjet` download tool.