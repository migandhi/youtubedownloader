# File: download_logic.py

from yt_dlp import YoutubeDL
import os
import time

# --- IMPORTANT CHANGE HERE ---
# Provide the full path to the folder containing ffmpeg.exe and ffprobe.exe
# Use a raw string (r'...') to handle backslashes correctly in Windows paths.
FFMPEG_PATH = r'L:\ffmpeg-2021-03-09-git-c35e456f54-full_build\bin'

def download_video_with_opts(url, output_path, audio_only=False, subtitles=False, progress_callback=None):
    """
    Download a single YouTube video.
    Includes a progress_callback function for real-time updates.
    """
    if audio_only:
        format_selector = 'bestaudio/best'
        file_extension = 'mp3'
        postprocessors = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        format_selector = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best'
        file_extension = 'mp4'
        postprocessors = [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }]

    ydl_opts = {
        'format': format_selector,
        'outtmpl': os.path.join(output_path, f'%(title)s.%(ext)s'),
        'postprocessors': postprocessors,
        'ignoreerrors': True,
        'no_warnings': True,
        'writesubtitles': subtitles,
        'writeautomaticsub': subtitles,
        'subtitleslangs': ['en'],
        'keepvideo': False,
        'noplaylist': True,
        'progress_hooks': [progress_callback],
        # Add the ffmpeg_location option
        'ffmpeg_location': FFMPEG_PATH,
    }
    
    if not audio_only:
        ydl_opts['merge_output_format'] = 'mp4'

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            return {'success': True, 'message': f'Download complete!'}
    except Exception as e:
        return {'success': False, 'message': f'Error downloading {url}: {str(e)}'}

def download_playlist_with_opts(url, output_path, audio_only=False, subtitles=False, progress_callback=None):
    """
    Download a YouTube playlist.
    """
    playlist_output_path = os.path.join(output_path, 'playlists', '%(playlist_title)s')
    os.makedirs(os.path.join(output_path, 'playlists'), exist_ok=True)

    if audio_only:
        file_extension = 'mp3'
    else:
        file_extension = 'mp4'

    ydl_opts = {
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best' if not audio_only else 'bestaudio/best',
        'outtmpl': os.path.join(playlist_output_path, f'%(playlist_index)s - %(title)s.%(ext)s'),
        'writesubtitles': subtitles,
        'writeautomaticsub': subtitles,
        'subtitleslangs': ['en'],
        'ignoreerrors': True,
        'noplaylist': False,
        'progress_hooks': [progress_callback],
        # Add the ffmpeg_location option here as well
        'ffmpeg_location': FFMPEG_PATH,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            return {'success': True, 'message': f'Download complete!'}
    except Exception as e:
        return {'success': False, 'message': f'Error downloading playlist {url}: {str(e)}'}

def get_content_type(url):
    """Quickly determine if a URL is a video or playlist."""
    if 'playlist?list=' in url:
        return 'playlist'
    if '/@' in url or '/channel/' in url or '/c/' in url or '/user/' in url:
        return 'channel_or_playlist'
    return 'video'