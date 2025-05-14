
import streamlit as st
from pytubefix import YouTube
from urllib.parse import urlparse, parse_qs
from moviepy import AudioFileClip
import tempfile
import os
import io

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

def download_video_stream(yt, progress_bar):
    video_stream = yt.streams.get_highest_resolution()
    if video_stream is None:
        return None, None, None
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        file_path = temp_file.name
    bytes_streamed = 0
    total_size = video_stream.filesize

    def on_progress(stream, chunk, bytes_remaining):
        nonlocal bytes_streamed
        bytes_streamed = total_size - bytes_remaining
        progress = bytes_streamed / total_size
        progress_bar.progress(min(progress, 1.0))
    yt.register_on_progress_callback(on_progress)
    video_stream.download(filename=file_path)
    # Load file into memory for serving via Streamlit
    with open(file_path, "rb") as fin:
        mp4_bytes = fin.read()
    os.remove(file_path)
    file_name = yt.title + ".mp4"
    return mp4_bytes, file_name, "video/mp4"

def download_audio_stream(yt, progress_bar):
    audio_stream = yt.streams.filter(only_audio=True).first()
    if audio_stream is None:
        return None, None, None
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_audio_file:
        audio_path = temp_audio_file.name
    bytes_streamed = 0
    total_size = audio_stream.filesize

    def on_progress(stream, chunk, bytes_remaining):
        nonlocal bytes_streamed
        bytes_streamed = total_size - bytes_remaining
        progress = bytes_streamed / total_size
        progress_bar.progress(min(progress, 1.0))
    yt.register_on_progress_callback(on_progress)
    audio_stream.download(filename=audio_path)
    mp3_path = audio_path.replace('.mp4', '.mp3')
    # Convert to mp3
    try:
        audio_clip = AudioFileClip(audio_path)
        audio_clip.write_audiofile(mp3_path, logger=None)
        audio_clip.close()
        with open(mp3_path, "rb") as fin:
            mp3_bytes = fin.read()
        os.remove(audio_path)
        os.remove(mp3_path)
        file_name = yt.title + ".mp3"
        return mp3_bytes, file_name, "audio/mpeg"
    except Exception:
        if os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
        return None, None, None

def download_caption_text(yt):
    caption = yt.captions.get_by_language_code('en')
    if caption is None:
        return None, None, None
    text = caption.generate_srt_captions()
    text_buffer = io.StringIO(text)
    file_bytes = text_buffer.getvalue().encode("utf-8")
    file_name = yt.title + ".txt"
    return file_bytes, file_name, "text/plain"

st.title("YouTube Downloader")
st.write(
    "Download any YouTube video as an **MP4 (video)**, **MP3 (audio)**, or **Text (captions if available)**. "
    "Paste the full YouTube URL, choose your format, and click Download. No login required."
)

url = st.text_input("Enter a YouTube video URL")
format_option = st.radio("Pick a format", ('mp4', 'mp3', 'text'), horizontal=True)
start_download = st.button("Download")

if url and start_download:
    try:
        clean_video_url = clean_url(url)
        yt = YouTube(clean_video_url)
        st.write(f"**Title:** {yt.title}")
        st.write(f"**Length:** {yt.length // 60} min {yt.length % 60} sec")

        progress_bar = st.progress(0)
        if format_option == "mp4":
            file_bytes, file_name, mime = download_video_stream(yt, progress_bar)
        elif format_option == "mp3":
            file_bytes, file_name, mime = download_audio_stream(yt, progress_bar)
        elif format_option == "text":
            file_bytes, file_name, mime = download_caption_text(yt)
            progress_bar.progress(1.0)
        else:
            file_bytes = None
            file_name = None
            mime = None

        if file_bytes is not None and file_name is not None:
            st.success(f"Download ready: {file_name}")
            st.download_button(
                label=f"Download {file_name}",
                data=file_bytes,
                file_name=file_name,
                mime=mime
            )
        else:
            if format_option == "text":
                st.warning("No English captions available for this video.")
            else:
                st.error("Could not generate download. Try another video.")

        progress_bar.empty()
    except Exception as e:
        st.error(f"An error occurred: {e}")

