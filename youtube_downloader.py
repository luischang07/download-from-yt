import customtkinter as ctk
from tkinter import filedialog, messagebox, Frame
import yt_dlp
import threading
import os
import sys
import time

# --- Configuración Robusta de VLC ---
VLC_AVAILABLE = False
try:
    if sys.platform == "win32":
        possible_vlc_paths = [
            r"C:\Program Files\VideoLAN\VLC",
            r"C:\Program Files (x86)\VideoLAN\VLC",
            os.path.join(os.getenv('LOCALAPPDATA', ''), 'Programs', 'VLC'),
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\VideoLAN"
        ]
        
        vlc_dir = None
        for p in possible_vlc_paths:
            if os.path.exists(os.path.join(p, "libvlc.dll")):
                vlc_dir = p
                break
        
        if vlc_dir:
            os.environ["PATH"] = vlc_dir + ";" + os.environ["PATH"]
            if hasattr(os, 'add_dll_directory'):
                os.add_dll_directory(vlc_dir)
            import vlc
            instance = vlc.Instance()
            instance.release()
            VLC_AVAILABLE = True
        else:
            print("Aviso: No se encontró la instalación de VLC en rutas estándar.")
    else:
        import vlc
        VLC_AVAILABLE = True
except Exception as e:
    print(f"Error inicializando motor de video: {e}")
    VLC_AVAILABLE = False
# ------------------------------------

