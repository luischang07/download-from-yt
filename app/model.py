import os
import sys
import yt_dlp
import threading

class DownloaderModel:
    """Handles all download and format fetching logic using yt_dlp."""

    def __init__(self):
        self.is_searching = False
        self.search_timeout_task = None

    def fetch_formats(self, url: str, mode: str):
        """Return a list of format dictionaries for the given URL and mode.
        Each dict contains 'label' and 'format_id'."""
        if not url:
            return []
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Video')
            formats = []
            if mode == "Audio":
                formats.append({'label': '🎵 MP3 (Mejor)', 'format_id': 'bestaudio/best'})
            else:
                formats.append({'label': '🏆 Automático (Mejor)', 'format_id': 'bv*+ba/b'})
                for f in info.get('formats', []):
                    if f.get('height') and f.get('vcodec') != 'none':
                        height = f['height']
                        fmt_id = f['format_id']
                        if f.get('acodec') == 'none':
                            fmt_id = f"{fmt_id}+bestaudio"
                        formats.append({'label': f"📺 {height}p", 'format_id': fmt_id})
            # Remove duplicates while preserving order
            seen = set()
            unique = []
            for fmt in formats:
                if fmt['label'] not in seen:
                    seen.add(fmt['label'])
                    unique.append(fmt)
            return unique, title

    def download(self, url: str, format_id: str, path: str, mode: str, progress_callback=None):
        """Download the given URL with selected format.
        `progress_callback` receives a dict from yt_dlp progress hook."""
        
        opts = {
            'format': format_id,
            'progress_hooks': [progress_callback] if progress_callback else [],
            'quiet': True,
        }
        
        if mode == "Audio":
            opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]
        else:
            # Force MP4 container for video
            opts['merge_output_format'] = 'mp4'
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            # Capture the original method to avoid recursion
            original_prepare_filename = ydl.prepare_filename

            def prepare_filename_custom(info):
                # Use the original method to generate the base filename
                # We explicitly pass the outtmpl here to enforce "Title.ext" format
                target_outtmpl = os.path.join(path, '%(title)s.%(ext)s')
                fn = original_prepare_filename(info, outtmpl=target_outtmpl)
                
                if not os.path.exists(fn):
                    return fn
                
                # Handle duplicates: Title (1).ext, Title (2).ext, etc.
                base, ext = os.path.splitext(fn)
                i = 1
                while True:
                    new_fn = f"{base} ({i}){ext}"
                    if not os.path.exists(new_fn):
                        return new_fn
                    i += 1

            # Wrapper to match yt_dlp's expected signature (accepts kwargs like outtmpl)
            def wrapped_prepare_filename(info, *args, **kwargs):
                return prepare_filename_custom(info)
            
            # Apply the patch
            ydl.prepare_filename = wrapped_prepare_filename
            ydl.download([url])
