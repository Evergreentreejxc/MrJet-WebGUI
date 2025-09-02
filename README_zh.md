
[English Version](README_en.md)

---
# MrJet WebGUI - 影片批次下載管理器

這是一個基於 **MrJet** ([cailurus/mrjet](https://github.com/cailurus/mrjet)) 引擎的圖形化網頁介面，旨在簡化從 MissAV 下載影片的流程。透過本工具，您可以輕鬆地批次輸入番号、管理下載佇列，並即時追蹤每個任務的進度。

  
## ✨ 核心功能

- **友善的網頁介面**: 透過 Streamlit 構建，操作直觀，無需學習複雜的指令。
- **強大的批次處理**: 支援一次輸入多個番号或 URL，可使用逗號、空格或換行符進行分隔。
- **智慧番号辨識**: 只需輸入番号（例如 `SSIS-001`），程式會自動為您補全完整的下載網址。
- **✅ 重複檔案檢查**: 在新增任務前，程式會自動掃描您指定的下載資料夾，避免下載已經存在的檔案，節省您的時間與硬碟空間。
- **即時進度追蹤**: 為佇列中的每個任務提供獨立的進度條，清晰展示 `校驗 (Verify)`、`下載 (Download)` 和 `建構 (Build)` 三個階段的狀態。
- **完整的佇列管理**:
    - **新增任務**: 將新項目加入等待佇列。
    - **開始所有**: 一鍵啟動所有處於 "未開始" 狀態的任務。
    - **清理已完成**: 快速從介面中移除已成功或失敗的任務及其日誌檔案。
- **詳細日誌記錄**: 每個下載任務都有獨立的日誌檔案，方便在出現問題時進行排查。

## 📋 環境需求

-   Python 3.10 或更高版本
-   **MrJet**: 必須已安裝並能從您的終端機/命令提示字元中正常執行。
-   `requirements.txt` 中所列的 Python 套件。

## 🚀 安裝與設定

1.  **安裝 MrJet 核心引擎**:
    請務必先根據 [MrJet 官方指引](https://github.com/cailurus/mrjet) 完成安裝，並確保 `mrjet` 指令可以在您的系統環境中被呼叫。

2.  **下載本專案**:
    ```bash
    git clone https://github.com/Evergreentreejxc/MrJet-WebGUI
    cd MrJet-WebGUI
    ```

3.  **安裝 Python 依賴套件**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **⚠️【重要】設定您的下載路徑**:
    打開 `main.py` 檔案，找到下面這一行，並將其路徑修改為您希望存放影片的資料夾。
    ```python
    # 【新增】請在此處設定你的影片下載資料夾
    DOWNLOAD_DIR = "D:\IDM Download" 
    ```

## 💡 如何使用

1.  **啟動應用程式**:
    在專案根目錄下執行以下指令：
    ```bash
    streamlit run main.py
    ```

2.  **開啟瀏覽器**:
    在終端機的輸出中找到 `Network URL`，並使用瀏覽器開啟它 (通常是 `http://localhost:8501`)。

3.  **新增下載任務**:
    -   在輸入框中，輸入一個或多個影片番号（如 `waaa-361, ssis-001`）或完整的 URL。
    -   點擊 **"Add"** 按鈕。程式會自動檢查檔案是否重複，然後將不重複的項目加入下方的佇列中。

4.  **開始下載**:
    -   點擊 **"Start All Queued"** 按鈕，所有處於 "Not Started" 狀態的任務將會開始執行。

5.  **監控與管理**:
    -   介面會自動刷新，即時顯示每個任務的進度。
    -   下載完成或失敗的任務可以透過展開 **"Utils"** 區塊並點擊 **"Clean finished tasks"** 來清除。

## 授權條款

本專案採用 MIT 授權 - 詳情請見 [LICENSE](LICENSE) 檔案。

## 致謝

-   感謝 [cailurus](https://github.com/cailurus) 開發了功能強大的 `mrjet` 下載工具。