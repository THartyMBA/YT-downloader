#This Python script allows you to download a Youtube video as either a MP4, MP3, or if they have text transcripts available as Text.  

import os
from pytubefix import YouTube
from pytubefix.cli import on_progress
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from urllib.parse import urlparse, parse_qs
from moviepy import AudioFileClip # For MP3 conversion
import pytube # For caption extraction


def clean_url(url):
    if 'youtube' in url or 'youtu.be' in url:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        if parsed_url.netloc == 'youtu.be':
            video_id = parsed_url.path.lstrip('/')
            return f"https://www.youtube.com/watch?v={video_id}"
        if 'v' in query_params:
            return f"https://www.youtube.com/watch?v={query_params['v'][0]}"
    return url

def on_progress_callback(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage_of_completion = bytes_downloaded / total_size * 100
    progress_var.set(percentage_of_completion)
    progress_bar.update()

def download_video(video_url, save_path, file_format):
    try:
        yt = YouTube(video_url, on_progress_callback=on_progress_callback)
        print(f"Title: {yt.title}")
        print(f"Length: {yt.length} seconds")

        if file_format == 'mp4':
            video_stream = yt.streams.get_highest_resolution()
            if video_stream is None:
                print("The highest resolution stream is not available.")
                return
            video_stream.download(output_path=save_path)
            print(f"Download completed and saved to {save_path}")

        elif file_format == 'mp3':
            audio_stream = yt.streams.filter(only_audio=True).first()
            if audio_stream is None:
                print("Audio stream is not available.")
                return
            audio_path = audio_stream.download(output_path=save_path)
            mp3_path = os.path.splitext(audio_path)[0] + '.mp3'
            AudioFileClip(audio_path).write_audiofile(mp3_path)
            os.remove(audio_path) # Remove the original downloaded file
            print(f"MP3 conversion completed and saved to {mp3_path}")

        elif file_format == 'text':
            caption = yt.captions.get_by_language_code('en')
            if caption is None:
                print("No English captions available.")
                return
            text_path = os.path.join(save_path, f"{yt.title}.txt")
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(caption.generate_srt_captions())
            print(f"Text extraction completed and saved to {text_path}")

        # Show a dialog to open the file location
        if messagebox.askyesno("Open Folder", "Download complete. Do you want to open the folder?"):
            os.startfile(save_path)
        
    except Exception as e:
        print(f"An error occurred: {e}")

def get_save_path():
    save_path = filedialog.askdirectory(title="Select Download Folder")
    return save_path

def start_download():
    video_url = url_entry.get()
    clean_video_url = clean_url(video_url)
    print(f"Cleaned URL: {clean_video_url}")
    save_path = get_save_path()
    if save_path:
        download_video(clean_video_url, save_path, format_var.get())

if __name__ == "__main__":
    root = tk.Tk()
    root.title("YouTube Video Downloader")

    # Padding around all elements
    padding_options = {'padx': 10, 'pady': 10}

    # URL input
    tk.Label(root, text="Enter the YouTube video URL:").pack(**padding_options)
    url_entry = tk.Entry(root, width=50)
    url_entry.pack(**padding_options)

    # Format selection
    format_var = tk.StringVar(value='mp4') # Default to MP4
    tk.Label(root, text="Select the format:").pack(**padding_options)
    formats_frame = tk.Frame(root)
    formats_frame.pack(**padding_options)
    tk.Radiobutton(formats_frame, text="MP4", variable=format_var, value='mp4').pack(side=tk.LEFT, **padding_options)
    tk.Radiobutton(formats_frame, text="MP3", variable=format_var, value='mp3').pack(side=tk.LEFT, **padding_options)
    tk.Radiobutton(formats_frame, text="Text", variable=format_var, value='text').pack(side=tk.LEFT, **padding_options)

    # Progress bar
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
    progress_bar.pack(pady=10, fill=tk.X, padx=10)

    # Download button
    download_button = tk.Button(root, text="Download", command=start_download)
    download_button.pack(**padding_options)

    root.mainloop()
