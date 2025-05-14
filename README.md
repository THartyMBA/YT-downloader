# YouTube Downloader (Tkinter GUI & Streamlit Web App)

This project provides two interfaces for downloading YouTube videos:
1.  A desktop GUI application built with Tkinter (`func.py`).
2.  A web application built with Streamlit (`app.py`).

Both applications allow users to download YouTube videos as MP4 (video), MP3 (audio), or Text (captions/transcripts, if available).

## Features

*   **Multiple Download Formats:**
    *   **MP4:** Download videos in their highest available resolution.
    *   **MP3:** Extract and convert audio from videos into MP3 format.
    *   **Text:** Download available English captions/transcripts as a `.txt` file (SRT format).
*   **URL Cleaning:** Automatically cleans up YouTube URLs, supporting both standard `youtube.com/watch?v=` and shortened `youtu.be/` links.
*   **User-Friendly Interfaces:**
    *   **Tkinter GUI (`func.py`):** A simple desktop application with URL input, format selection, a download button, and a progress bar. It also prompts to open the download folder upon completion.
    *   **Streamlit Web App (`app.py`):** A web-based interface accessible via a browser, featuring URL input, format selection, a download button, progress display, and direct download links for the generated files.
*   **Progress Indication:** Both applications show download progress.

## How It Works

Both applications utilize the `pytubefix` library to interact with YouTube, fetch video information, and download streams.

*   **`func.py` (Tkinter GUI):**
    *   Uses `tkinter` for the graphical user interface.
    *   Downloads files directly to a user-selected folder.
    *   Uses `moviepy` for converting downloaded audio streams to MP3.

*   **`app.py` (Streamlit Web App):**
    *   Uses `streamlit` to create an interactive web interface.
    *   Downloads files to temporary storage on the server, then provides them to the user via a download button in the browser.
    *   Uses `moviepy` for MP3 conversion.

## Prerequisites

*   Python 3.x
*   pip (Python package installer)

## Installation & Setup

1.  **Clone the repository or download the files.**
    ```bash
    # If you have git installed
    # git clone <repository_url>
    # cd <repository_directory>
    ```
    Or simply ensure `func.py` and `app.py` are in the same directory.

2.  **Install the required Python libraries:**
    Open your terminal or command prompt and run:
    ```bash
    pip install pytubefix moviepy streamlit tkinter
    ```
    *(Note: `tkinter` is usually included with standard Python installations on Windows and macOS. If you're on Linux, you might need to install it separately, e.g., `sudo apt-get install python3-tk` for Debian/Ubuntu based systems.)*

## How to Run

### 1. Tkinter GUI Application (`func.py`)

Navigate to the directory containing `func.py` in your terminal or command prompt and run:

```bash
python "c:\directory file location"
```

*   Enter the YouTube video URL.
*   Select the desired format (MP4, MP3, or Text).
*   Click "Download".
*   You will be prompted to select a save location for the downloaded file.

### 2. Streamlit Web Application (`app.py`)

Navigate to the directory containing `app.py` in your terminal or command prompt and run:

```bash
streamlit run "c:\directory file location"
```

*   This will typically open the web application in your default web browser (e.g., at `http://localhost:8501`).
*   Paste the YouTube video URL into the input field.
*   Choose your desired format (mp4, mp3, or text).
*   Click the "Download" button.
*   Once processing is complete, a download link for the file will appear.

## File Structure

*   `func.py`: The Tkinter GUI application script.
*   `app.py`: The Streamlit web application script.
*   `README.md`: This file.
  
## Disclaimer

**Please ensure you comply with YouTube's Terms of Service and respect copyright laws when using this tool. This downloader is intended for personal, fair use only. Downloading copyrighted material without permission is illegal in many countries. Use this tool responsibly and at your own risk.**

---
