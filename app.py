# File: app.py

from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import os
import threading
import json
import time
from download_logic import download_video_with_opts, download_playlist_with_opts, get_content_type

app = Flask(__name__)

DOWNLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Use a dictionary to store progress updates by a unique ID (session_id)
download_progress = {}

@app.route('/')
def index():
    return render_template('index.html')

def yt_dlp_progress_hook(d):
    """
    A custom hook for yt-dlp to report progress.
    Updates the download_progress dictionary.
    """
    session_id = d.get('session_id')
    if not session_id:
        return

    # Extract relevant progress info
    status = d.get('status')
    
    if status == 'downloading':
        percent = d.get('_percent_str', '').strip()
        speed = d.get('_speed_str', 'N/A').strip()
        eta = d.get('_eta_str', 'N/A').strip()
        filename = d.get('filename')
        
        message = f"Downloading: {filename} | {percent} | Speed: {speed} | ETA: {eta}"
        download_progress[session_id] = {'status': status, 'message': message, 'percent': percent}
        
    elif status == 'finished':
        message = f"Download finished. Post-processing..."
        download_progress[session_id] = {'status': status, 'message': message, 'percent': '100%'}

    elif status == 'error':
        message = f"Download error: {d.get('message', 'Unknown error')}"
        download_progress[session_id] = {'status': status, 'message': message, 'percent': '0%'}

@app.route('/download', methods=['POST'])
def start_download():
    """Starts the download and returns a unique session ID for streaming updates."""
    data = request.get_json()
    url = data.get('url')
    format_choice = data.get('format', 'mp4')
    subtitles = data.get('subtitles', False)
    
    # Generate a unique session ID for this download
    session_id = f"download_{int(time.time())}"
    download_progress[session_id] = {'status': 'pending', 'message': 'Starting download...', 'percent': '0%'}

    # Use a lambda to pass the session_id to the hook function
    def progress_callback(d):
        d['session_id'] = session_id
        yt_dlp_progress_hook(d)

    # Start the download in a separate thread
    content_type = get_content_type(url)
    audio_only = (format_choice == 'mp3')
    
    if content_type in ['playlist', 'channel_or_playlist']:
        thread = threading.Thread(target=download_playlist_with_opts, 
                                  args=(url, DOWNLOAD_FOLDER, audio_only, subtitles, progress_callback))
    else:
        thread = threading.Thread(target=download_video_with_opts, 
                                  args=(url, DOWNLOAD_FOLDER, audio_only, subtitles, progress_callback))

    thread.start()
    
    return jsonify({
        'success': True, 
        'message': 'Download started. Connecting to progress stream...',
        'session_id': session_id
    })

@app.route('/stream/<session_id>')
def stream_progress(session_id):
    """Serve real-time download progress via Server-Sent Events (SSE)."""
    
    def generate_events():
        stop_stream = False
        
        while not stop_stream:
            if session_id in download_progress:
                progress_info = download_progress[session_id]
                
                yield f"data: {json.dumps(progress_info)}\n\n"
                
                if progress_info['status'] in ['finished', 'error']:
                    stop_stream = True
                    if session_id in download_progress:
                        del download_progress[session_id]
            
            time.sleep(1)

    response = Response(stream_with_context(generate_events()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response

if __name__ == '__main__':
    print("--- YouTube Downloader Web UI ---")
    print(f"Downloads will be saved to: {DOWNLOAD_FOLDER}")
    print("Open your web browser and go to: http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)