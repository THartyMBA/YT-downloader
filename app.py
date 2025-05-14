# This Python script creates a web application using Streamlit
# that allows users to download YouTube videos as MP4 (video),
# MP3 (audio), or Text (captions, if available).

# Import necessary libraries
import streamlit as st
from pytubefix import YouTube # For interacting with YouTube and downloading videos/audio
from urllib.parse import urlparse, parse_qs # For cleaning and parsing YouTube URLs
from moviepy import AudioFileClip # For converting audio files to MP3 format
import tempfile # For creating temporary files to store downloads before serving
import os # For operating system dependent functionalities like file removal
import io # For handling in-memory text streams (used for captions)

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

def download_video_stream(yt, progress_bar):
    """
    Downloads the highest resolution video stream as an MP4.

    Args:
        yt (YouTube): An instance of the pytubefix YouTube object.
        progress_bar (streamlit.delta_generator.DeltaGenerator): Streamlit progress bar object to update.

    Returns:
        tuple: (bytes, str, str) containing the video file bytes,
               the suggested file name, and the MIME type.
               Returns (None, None, None) if the stream is not available.
    """
    # Get the stream with the highest resolution
    video_stream = yt.streams.get_highest_resolution()
    if video_stream is None:
        return None, None, None # Return None if no suitable stream is found
    st.info(f"Selected video stream: {video_stream.itag} ({video_stream.resolution}, {video_stream.fps}fps)")

    # Create a temporary file to download the video to
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        file_path = temp_file.name
    bytes_streamed = 0
    total_size = video_stream.filesize

    st.info(f"Pytubefix reports video filesize: {total_size} bytes.") # Log expected size

    def on_progress(stream, chunk, bytes_remaining):
        nonlocal bytes_streamed
        # Calculate total bytes downloaded so far more directly
        current_bytes_downloaded = total_size - bytes_remaining
        progress = current_bytes_downloaded / total_size if total_size > 0 else 0
        # Update bytes_streamed for consistency if it were used elsewhere, but current_bytes_downloaded is more direct
        bytes_streamed = current_bytes_downloaded
        progress_bar.progress(min(progress, 1.0)) # Update Streamlit progress bar (cap at 1.0)

    yt.register_on_progress_callback(on_progress) # Register the progress callback
    mp4_bytes = None
    try:
        st.info(f"Attempting to download to temporary file: {file_path}")
        # --- MODIFICATION START ---
        # Instead of downloading directly to file, stream to an in-memory buffer first
        st.info("Streaming video to in-memory buffer...")
        buffer = io.BytesIO()
        video_stream.stream_to_buffer(buffer)
        buffer.seek(0) # Reset buffer position to the beginning for reading

        st.info(f"Buffer size after streaming: {len(buffer.getvalue())} bytes. Writing buffer to temporary file: {file_path}")
        with open(file_path, "wb") as f_out:
            f_out.write(buffer.getvalue())
        # --- MODIFICATION END ---
        if not os.path.exists(file_path):
            st.error(f"Temporary file {file_path} was not created after download attempt.")
            return None, None, None

        temp_file_actual_size = os.path.getsize(file_path)
        st.info(f"Temporary file actual size on disk: {temp_file_actual_size} bytes.")

        # Load the downloaded file into memory to be served by Streamlit's download button
        with open(file_path, "rb") as fin:
            mp4_bytes = fin.read()
        st.info(f"Bytes read into memory: {len(mp4_bytes)} bytes.")

        if total_size > 0 and temp_file_actual_size != total_size:
            st.warning(
                f"Filesize mismatch: Pytubefix reported {total_size}, "
                f"but temporary file on disk is {temp_file_actual_size} bytes."
            )
        if len(mp4_bytes) != temp_file_actual_size:
            st.error(
                f"CRITICAL READ ERROR: Temporary file on disk was {temp_file_actual_size} bytes, "
                f"but only {len(mp4_bytes)} bytes were read into memory. Data loss occurred."
            )
            return None, None, None # Data is corrupted/incomplete

    except Exception as e:
        st.error(f"An error occurred during video download or file handling: {e}")
        return None, None, None
    finally:
        if os.path.exists(file_path):
            os.remove(file_path) # Delete the temporary file
        yt.register_on_progress_callback(None) # Clear the progress callback

    if mp4_bytes:
        file_name = yt.title + ".mp4" # Construct the filename
        return mp4_bytes, file_name, "video/mp4" # Return file bytes, name, and MIME type
    return None, None, None

