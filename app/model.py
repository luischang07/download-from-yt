import os
import json
import threading
import time
import requests
import subprocess
import sys
from io import BytesIO
from PIL import Image
from functools import lru_cache

class DownloaderModel:
    def __init__(self):
        self.config_file = "config.json"
        self.download_path = self.load_config()
        self.current_video_info = None
        self.available_formats = []
        self.preview_url = None
        self.preview_formats = {}
        self.download_queue = []

    @lru_cache(maxsize=50)
    def load_thumbnail_image(self, url):
        try:
            response = requests.get(url)
            img_data = BytesIO(response.content)
            pil_image = Image.open(img_data)
            return pil_image
        except:
            return None

    def load_config(self):
        default_path = os.path.join(os.path.expanduser("~"), "Downloads")
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    path = data.get('download_path', '')
                    if path and os.path.exists(path):
                        return path
        except Exception as e:
            print(f"Error cargando config: {e}")
        return default_path

    def save_config(self, path):
        self.download_path = path
        try:
            with open(self.config_file, 'w') as f:
                json.dump({'download_path': self.download_path}, f)
        except Exception as e:
            print(f"Error guardando config: {e}")

    def _get_ffmpeg_path(self):
        """Obtiene la ruta de ffmpeg dependiendo de si es script o EXE"""
        import sys
        
        # 1. Si es un EXE compilado (PyInstaller)
        if getattr(sys, 'frozen', False):
            # Opción A: Si está en la misma carpeta que el EXE (instalación estándar)
            exe_dir = os.path.dirname(sys.executable)
            ffmpeg_exe = os.path.join(exe_dir, 'ffmpeg.exe')
            if os.path.exists(ffmpeg_exe):
                return exe_dir
                
            # Opción B: Si está empaquetado dentro del EXE (onefile)
            if hasattr(sys, '_MEIPASS'):
                return sys._MEIPASS
                
        # 2. Si es script de desarrollo
        else:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ffmpeg_dev = os.path.join(project_root, 'ffmpeg.exe')
            if os.path.exists(ffmpeg_dev):
                return project_root
                
        return None # Dejar que yt-dlp busque en PATH

    def fetch_video_info(self, url, callback_success, callback_error):
        def _thread():
            try:
                import yt_dlp
                opts = {'quiet': True}
                ffmpeg_loc = self._get_ffmpeg_path()
                if ffmpeg_loc:
                    opts['ffmpeg_location'] = ffmpeg_loc
                    
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    self.current_video_info = info
                    callback_success(info)
            except Exception as e:
                callback_error(str(e))
        
        threading.Thread(target=_thread, daemon=True).start()

    def process_formats(self, mode):
        if not self.current_video_info: return [], None, None, {}

        info = self.current_video_info
        title = info.get('title', 'Video')
        thumbnail_url = info.get('thumbnail', None)
        
        # Preview Logic
        self.preview_url = None
        self.preview_formats = {}
        formats_list = info.get('formats', [])
        
        for f in formats_list:
            if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('url'):
                height = f.get('height', 0)
                if height:
                    label = f"{height}p"
                    self.preview_formats[label] = f['url']

        if '720p' in self.preview_formats:
            self.preview_url = self.preview_formats['720p']
        elif '360p' in self.preview_formats:
            self.preview_url = self.preview_formats['360p']
        elif self.preview_formats:
            self.preview_url = list(self.preview_formats.values())[-1]

        # Download Formats Logic
        formats = []
        if mode == "Audio":
            formats.append(('best', {'label': '🎵 MP3 (Mejor)', 'format_id': 'bestaudio/best'}))
        else:
            formats.append(('auto', {'label': '🏆 Automático (Mejor)', 'format_id': 'bv*+ba/b'}))
            for f in info.get('formats', []):
                if f.get('height') and f.get('vcodec') != 'none':
                    height = f['height']
                    f_id = f['format_id']
                    if f.get('acodec') == 'none': f_id = f"{f_id}+bestaudio"
                    lbl = f"{height}p"
                    formats.append((lbl, {'label': f"📺 {lbl}", 'format_id': f_id}))
        
        unique_formats = {}
        formats.sort(key=lambda x: int(x[0].replace('p','')) if 'p' in x[0] else 99999, reverse=True)
        for _, data in formats:
            if data['label'] not in unique_formats: unique_formats[data['label']] = data
        
        self.available_formats = list(unique_formats.values())
        return self.available_formats, title, thumbnail_url, self.preview_formats

    def add_to_queue(self, url, format_data, mode, filename, title, thumbnail_url):
        item = {
            'url': url,
            'format_data': format_data,
            'mode': mode,
            'filename': filename,
            'title': title,
            'thumbnail_url': thumbnail_url,
            'status': 'pending', # pending, downloading, completed, error
            'progress': 0
        }
        self.download_queue.append(item)
        return len(self.download_queue) - 1 # Return index

    def _download_item_sync(self, url, format_data, mode, filename, progress_callback):
        def hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 1
                p = d.get('downloaded_bytes', 0) / total
                if progress_callback:
                    progress_callback(p)
        
        path = self.download_path
        
        # Ensure unique filename to avoid skipping download
        ext = "mp3" if mode == "Audio" else "mp4"
        existing_files = set(os.listdir(path))
        base_filename = filename
        counter = 1
        while f"{base_filename}.{ext}" in existing_files:
            base_filename = f"{filename} (#{counter})"
            counter += 1
        
        opts = {
            'outtmpl': os.path.join(path, f'{base_filename}.%(ext)s'),
            'progress_hooks': [hook],
            'format': format_data['format_id'],
            'merge_output_format': 'mp4',
            'extractor_args': {'youtube': {'player_client': ['default']}},
            'keepvideo': False,
            'writethumbnail': True,
            'quiet': True,
            'no_warnings': True
        }
        
        ffmpeg_loc = self._get_ffmpeg_path()
        if ffmpeg_loc:
            opts['ffmpeg_location'] = ffmpeg_loc

        if mode == "Audio":
            opts['postprocessors'] = [
                {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'},
                {'key': 'FFmpegMetadata'},
                {'key': 'EmbedThumbnail'},
            ]
        else:
            opts['postprocessor_args'] = {'merger': ['-c:a', 'aac']}

        import yt_dlp
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        # Cleanup Logic
        final_ext = ".mp3" if mode == "Audio" else ".mp4"
        final_file = os.path.join(path, f"{base_filename}{final_ext}")
        
        if os.path.exists(final_file):
            garbage_exts = ['.webm', '.m4a', '.part', '.ytdl', '.orig', '.temp.mp4']
            try:
                # Allow a short delay to ensure yt-dlp/ffmpeg and the filesystem
                # have fully flushed and closed all related files before cleanup.
                time.sleep(1)
                for f in os.listdir(path):
                    if f.startswith(base_filename):
                        full_path = os.path.join(path, f)
                        if full_path != final_file and not f.endswith(('.jpg', '.webp', '.png')):
                            if any(f.endswith(ext) for ext in garbage_exts) or f.endswith(f".f{format_data['format_id']}.mp4"):
                                try:
                                    os.remove(full_path)
                                except: pass
            except: pass

    def process_queue(self, progress_callback, item_complete_callback, all_complete_callback, error_callback):
        def _thread():
            for i, item in enumerate(self.download_queue):
                if item['status'] == 'completed': continue
                
                item['status'] = 'downloading'
                try:
                    # Wrapper for progress to include index
                    def item_progress(p):
                        item['progress'] = p
                        progress_callback(i, p)
                    
                    self._download_item_sync(
                        item['url'], 
                        item['format_data'], 
                        item['mode'], 
                        item['filename'], 
                        item_progress
                    )
                    
                    item['status'] = 'completed'
                    item['progress'] = 1.0
                    item_complete_callback(i)
                    
                except Exception as e:
                    item['status'] = 'error'
                    error_callback(i, str(e))
            
            all_complete_callback()
            # self.download_queue = [] 

        threading.Thread(target=_thread, daemon=True).start()

    def download_video(self, url, format_data, mode, filename, progress_callback, complete_callback, error_callback):
        def _thread():
            try:
                self._download_item_sync(url, format_data, mode, filename, progress_callback)
                complete_callback()
            except Exception as e:
                error_callback(str(e))
        
        threading.Thread(target=_thread, daemon=True).start()

    def get_library_files(self):
        exts = {'Video': ['.mp4', '.mkv', '.webm', '.avi'], 'Audio': ['.mp3', '.m4a', '.wav', '.flac']}
        files = []
        if os.path.exists(self.download_path):
            for f in os.listdir(self.download_path):
                fp = os.path.join(self.download_path, f)
                if os.path.isfile(fp):
                    ext = os.path.splitext(f)[1].lower()
                    ftype = next((k for k, v in exts.items() if ext in v), None)
                    if ftype: files.append({'name': f, 'path': fp, 'type': ftype})
        return files

    # --- NUEVO: Método de Actualización ---
    def update_ytdlp(self):
        try:
            # Verifica si está corriendo como ejecutable congelado (EXE)
            if getattr(sys, 'frozen', False):
                return False, "No se puede actualizar en versión EXE (Reinstala la app)"
            
            # Ejecuta pip install --upgrade yt-dlp
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
            return True, "Motor actualizado a la última versión"
        except Exception as e:
            print(f"Error actualizando: {e}")
            return False, "Error al actualizar el motor"
    # --------------------------------------