class MediaPlayerFrame(ctk.CTkFrame):
    def __init__(self, parent, close_callback):
        super().__init__(parent)
        self.close_callback = close_callback
        self.instance = None
        self.player = None
        self.is_playing = False
        self.update_timer = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Botón de regreso
        top_bar = ctk.CTkFrame(self, height=40, fg_color="transparent")
        top_bar.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(top_bar, text="⬅ Volver", width=80, command=self.stop_and_close).pack(side="left")
        self.title_label = ctk.CTkLabel(top_bar, text="Reproductor", font=("Arial", 16, "bold"))
        self.title_label.pack(side="left", padx=20)

        # Área de video
        self.video_container = ctk.CTkFrame(self, fg_color="black")
        self.video_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Frame nativo para VLC (necesario para el HWND)
        self.video_frame = Frame(self.video_container, bg="black")
        self.video_frame.pack(fill="both", expand=True)
        
        # Controles
        self.controls_frame = ctk.CTkFrame(self, height=100)
        self.controls_frame.pack(fill="x", side="bottom", padx=10, pady=10)
        
        # --- Frame para Slider y Tiempo ---
        timeline_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        timeline_frame.pack(fill="x", padx=10, pady=5)

        # Slider de tiempo
        self.time_slider = ctk.CTkSlider(timeline_frame, from_=0, to=100, command=self.on_seek)
        self.time_slider.set(0)
        self.time_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Label de tiempo (00:00 / 00:00)
        self.time_label = ctk.CTkLabel(timeline_frame, text="00:00 / 00:00", font=("Consolas", 12))
        self.time_label.pack(side="right")
        # -----------------------------------------
        
        # Botones
        btn_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        btn_frame.pack(pady=5)
        
        # Botones de control
        ctk.CTkButton(btn_frame, text="⏪ -5s", width=60, command=lambda: self.seek_delta(-5000)).pack(side="left", padx=5)
        self.btn_play = ctk.CTkButton(btn_frame, text="⏸", width=60, command=self.toggle_play)
        self.btn_play.pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="+5s ⏩", width=60, command=lambda: self.seek_delta(5000)).pack(side="left", padx=5)
        
        # Volumen
        ctk.CTkLabel(btn_frame, text="🔊").pack(side="left", padx=(20, 5))
        self.vol_slider = ctk.CTkSlider(btn_frame, from_=0, to=100, width=100, command=self.set_volume)
        self.vol_slider.set(70)
        self.vol_slider.pack(side="left", padx=5)

    def format_ms(self, ms):
        """Convierte milisegundos a formato MM:SS o HH:MM:SS"""
        if ms < 0: ms = 0
        seconds = int(ms / 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def load_media(self, uri, title="Video"):
        self.title_label.configure(text=title)
        self.time_label.configure(text="00:00 / 00:00") # Resetear label
        
        if not VLC_AVAILABLE:
            self.show_internal_error()
            return

        try:
            # Limpiar instancia anterior si existe
            if self.player:
                self.player.stop()
                self.player.release()

            # Parámetros para evitar desincronización de audio (lag)
            args = [
                '--file-caching=1000',      # Buffer de archivo (1s)
                '--network-caching=1000',   # Buffer de red (1s)
                '--clock-jitter=0',         # Reducir jitter del reloj
                '--clock-synchro=0',        # Sincronización estricta
                '--quiet'
            ]
            if sys.platform.startswith('linux'):
                args.append('--no-xlib')
                
            self.instance = vlc.Instance(args)
            self.player = self.instance.media_player_new()
            
            if sys.platform == "win32":
                self.player.set_hwnd(self.video_frame.winfo_id())
            else:
                self.player.set_xwindow(self.video_frame.winfo_id())
                
            media = self.instance.media_new(uri)
            self.player.set_media(media)
            self.play()
            
            self.update_ui_loop()
        except Exception as e:
            print(f"Error VLC: {e}")
            self.show_internal_error()

    def show_internal_error(self):
        for widget in self.video_frame.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.video_frame, text="⚠️ Error: VLC no encontrado", text_color="white").pack(expand=True)

    def play(self):
        if self.player:
            self.player.play()
            self.is_playing = True
            self.btn_play.configure(text="⏸")

    def toggle_play(self):
        if not self.player: return
        
        # --- NUEVO: Lógica de reinicio ---
        # Si el video terminó (State.Ended), reiniciarlo desde el principio
        if self.player.get_state() == vlc.State.Ended:
            self.player.stop() # Resetear estado interno
            self.player.play() # Reproducir
            self.btn_play.configure(text="⏸")
            self.is_playing = True
            return
        # ---------------------------------

        if self.is_playing:
            self.player.pause()
            self.btn_play.configure(text="▶")
            self.is_playing = False
        else:
            self.player.play()
            self.btn_play.configure(text="⏸")
            self.is_playing = True

    def seek_delta(self, ms):
        """Adelantar o retrasar ms milisegundos"""
        if self.player:
            current_time = self.player.get_time()
            new_time = current_time + ms
            if new_time < 0: new_time = 0
            self.player.set_time(new_time)

    def stop_and_close(self):
        if self.update_timer:
            self.after_cancel(self.update_timer)
        if self.player:
            self.player.stop()
        self.close_callback()

    def set_volume(self, value):
        if self.player:
            self.player.audio_set_volume(int(value))

    def on_seek(self, value):
        if self.player:
            # --- NUEVO: Auto-play al arrastrar si estaba finalizado ---
            if self.player.get_state() == vlc.State.Ended:
                self.player.play() # Forzar play para reactivar el motor
                self.player.set_position(value / 100) # Ir a la posición
                self.btn_play.configure(text="⏸")
                self.is_playing = True
            else:
                self.player.set_position(value / 100)
            # ----------------------------------------------------------

    def update_ui_loop(self):
        if self.player:
            # --- NUEVO: Detectar fin natural del video ---
            if self.player.get_state() == vlc.State.Ended and self.is_playing:
                self.is_playing = False
                self.btn_play.configure(text="▶") # Cambiar icono a Play
                self.time_slider.set(100) # Poner barra al final
            # ---------------------------------------------

            if self.player.is_playing():
                try:
                    # Actualizar Slider
                    pos = self.player.get_position() * 100
                    self.time_slider.set(pos)
                    
                    # Actualizar Label de Tiempo
                    current_ms = self.player.get_time()
                    total_ms = self.player.get_length()
                    
                    if total_ms > 0:
                        time_str = f"{self.format_ms(current_ms)} / {self.format_ms(total_ms)}"
                        self.time_label.configure(text=time_str)
                    
                except: pass
        self.update_timer = self.after(1000, self.update_ui_loop)