def download_audio_stream(yt, progress_bar):
    """
    Downloads the audio stream and converts it to MP3.

    Args:
        yt (YouTube): An instance of the pytubefix YouTube object.
        progress_bar (streamlit.delta_generator.DeltaGenerator): Streamlit progress bar object to update.

    Returns:
        tuple: (bytes, str, str) containing the MP3 file bytes,
               the suggested file name, and the MIME type.
               Returns (None, None, None) if the stream is not available or conversion fails.
    """
    # Get the first available audio-only stream
    audio_stream = yt.streams.filter(only_audio=True).first()
    if audio_stream is None:
        return None, None, None # Return None if no audio stream is found

    # Create a temporary file to download the audio (often in .mp4 or .webm format)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_audio_file: # Suffix might be .webm, but .mp4 is common
        audio_path = temp_audio_file.name

    bytes_streamed = 0
    total_size = audio_stream.filesize

    def on_progress(stream, chunk, bytes_remaining):
        """
        Callback function to update the Streamlit progress bar during download.

        Args:
            stream: The stream being downloaded.
            chunk: The chunk of data just downloaded.
            bytes_remaining: The number of bytes remaining to be downloaded.
        """
        nonlocal bytes_streamed
        bytes_streamed = total_size - bytes_remaining
        # Ensure total_size is not zero to prevent DivisionByZeroError
        progress = (bytes_streamed / total_size) if total_size > 0 else 0
        progress_bar.progress(min(progress, 1.0))

    yt.register_on_progress_callback(on_progress) # Register the progress callback
    audio_stream.download(filename=audio_path) # Download the audio to the temporary file

    mp3_path = audio_path.rsplit('.', 1)[0] + '.mp3' # Define the path for the output MP3 file

    # Convert the downloaded audio file to MP3 using moviepy
    try:
        audio_clip = AudioFileClip(audio_path)
        audio_clip.write_audiofile(mp3_path, logger=None) # Suppress moviepy logs
        audio_clip.close() # Close the clip to release resources

        # Load the converted MP3 file into memory
        with open(mp3_path, "rb") as fin:
            mp3_bytes = fin.read()

        os.remove(audio_path) # Delete the original temporary audio file
        os.remove(mp3_path) # Delete the temporary MP3 file

        file_name = yt.title + ".mp3" # Construct the filename
        return mp3_bytes, file_name, "audio/mpeg" # Return file bytes, name, and MIME type
    except Exception as e: # Catch any errors during conversion or file handling
        st.error(f"Error during MP3 conversion: {e}") # Show error in Streamlit UI
        # Ensure temporary files are cleaned up even if an error occurs
        if os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists(mp3_path):
            os.remove(mp3_path) # Ensure mp3_path is also cleaned up on error
        yt.register_on_progress_callback(None) # Clear callback on error too
        return None, None, None

def download_caption_text(yt):
    """
    Downloads English captions for the video as a text file (SRT format).

    Args:
        yt (YouTube): An instance of the pytubefix YouTube object.

    Returns:
        tuple: (bytes, str, str) containing the text file bytes,
               the suggested file name, and the MIME type.
               Returns (None, None, None) if no English captions are available.
    """
    # Try to get English captions
    caption = yt.captions.get_by_language_code('en')
    if caption is None:
        return None, None, None # Return None if no English captions are found

    text = caption.generate_srt_captions() # Generate captions in SRT format
    text_buffer = io.StringIO(text) # Create an in-memory text buffer
    file_bytes = text_buffer.getvalue().encode("utf-8") # Encode the text to bytes (UTF-8)

    file_name = yt.title + ".txt" # Construct the filename
    return file_bytes, file_name, "text/plain" # Return file bytes, name, and MIME type

# --- Streamlit User Interface (UI) Setup ---
st.title("YouTube Downloader")
st.write(
    "Download any YouTube video as an **MP4 (video)**, **MP3 (audio)**, or **Text (captions if available)**. "
    "Paste the full YouTube URL, choose your format, and click Download. No login required."
)

# Input field for the YouTube URL
url = st.text_input("Enter a YouTube video URL")

# Radio buttons for selecting the download format
format_option = st.radio("Pick a format", ('mp4', 'mp3', 'text'), horizontal=True)

# Button to initiate the download process
start_download = st.button("Download")

# --- Download Logic ---
# This block executes when a URL is provided and the "Download" button is clicked.
if url and start_download:
    try:
        clean_video_url = clean_url(url) # Clean the input URL
        yt = YouTube(clean_video_url) # Create a YouTube object

        # Display video title and length
        st.write(f"**Title:** {yt.title}")
        st.write(f"**Length:** {yt.length // 60} min {yt.length % 60} sec")

        progress_bar = st.progress(0) # Initialize Streamlit progress bar

        # Call the appropriate download function based on the selected format
        if format_option == "mp4":
            file_bytes, file_name, mime = download_video_stream(yt, progress_bar)
        elif format_option == "mp3":
            file_bytes, file_name, mime = download_audio_stream(yt, progress_bar)
        elif format_option == "text":
            file_bytes, file_name, mime = download_caption_text(yt)
            progress_bar.progress(1.0) # For text, download is instant, so set progress to 100%
        else:
            # Should not happen with radio buttons, but good for robustness
            file_bytes = None
            file_name = None
            mime = None

        # If file bytes were successfully obtained, provide a download button
        if file_bytes is not None and file_name is not None:
            st.success(f"Download ready: {file_name}")
            st.download_button(
                label=f"Download {file_name}",
                data=file_bytes, # The bytes of the file to download
                file_name=file_name, # The default name for the downloaded file
                mime=mime # The MIME type of the file
            )
        else:
            # Handle cases where download failed or content was not available
            if format_option == "text":
                st.warning("No English captions available for this video.")
            else:
                st.error("Could not generate download. Try another video.")

        progress_bar.empty() # Clear the progress bar after completion or error
    except Exception as e: # Catch any other exceptions during the process
        st.error(f"An error occurred: {e}") # Display a generic error message

# --- Disclaimer ---
# Display a disclaimer at the bottom of the app
st.markdown("---") # Adds a horizontal rule for separation
st.markdown(
    "**Disclaimer:** Please ensure you comply with YouTube's Terms of Service and respect copyright laws when using this tool. "
    "This downloader is intended for personal, fair use only. Downloading copyrighted material without permission is illegal in many countries. "
    "Use this tool responsibly and at your own risk."
)
