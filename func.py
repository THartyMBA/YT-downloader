#This Python script allows you to download a Youtube video as either a MP4, MP3, or if they have text transcripts available as Text.  

# Import necessary libraries
import os
from pytubefix import YouTube # For downloading YouTube videos
# from pytubefix.cli import on_progress # This import seems unused in the current script, but was likely for a CLI progress bar
import tkinter as tk # For creating the graphical user interface (GUI)
from tkinter import filedialog, messagebox # Specific tkinter modules for file dialogs and message boxes
from tkinter import ttk # Themed tkinter widgets, used here for the progress bar
from urllib.parse import urlparse, parse_qs # For parsing and cleaning YouTube URLs
from moviepy import AudioFileClip # For MP3 conversion
# import pytube


def clean_url(url):
    """
    Cleans the input YouTube URL to a standard 'watch?v=' format.
    Handles both standard YouTube URLs and shortened 'youtu.be' URLs.

    Args:
        url (str): The input YouTube URL.

    Returns:
        str: The cleaned YouTube URL or the original URL if not a YouTube link.
    """
    if 'youtube' in url or 'youtu.be' in url:
        parsed_url = urlparse(url) # Parse the URL into components
        query_params = parse_qs(parsed_url.query) # Extract query parameters (like 'v=VIDEO_ID')
        if parsed_url.netloc == 'youtu.be': # Check if it's a shortened URL
            video_id = parsed_url.path.lstrip('/') # Extract video ID from the path
            return f"https://www.youtube.com/watch?v={video_id}" # Construct standard URL
        if 'v' in query_params: # Check if 'v' (video ID) is in query parameters
            return f"https://www.youtube.com/watch?v={query_params['v'][0]}" # Construct standard URL
    return url # Return original URL if not recognized as a YouTube link

def on_progress_callback(stream, chunk, bytes_remaining):
    """
    Callback function to update the GUI's progress bar during download.

    Args:
        stream: The stream being downloaded.
        chunk: The chunk of data just downloaded.
        bytes_remaining: The number of bytes remaining to be downloaded.
    """
    # Calculate the total size of the stream
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage_of_completion = bytes_downloaded / total_size * 100
    progress_var.set(percentage_of_completion)
    progress_bar.update()

def download_video(video_url, save_path, file_format):
    """
    Downloads the YouTube video in the specified format (MP4, MP3, or Text).

    Args:
        video_url (str): The URL of the YouTube video.
        save_path (str): The directory where the file should be saved.
        file_format (str): The desired format ('mp4', 'mp3', 'text').
    """
    try:
        # Initialize YouTube object with the URL and progress callback
        yt = YouTube(video_url, on_progress_callback=on_progress_callback)
        print(f"Title: {yt.title}")
        print(f"Length: {yt.length} seconds")

        # Handle MP4 download
        if file_format == 'mp4':
            # Get the stream with the highest resolution
            video_stream = yt.streams.get_highest_resolution()
            if video_stream is None:
                print("The highest resolution stream is not available.")
                messagebox.showerror("Error", "The highest resolution stream is not available for this video.")
                return
            # Download the video stream to the specified path
            video_stream.download(output_path=save_path)
            print(f"Download completed and saved to {save_path}")

        # Handle MP3 download
        elif file_format == 'mp3':
            # Get the first available audio-only stream
            audio_stream = yt.streams.filter(only_audio=True).first()
            if audio_stream is None:
                print("Audio stream is not available.")
                messagebox.showerror("Error", "Audio stream is not available for this video.")
                return
            # Download the audio stream (usually in .mp4 or .webm format)
            audio_path = audio_stream.download(output_path=save_path)
            # Define the path for the output MP3 file
            mp3_path = os.path.splitext(audio_path)[0] + '.mp3'
            # Convert the downloaded audio file to MP3 using moviepy
            AudioFileClip(audio_path).write_audiofile(mp3_path)
            os.remove(audio_path) # Remove the original downloaded file
            print(f"MP3 conversion completed and saved to {mp3_path}")

        # Handle Text (captions) download
        elif file_format == 'text':
            # Try to get English captions
            caption = yt.captions.get_by_language_code('en')
            if caption is None:
                print("No English captions available.")
                messagebox.showwarning("Captions", "No English captions available for this video.")
                return
            # Define the path for the output text file
            text_path = os.path.join(save_path, f"{yt.title}.txt")
            # Write the captions (in SRT format) to the text file
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(caption.generate_srt_captions())
            print(f"Text extraction completed and saved to {text_path}")

        # After successful download, ask the user if they want to open the folder
        if messagebox.askyesno("Open Folder", "Download complete. Do you want to open the folder?"):
            os.startfile(save_path) # Opens the folder in the default file explorer
        
    except Exception as e:
        print(f"An error occurred: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")

def get_save_path():
    """
    Opens a dialog for the user to select a directory to save the downloaded file.

    Returns:
        str: The selected directory path, or None if canceled.
    """
    save_path = filedialog.askdirectory(title="Select Download Folder")
    return save_path

def start_download():
    """
    Initiates the download process by getting the URL, save path, and selected format.
    """
    video_url = url_entry.get()
    clean_video_url = clean_url(video_url) # Clean the URL first
    print(f"Cleaned URL: {clean_video_url}")
    save_path = get_save_path()
    if save_path:
        download_video(clean_video_url, save_path, format_var.get())

if __name__ == "__main__":
    root = tk.Tk()
    root.title("YouTube Video Downloader") # Set the title of the main window

    # Define padding options for GUI elements for consistent spacing
    padding_options = {'padx': 10, 'pady': 10}

    # --- GUI Elements ---

    # Label and Entry for YouTube URL input
    tk.Label(root, text="Enter the YouTube video URL:").pack(**padding_options)
    url_entry = tk.Entry(root, width=50)
    url_entry.pack(**padding_options)

    # Label and Radio buttons for format selection (MP4, MP3, Text)
    format_var = tk.StringVar(value='mp4') # Tkinter variable to hold the selected format, default to 'mp4'
    tk.Label(root, text="Select the format:").pack(**padding_options)
    formats_frame = tk.Frame(root) # Frame to group radio buttons
    formats_frame.pack(**padding_options)
    tk.Radiobutton(formats_frame, text="MP4", variable=format_var, value='mp4').pack(side=tk.LEFT, **padding_options)
    tk.Radiobutton(formats_frame, text="MP3", variable=format_var, value='mp3').pack(side=tk.LEFT, **padding_options)
    tk.Radiobutton(formats_frame, text="Text", variable=format_var, value='text').pack(side=tk.LEFT, **padding_options)

    # Progress bar to show download progress
    progress_var = tk.DoubleVar() # Tkinter variable to bind to the progress bar's value
    progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
    progress_bar.pack(pady=10, fill=tk.X, padx=10)

    # Button to trigger the download
    download_button = tk.Button(root, text="Download", command=start_download)
    download_button.pack(**padding_options)

    root.mainloop() # Start the Tkinter event loop to run the GUI