class YouTubeDownloader:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("YouTube Downloader & Library")
        self.window.geometry("900x700")
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.download_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.available_formats = []
        self.is_searching = False
        self.search_timeout_task = None
        
        self.setup_main_layout()
        
    def setup_main_layout(self):
        # --- Sidebar (Menú Izquierdo) ---
        self.sidebar = ctk.CTkFrame(self.window, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        app_title = ctk.CTkLabel(self.sidebar, text="YT Downloader", font=ctk.CTkFont(size=20, weight="bold"))
        app_title.pack(pady=20, padx=10)
        
        self.btn_home = ctk.CTkButton(self.sidebar, text="🏠 Descargar", command=lambda: self.show_view("home"))
        self.btn_home.pack(pady=10, padx=20, fill="x")
        
        self.btn_lib = ctk.CTkButton(self.sidebar, text="📂 Biblioteca", command=lambda: self.show_view("library"))
        self.btn_lib.pack(pady=10, padx=20, fill="x")
        
        # --- Área de Contenido Principal ---
        self.content_area = ctk.CTkFrame(self.window, corner_radius=0, fg_color="transparent")
        self.content_area.pack(side="right", fill="both", expand=True)
        
        # Inicializar Vistas
        self.init_home_view()
        self.init_library_view()
        self.init_player_view()
        
        # Mostrar Home por defecto
        self.show_view("home")

    def init_home_view(self):
        self.home_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        
        # URL Input con botón de limpiar
        url_frame = ctk.CTkFrame(self.home_frame, fg_color="transparent")
        url_frame.pack(pady=(20, 10))
        
        ctk.CTkLabel(url_frame, text="URL del video:").pack(anchor="w")
        
        input_box = ctk.CTkFrame(url_frame, fg_color="transparent")
        input_box.pack(pady=5)
        
        self.url_entry = ctk.CTkEntry(input_box, width=400, placeholder_text="https://youtube.com/...")
        self.url_entry.pack(side="left", padx=(0, 5))
        
        # Botón Limpiar URL
        ctk.CTkButton(input_box, text="✖", width=30, fg_color="gray", command=lambda: self.url_entry.delete(0, 'end')).pack(side="left")
        
        # Opciones de descarga
        opts_frame = ctk.CTkFrame(self.home_frame)
        opts_frame.pack(pady=20, padx=20, fill="x")
        
        self.type_selector = ctk.CTkSegmentedButton(opts_frame, values=["Video", "Audio"], command=self.on_type_change)
        self.type_selector.set("Video")
        self.type_selector.pack(pady=10)
        
        # Botones de Búsqueda
        search_row = ctk.CTkFrame(opts_frame, fg_color="transparent")
        search_row.pack(pady=5)
        
        self.fetch_button = ctk.CTkButton(search_row, text="🔍 Buscar Calidades", command=self.fetch_formats)
        self.fetch_button.pack(side="left", padx=5)
        
        self.cancel_button = ctk.CTkButton(search_row, text="❌ Cancelar", command=self.cancel_search, fg_color="red", state="disabled", width=80)
        self.cancel_button.pack(side="left", padx=5)
        
        # Resultados
        results_frame = ctk.CTkFrame(opts_frame, fg_color="transparent")
        results_frame.pack(pady=10)
        
        self.quality_combo = ctk.CTkComboBox(results_frame, width=350, state="disabled", values=["Primero busca el video"])
        self.quality_combo.pack(side="left", padx=5)
        
        # Ruta
        path_frame = ctk.CTkFrame(self.home_frame, fg_color="transparent")
        path_frame.pack(pady=10)
        self.path_entry = ctk.CTkEntry(path_frame, width=300)
        self.path_entry.insert(0, self.download_path)
        self.path_entry.pack(side="left", padx=5)
        ctk.CTkButton(path_frame, text="Explorar", width=80, command=self.browse_folder).pack(side="left")
        
        # Progreso y Descarga
        self.progress_bar = ctk.CTkProgressBar(self.home_frame, width=400)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(self.home_frame, text="Listo", text_color="gray")
        self.status_label.pack()
        
        self.download_button = ctk.CTkButton(self.home_frame, text="⬇ Descargar", height=40, font=("Arial", 16, "bold"), command=self.start_download)
        self.download_button.pack(pady=20)

    def init_library_view(self):
        self.library_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        
        top_bar = ctk.CTkFrame(self.library_frame)
        top_bar.pack(fill="x", padx=10, pady=10)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self._filter_library)
        ctk.CTkEntry(top_bar, textvariable=self.search_var, placeholder_text="Buscar archivo...").pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkButton(top_bar, text="🔄", width=40, command=self._load_library_files).pack(side="right", padx=10)
        
        self.lib_tabs = ctk.CTkTabview(self.library_frame)
        self.lib_tabs.pack(fill="both", expand=True, padx=10, pady=5)
        self.lib_tabs.add("Todos")
        self.lib_tabs.add("Video")
        self.lib_tabs.add("Audio")
        
        self.scroll_frames = {}
        for tab in ["Todos", "Video", "Audio"]:
            self.scroll_frames[tab] = ctk.CTkScrollableFrame(self.lib_tabs.tab(tab))
            self.scroll_frames[tab].pack(fill="both", expand=True)

    def init_player_view(self):
        self.player_frame = MediaPlayerFrame(self.content_area, close_callback=lambda: self.show_view("last"))

    def show_view(self, view_name):
        # Ocultar todo
        self.home_frame.pack_forget()
        self.library_frame.pack_forget()
        self.player_frame.pack_forget()
        
        # Colorear botones sidebar
        self.btn_home.configure(fg_color="transparent", border_width=0)
        self.btn_lib.configure(fg_color="transparent", border_width=0)
        
        if view_name == "last":
            view_name = self.last_view if hasattr(self, 'last_view') else "home"

        if view_name == "home":
            self.home_frame.pack(fill="both", expand=True)
            self.btn_home.configure(fg_color=("gray75", "gray25"))
            self.last_view = "home"
        elif view_name == "library":
            self.library_frame.pack(fill="both", expand=True)
            self.btn_lib.configure(fg_color=("gray75", "gray25"))
            self._load_library_files()
            self.last_view = "library"
        elif view_name == "player":
            self.player_frame.pack(fill="both", expand=True)

    # --- Lógica del Reproductor ---
    def open_player(self, uri, title="Video"):
        self.show_view("player")
        # Forzar actualización de UI para que VLC encuentre el frame
        self.window.update_idletasks()
        self.player_frame.load_media(uri, title)

    # --- Lógica de Descarga ---
    def on_type_change(self, value):
        self.quality_combo.set("Primero busca el video")
        self.quality_combo.configure(state="disabled", values=["Primero busca el video"])
        self.available_formats = []

    def cancel_search(self, auto=False):
        if not self.is_searching: return
        self.is_searching = False
        if self.search_timeout_task:
            self.window.after_cancel(self.search_timeout_task)
            self.search_timeout_task = None
        self.fetch_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        msg = "Tiempo agotado" if auto else "Cancelado"
        self.status_label.configure(text=msg, text_color="orange")

    def fetch_formats(self):
        url = self.url_entry.get().strip()
        if not url: return
        
        self.is_searching = True
        self.fetch_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.status_label.configure(text="Analizando...", text_color="blue")
        self.search_timeout_task = self.window.after(10000, lambda: self.cancel_search(auto=True))
        
        threading.Thread(target=self._fetch_formats_thread, args=(url, self.type_selector.get()), daemon=True).start()

    def _fetch_formats_thread(self, url, mode):
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                if not self.is_searching: return
                info = ydl.extract_info(url, download=False)
                if not self.is_searching: return
                
                title = info.get('title', 'Video')
                formats = []
                
                if mode == "Audio":
                    formats.append(('best', {'label': '🎵 MP3 (Mejor)', 'format_id': 'bestaudio/best'}))
                else:
                    # Opción automática (Video + Audio)
                    formats.append(('auto', {'label': '🏆 Automático (Mejor)', 'format_id': 'bv*+ba/b'}))
                    
                    # Sonido en calidades específicas
                    for f in info.get('formats', []):
                        if f.get('height') and f.get('vcodec') != 'none':
                            height = f['height']
                            f_id = f['format_id']
                            
                            # Si el formato no tiene codec de audio (es video puro), forzamos la mezcla
                            if f.get('acodec') == 'none':
                                f_id = f"{f_id}+bestaudio"
                            
                            lbl = f"{height}p"
                            formats.append((lbl, {'label': f"📺 {lbl}", 'format_id': f_id}))
                
                # Eliminar duplicados manteniendo el orden
                unique_formats = {}
                formats.sort(key=lambda x: int(x[0].replace('p','')) if 'p' in x[0] else 99999, reverse=True)
                
                for _, data in formats:
                    if data['label'] not in unique_formats:
                        unique_formats[data['label']] = data
                
                self.available_formats = list(unique_formats.values())
                labels = [f['label'] for f in self.available_formats]
                
                if self.is_searching:
                    self.window.after(0, self._update_formats_ui, labels, title)
        except Exception as e:
            if self.is_searching: self.window.after(0, self._show_error, str(e))
        finally:
            if self.is_searching: self.window.after(0, self._finalize_search)

    def _finalize_search(self):
        self.is_searching = False
        if self.search_timeout_task: self.window.after_cancel(self.search_timeout_task)
        self.fetch_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")

    def _update_formats_ui(self, labels, title):
        self.quality_combo.configure(values=labels, state="readonly")
        if labels: self.quality_combo.set(labels[0])
        self.status_label.configure(text=f"Detectado: {title[:30]}...", text_color="green")

    def _show_error(self, msg):
        self.status_label.configure(text="Error", text_color="red")
        messagebox.showerror("Error", msg)

    def browse_folder(self):
        d = filedialog.askdirectory()
        if d:
            self.download_path = d
            self.path_entry.delete(0, 'end')
            self.path_entry.insert(0, d)

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url or not self.available_formats: return
        
        sel_label = self.quality_combo.get()
        sel_data = next((f for f in self.available_formats if f['label'] == sel_label), None)
        if not sel_data: return
        
        self.download_button.configure(state="disabled")
        threading.Thread(target=self._download_thread, args=(url, sel_data, self.download_path, self.type_selector.get()), daemon=True).start()

    def _download_thread(self, url, data, path, mode):
        try:
            def hook(d):
                if d['status'] == 'downloading':
                    total = d.get('total_bytes') or d.get('total_bytes_estimate') or 1
                    p = d.get('downloaded_bytes', 0) / total
                    self.window.after(0, self.progress_bar.set, p)
                    self.window.after(0, self.status_label.configure, {"text": f"{p*100:.0f}%", "text_color": "blue"})
            
            opts = {
                'outtmpl': os.path.join(path, '%(title)s_%(epoch)s.%(ext)s'),
                'progress_hooks': [hook],
                'format': data['format_id'],
                'merge_output_format': 'mp4'
            }
            
            if mode == "Audio":
                opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]
            else:
                # CORRECCIÓN: Forzar codificación de audio a AAC al unir video y audio.
                # Esto soluciona el problema de "sin sonido" en videos 4K (Opus -> MP4).
                opts['postprocessor_args'] = {'merger': ['-c:a', 'aac']}
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            
            self.window.after(0, lambda: [self.progress_bar.set(1), self.status_label.configure(text="¡Listo!", text_color="green"), messagebox.showinfo("Fin", "Descarga completada")])
        except Exception as e:
            self.window.after(0, self._show_error, str(e))
        finally:
            self.window.after(0, lambda: self.download_button.configure(state="normal"))

    # --- Biblioteca ---
    def _load_library_files(self):
        for f in self.scroll_frames.values():
            for w in f.winfo_children(): w.destroy()
            
        exts = {
            'Video': ['.mp4', '.mkv', '.webm', '.avi'],
            'Audio': ['.mp3', '.m4a', '.wav', '.flac']
        }
        
        self.all_files = []
        if os.path.exists(self.download_path):
            for f in os.listdir(self.download_path):
                fp = os.path.join(self.download_path, f)
                if os.path.isfile(fp):
                    ext = os.path.splitext(f)[1].lower()
                    ftype = next((k for k, v in exts.items() if ext in v), None)
                    if ftype:
                        self.all_files.append({'name': f, 'path': fp, 'type': ftype})
        
        self._render_library(self.all_files)

    def _render_library(self, files):
        for f in self.scroll_frames.values():
            for w in f.winfo_children(): w.destroy()
            
        for item in files:
            self._add_lib_item(self.scroll_frames["Todos"], item)
            self._add_lib_item(self.scroll_frames[item['type']], item)

    def _add_lib_item(self, parent, item):
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", pady=2)
        icon = "📺" if item['type'] == "Video" else "🎵"
        ctk.CTkLabel(row, text=f"{icon} {item['name']}", anchor="w").pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkButton(row, text="▶", width=40, fg_color="green", command=lambda: self.open_player(item['path'], item['name'])).pack(side="right", padx=5)

    def _filter_library(self, *args):
        q = self.search_var.get().lower()
        if hasattr(self, 'all_files'):
            self._render_library([f for f in self.all_files if q in f['name'].lower()])

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = YouTubeDownloader()
    app.run()
