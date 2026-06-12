import customtkinter as ctk
from tkinter import Frame, messagebox
import os
import sys
import time

# --- Configuración Robusta de VLC ---
VLC_AVAILABLE = False
try:
    if sys.platform == "win32":
        possible_vlc_paths = []
        
        # 1. Rutas Portables (Prioridad)
        if getattr(sys, 'frozen', False):
            # Si es un EXE compilado con PyInstaller
            # Opción A: VLC embebido dentro del EXE (sys._MEIPASS)
            possible_vlc_paths.append(os.path.join(sys._MEIPASS, 'vlc'))
            # Opción B: VLC en carpeta junto al EXE
            possible_vlc_paths.append(os.path.join(os.path.dirname(sys.executable), 'vlc'))
        else:
            # Entorno de desarrollo (script .py)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            possible_vlc_paths.append(os.path.join(project_root, 'vlc'))

        # 2. Rutas de Instalación Estándar
        possible_vlc_paths.extend([
            r"C:\Program Files\VideoLAN\VLC",
            r"C:\Program Files (x86)\VideoLAN\VLC",
            os.path.join(os.getenv('LOCALAPPDATA', ''), 'Programs', 'VLC'),
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\VideoLAN"
        ])
        
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
        super().__init__(parent, fg_color="transparent") # Fondo transparente para integrarse
        self.close_callback = close_callback
        self.instance = None
        self.player = None
        self.is_playing = False
        self.update_timer = None
        self.is_changing_quality = False # Flag para evitar conflictos durante el cambio
        self.is_fullscreen = False
        self.hide_job = None
        self.restore_job = None # Job para restaurar estado tras switch_output
        self.state_callback = None # Callback para notificar cambios de estado (play/pause)
        
        self.setup_ui()

    def set_state_callback(self, callback):
        self.state_callback = callback
        
    def setup_ui(self):
        # --- Cabecera Minimalista (Estilo Oscuro) ---
        self.top_bar = ctk.CTkFrame(self, height=40, fg_color="#0f0f0f", corner_radius=0)
        self.top_bar.pack(fill="x", side="top")
        
        # Botón Cerrar a la derecha
        ctk.CTkButton(self.top_bar, text="✕", width=40, height=30, 
        command=self.stop_and_close, 
        fg_color="transparent", hover_color="#cc0000",
        font=("Arial", 16, "bold"), text_color="white").pack(side="right", padx=10, pady=5)

        # Botón Ayuda
        ctk.CTkButton(self.top_bar, text="?", width=30, height=30,
                     command=self.show_controls_info,
                     fg_color="transparent", hover_color="gray30",
                     font=("Arial", 14, "bold"), text_color="white").pack(side="right", padx=0, pady=5)
              
        self.title_label = ctk.CTkLabel(self.top_bar, text="Reproductor", font=("Segoe UI", 14), text_color="gray80")
        self.title_label.pack(side="left", padx=15)

        # --- Área de Video ---
        self.video_container = ctk.CTkFrame(self, fg_color="black", corner_radius=0)
        self.video_container.pack(fill="both", expand=True)
        
        # Frame nativo para VLC
        self.video_frame = Frame(self.video_container, bg="black")
        self.video_frame.pack(fill="both", expand=True)
        
        # --- Barra de Controles (Estilo YouTube Moderno) ---
        self.controls_frame = ctk.CTkFrame(self, height=80, fg_color="#0f0f0f", corner_radius=0)
        self.controls_frame.pack(fill="x", side="bottom")
        
        # 1. Barra de Progreso (Estilizada)
        self.time_slider = ctk.CTkSlider(self.controls_frame, from_=0, to=100, command=self.on_seek, 
                                        height=18, border_width=0, 
                                        fg_color="#333333",             # Track oscuro
                                        progress_color="#ff0000",       # Progreso Rojo
                                        button_color="#ff0000",         # Botón Rojo
                                        button_hover_color="#ff4d4d")   # Hover más claro
        self.time_slider.set(0)
        self.time_slider.pack(fill="x", padx=0, pady=(0, 5))
        
        # 2. Fila de Botones
        self.buttons_row = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        self.buttons_row.pack(fill="x", padx=20, pady=(5, 20))
        
        # --- Izquierda: Controles de Reproducción y Volumen ---
        left_frame = ctk.CTkFrame(self.buttons_row, fg_color="transparent")
        left_frame.pack(side="left")

        # Botones de Navegación (Prev - Play - Next)
        ctk.CTkButton(left_frame, text="⏮", width=35, height=35, corner_radius=17,
                     fg_color="transparent", hover_color="#333333", text_color="white", font=("Arial", 18),
                     command=lambda: self.seek_delta(-5000)).pack(side="left", padx=2)

        # Play/Pause (Destacado - Círculo Blanco)
        self.btn_play = ctk.CTkButton(left_frame, text="▶", width=45, height=45, corner_radius=22, 
                                     font=("Arial", 22), 
                                     fg_color="white",              # Fondo blanco
                                     text_color="black",            # Icono negro
                                     hover_color="#e0e0e0",
                                     command=self.toggle_play)
        self.btn_play.pack(side="left", padx=10)

        ctk.CTkButton(left_frame, text="⏭", width=35, height=35, corner_radius=17,
                     fg_color="transparent", hover_color="#333333", text_color="white", font=("Arial", 18),
                     command=lambda: self.seek_delta(5000)).pack(side="left", padx=2)

        # Volumen
        self.vol_container = ctk.CTkFrame(left_frame, fg_color="transparent")
        self.vol_container.pack(side="left", padx=(20, 0))
        
        self.vol_icon = ctk.CTkButton(self.vol_container, text="🔊", width=30, height=30, corner_radius=15,
                                     fg_color="transparent", hover_color="#333333", text_color="white", 
                                     font=("Arial", 16), command=self.toggle_mute)
        self.vol_icon.pack(side="left")
        
        self.vol_slider = ctk.CTkSlider(self.vol_container, from_=0, to=100, width=80, height=14,
                                       command=self.set_volume, 
                                       fg_color="#333333", progress_color="white", button_color="white", button_hover_color="#e0e0e0")
        self.vol_slider.set(70)
        self.vol_slider.pack(side="left", padx=5)

        # Tiempo
        self.time_label = ctk.CTkLabel(left_frame, text="00:00 / 00:00", font=("Segoe UI", 13), text_color="#aaaaaa")
        self.time_label.pack(side="left", padx=15)

        # --- Derecha: Calidad y Pantalla Completa ---
        right_frame = ctk.CTkFrame(self.buttons_row, fg_color="transparent")
        right_frame.pack(side="right")

        # Selector de Calidad
        self.quality_menu = ctk.CTkOptionMenu(right_frame, values=["Default"], width=90, height=28,
                                            command=self.change_quality,
                                            fg_color="#2b2b2b",             # Fondo oscuro
                                            button_color="#2b2b2b",         # Botón oscuro
                                            button_hover_color="#3a3a3a",   # Hover más claro
                                            text_color="white",
                                            dropdown_fg_color="#2b2b2b",
                                            dropdown_hover_color="#3a3a3a",
                                            dropdown_text_color="white")
        # self.quality_menu.pack(side="left", padx=10)

        # Botón Picture-in-Picture (PiP)
        ctk.CTkButton(right_frame, text="⧉", width=40, height=40, corner_radius=20,
                     command=self.on_pip_click,
                     fg_color="transparent", hover_color="#333333", text_color="white", font=("Arial", 18)).pack(side="left", padx=5)

        # Pantalla Completa
        ctk.CTkButton(right_frame, text="⛶", width=40, height=40, corner_radius=20,
                     command=self.toggle_fullscreen,
                     fg_color="transparent", hover_color="#333333", text_color="white", font=("Arial", 18)).pack(side="right", padx=5)

    def setup_shortcuts(self):
        root = self.winfo_toplevel()
        root.bind("<Key>", self.on_key_press)

    def on_pip_click(self):
        if self.close_callback:
            # Usamos el callback de cierre para volver a la vista anterior, 
            # lo que activará automáticamente el mini player gracias a la lógica del controlador
            self.close_callback()

    def on_key_press(self, event):
        if not self.winfo_ismapped(): return
        
        # Ignorar si se está escribiendo en un input
        if isinstance(event.widget, (ctk.CTkEntry, ctk.CTkTextbox)):
            return

        key = event.keysym
        if key in ['f', 'F']:
            self.toggle_fullscreen()
        elif key == 'Escape':
            if self.is_fullscreen:
                self.toggle_fullscreen()
            else:
                self.minimize()
        elif key == 'space':
            self.toggle_play()
        elif key == 'Right':
            self.seek_delta(5000)
        elif key == 'Left':
            self.seek_delta(-5000)
        elif key == 'Up':
            self.change_volume(5)
        elif key == 'Down':
            self.change_volume(-5)
        elif key in ['m', 'M']:
            self.toggle_mute()

    def toggle_mute(self):
        if not self.player: return
        
        self.player.audio_toggle_mute()
        is_muted = self.player.audio_get_mute()
        self.vol_icon.configure(text="🔇" if is_muted else "🔊")

    def change_volume(self, delta):
        current = self.vol_slider.get()
        new_vol = max(0, min(100, current + delta))
        self.vol_slider.set(new_vol)
        self.set_volume(new_vol)

    def format_ms(self, ms):
        """Convierte milisegundos a formato MM:SS o HH:MM:SS"""
        if ms < 0: ms = 0
        seconds = int(ms / 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def load_media(self, uri, title="Video", formats=None):
        # Cancelar restauración pendiente si existe (para evitar conflictos al cambiar video rápido)
        if self.restore_job:
            self.after_cancel(self.restore_job)
            self.restore_job = None

        # Detener actualizaciones anteriores para evitar conflictos de UI
        if self.update_timer:
            self.after_cancel(self.update_timer)
            self.update_timer = None

        self.title_label.configure(text=title)
        self.time_label.configure(text="00:00 / 00:00") # Resetear label
        self.time_slider.set(0) # Resetear slider para nuevo video
        if getattr(self, 'mini_progress_bar', None):
            try: self.mini_progress_bar.set(0)
            except: pass
        
        # Configurar bindings si no se han configurado
        if not hasattr(self, 'shortcuts_bound'):
            self.setup_shortcuts()
            self.shortcuts_bound = True
        
        # Configurar selector de calidad
        self.current_formats = formats
        if formats and len(formats) > 1:
            # Ordenar: 1080p, 720p, 480p, 360p...
            def sort_key(k):
                try: return int(k.replace('p', ''))
                except: return 0
            
            keys = sorted(list(formats.keys()), key=sort_key, reverse=True)
            self.quality_menu.configure(values=keys)
            
            # Seleccionar calidad actual
            current_q = keys[0]
            for k, v in formats.items():
                if v == uri:
                    current_q = k
                    break
            self.quality_menu.set(current_q)
            self.quality_menu.pack(side="left", padx=(0, 10))
        else:
            self.quality_menu.pack_forget()

        self._init_player(uri)

    def change_quality(self, value):
        if not self.current_formats or value not in self.current_formats: return
        
        self.is_changing_quality = True # Bloquear actualizaciones de UI
        new_url = self.current_formats[value]
        
        # Guardar tiempo actual
        current_time = 0
        if self.player:
            try:
                current_time = self.player.get_time()
                self.player.set_pause(1) # Pausar primero para liberar recursos
            except: pass
            
        # Realizar el cambio con un pequeño delay para permitir que VLC procese el stop/pause
        self.after(100, lambda: self._perform_quality_switch(new_url, current_time))

    def _perform_quality_switch(self, url, start_time):
        try:
            # Detener completamente
            if self.player:
                self.player.stop()
            
            # Crear nuevo media
            media = self.instance.media_new(url)
            self.player.set_media(media)
            self.player.play()
            
            # Función recursiva para restaurar el tiempo una vez que empiece a reproducir
            def restore_time(attempts=0):
                if attempts > 20: # Timeout de 2 segundos
                    self.is_changing_quality = False
                    return

                if self.player.is_playing():
                    if start_time > 0:
                        self.player.set_time(start_time)
                    self.is_changing_quality = False
                else:
                    # Reintentar en 100ms
                    self.after(100, lambda: restore_time(attempts + 1))
            
            self.after(200, restore_time)
            
        except Exception as e:
            print(f"Error switching quality: {e}")
            self.is_changing_quality = False

    def _init_player(self, uri):
        if not VLC_AVAILABLE:
            self.show_internal_error()
            return

        try:
            # Reutilizar instancia si existe para evitar crashes por recreación rápida
            if not self.instance:
                # Parámetros optimizados para sincronización y respuesta instantánea
                # NOTA: Algunos parámetros avanzados pueden causar errores en versiones antiguas de VLC
                # Se han simplificado para mayor compatibilidad
                args = [
                    '--file-caching=3000',      
                    '--network-caching=3000',   
                    '--quiet',
                    '--no-video-title-show'
                ]
                if sys.platform.startswith('linux'):
                    args.append('--no-xlib')
                    
                self.instance = vlc.Instance(args)
                self.player = self.instance.media_player_new()
                
                if sys.platform == "win32":
                    self.player.set_hwnd(self.video_frame.winfo_id())
                else:
                    self.player.set_xwindow(self.video_frame.winfo_id())
                
                # Deshabilitar input de mouse en VLC para que Tkinter reciba los eventos
                self.player.video_set_mouse_input(False)
                self.player.video_set_key_input(False)
            else:
                # Si ya existe, solo detenemos para cargar el nuevo media
                self.player.stop()

            media = self.instance.media_new(uri)
            self.player.set_media(media)
            self.play()
            
            if not self.update_timer:
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
            if getattr(self, 'mini_play_btn', None): self.mini_play_btn.configure(text="⏸")
            self.is_playing = True
            if self.state_callback: self.state_callback(True)
            return
        # ---------------------------------

        if self.is_playing:
            self.player.set_pause(1)
            self.btn_play.configure(text="▶")
            if getattr(self, 'mini_play_btn', None): self.mini_play_btn.configure(text="▶")
            self.is_playing = False
            if self.state_callback: self.state_callback(False)
        else:
            self.player.set_pause(0)
            self.btn_play.configure(text="⏸")
            if getattr(self, 'mini_play_btn', None): self.mini_play_btn.configure(text="⏸")
            self.is_playing = True
            if self.state_callback: self.state_callback(True)

    def seek_delta(self, ms):
        """Adelantar o retrasar ms milisegundos"""
        if self.player:
            current_time = self.player.get_time()
            new_time = current_time + ms
            if new_time < 0: new_time = 0
            self.player.set_time(new_time)

    def stop_and_close(self):
        """Cierra el reproductor completamente (Botón X)"""
        if self.update_timer:
            self.after_cancel(self.update_timer)
        
        # Detener explícitamente
        if self.player:
            self.player.stop()
            # Intentar limpiar media para indicar estado 'Stopped' definitivo
            # self.player.set_media(None) # Esto a veces causa crash en VLC, mejor confiar en stop()
        
        self.is_playing = False
        
        # Salir de pantalla completa si está activa
        if self.is_fullscreen:
            self.toggle_fullscreen()
            
        self.close_callback()

    def minimize(self):
        """Minimiza el reproductor sin detenerlo (Tecla ESC)"""
        # NO llamamos a stop(). Dejamos que el controlador maneje la transición.
        if self.is_fullscreen:
            self.toggle_fullscreen()
        self.close_callback()

    def stop(self):
        """Detiene la reproducción sin cerrar el frame (usado por Mini Player)"""
        if self.player:
            self.player.stop()
        self.is_playing = False
        self.btn_play.configure(text="▶")
        if getattr(self, 'mini_play_btn', None):
            self.mini_play_btn.configure(text="▶")

    # --- NUEVO: Soporte para Mini Reproductor ---
    def set_mini_ui(self, title_lbl=None, progress_bar=None, play_btn=None):
        self.mini_title_lbl = title_lbl
        self.mini_progress_bar = progress_bar
        self.mini_play_btn = play_btn

    def switch_output(self, widget_id):
        if not self.player: return
        
        # Guardar estado
        t = self.player.get_time()
        was_playing = self.player.is_playing()
        
        # Cambiar ventana de salida (requiere stop/play en la mayoría de plataformas)
        self.player.stop()
        if sys.platform == "win32":
            self.player.set_hwnd(widget_id)
        else:
            self.player.set_xwindow(widget_id)
            
        self.player.play()
        
        # Restaurar estado
        # Pequeño delay para asegurar que VLC ha inicializado el nuevo video output
        def restore():
            self.player.set_time(t)
            if not was_playing:
                self.player.set_pause(1)
            else:
                self.is_playing = True
                self.btn_play.configure(text="⏸")
                if getattr(self, 'mini_play_btn', None):
                    self.mini_play_btn.configure(text="⏸")
            self.restore_job = None

        self.restore_job = self.after(100, restore)
    # --------------------------------------------

    def set_volume(self, value):
        if self.player:
            self.player.audio_set_volume(int(value))
            # Si se mueve el slider, asegurar que el icono se actualice si estaba muteado
            if self.player.audio_get_mute():
                self.player.audio_set_mute(False)
                self.vol_icon.configure(text="🔊")

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
        if self.player and not self.is_changing_quality:
            # --- NUEVO: Detectar fin natural del video ---
            if self.player.get_state() == vlc.State.Ended and self.is_playing:
                self.is_playing = False
                self.btn_play.configure(text="▶") # Cambiar icono a Play
                self.time_slider.set(100) # Poner barra al final
                if getattr(self, 'mini_progress_bar', None):
                    try: self.mini_progress_bar.set(100)
                    except: pass
            # ---------------------------------------------

            if self.player.is_playing():
                try:
                    # Actualizar Slider
                    pos = self.player.get_position() * 100
                    self.time_slider.set(pos)
                    
                    # Actualizar slider del mini reproductor
                    if getattr(self, 'mini_progress_bar', None):
                        try: self.mini_progress_bar.set(pos)
                        except: pass

                    # Actualizar Label de Tiempo
                    current_ms = self.player.get_time()
                    total_ms = self.player.get_length()
                    
                    if total_ms > 0:
                        time_str = f"{self.format_ms(current_ms)} / {self.format_ms(total_ms)}"
                        self.time_label.configure(text=time_str)
                    
                except: pass
        self.update_timer = self.after(1000, self.update_ui_loop)

    def toggle_fullscreen(self):
        if self.is_fullscreen:
            self._exit_fullscreen()
        else:
            self._enter_fullscreen()

    # ---- Fullscreen via dedicated Toplevel (guarantees 100% screen coverage) ----

    def _enter_fullscreen(self):
        if self.is_fullscreen:
            return
        self.is_fullscreen = True
        root = self.winfo_toplevel()

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()

        # Borderless Toplevel that covers the entire monitor
        self._fs_win = ctk.CTkToplevel(root)
        self._fs_win.overrideredirect(True)
        self._fs_win.geometry(f"{sw}x{sh}+0+0")
        self._fs_win.attributes('-topmost', True)
        self._fs_win.configure(fg_color='black')
        self._fs_win.focus_force()
        self._fs_win.update_idletasks()

        # Native tkinter Frame for VLC (fills the whole window)
        from tkinter import Frame as _TkFrame
        self._fs_video_frame = _TkFrame(self._fs_win, bg='black')
        self._fs_video_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._fs_win.update_idletasks()

        # ---- Controls overlay (auto-hide on inactivity) ----
        self._fs_controls_bar = ctk.CTkFrame(
            self._fs_win, height=80, fg_color='#0f0f0f', corner_radius=0)

        # Progress slider
        self._fs_slider = ctk.CTkSlider(
            self._fs_controls_bar, from_=0, to=100,
            command=self.on_seek, height=16,
            fg_color='#333333', progress_color='#ff0000',
            button_color='#ff0000', button_hover_color='#ff4d4d')
        self._fs_slider.set(self.time_slider.get())
        self._fs_slider.pack(fill='x', padx=0, pady=(4, 0))

        btn_row = ctk.CTkFrame(self._fs_controls_bar, fg_color='transparent')
        btn_row.pack(fill='x', padx=20, pady=(4, 12))

        # Play / Pause
        self._fs_btn_play = ctk.CTkButton(
            btn_row, text='⏸' if self.is_playing else '▶',
            width=45, height=45, corner_radius=22,
            font=('Arial', 22), fg_color='white',
            text_color='black', hover_color='#e0e0e0',
            command=self.toggle_play)
        self._fs_btn_play.pack(side='left', padx=10)

        # Seek back / forward
        ctk.CTkButton(btn_row, text='⏮', width=35, height=35, corner_radius=17,
                      fg_color='transparent', hover_color='#333333',
                      text_color='white', font=('Arial', 18),
                      command=lambda: self.seek_delta(-5000)).pack(side='left', padx=2)
        ctk.CTkButton(btn_row, text='⏭', width=35, height=35, corner_radius=17,
                      fg_color='transparent', hover_color='#333333',
                      text_color='white', font=('Arial', 18),
                      command=lambda: self.seek_delta(5000)).pack(side='left', padx=2)

        # Time label (syncs via update loop)
        self._fs_time_label = ctk.CTkLabel(
            btn_row, text=self.time_label.cget('text'),
            font=('Segoe UI', 13), text_color='#aaaaaa')
        self._fs_time_label.pack(side='left', padx=15)

        # Exit fullscreen button (right side)
        ctk.CTkButton(btn_row, text='⛶', width=40, height=40, corner_radius=20,
                      fg_color='transparent', hover_color='#333333',
                      text_color='white', font=('Arial', 18),
                      command=self._exit_fullscreen).pack(side='right', padx=5)

        # Keep slider in sync with main slider (piggybacking the update loop)
        self._fs_slider_sync_job = None
        self._sync_fs_slider()

        # Mouse-move: show controls, start hide timer
        self._fs_hide_job = None
        self._fs_win.bind('<Motion>', self._fs_on_mouse_move)
        self._fs_video_frame.bind('<Motion>', self._fs_on_mouse_move)

        # Keyboard shortcuts on the fullscreen window
        self._fs_win.bind('<Escape>', lambda e: self._exit_fullscreen())
        self._fs_win.bind('<f>',      lambda e: self._exit_fullscreen())
        self._fs_win.bind('<F>',      lambda e: self._exit_fullscreen())
        self._fs_win.bind('<space>',  lambda e: self.toggle_play())
        self._fs_win.bind('<Right>',  lambda e: self.seek_delta(5000))
        self._fs_win.bind('<Left>',   lambda e: self.seek_delta(-5000))
        self._fs_win.bind('<Up>',     lambda e: self.change_volume(5))
        self._fs_win.bind('<Down>',   lambda e: self.change_volume(-5))
        self._fs_win.bind('<m>',      lambda e: self.toggle_mute())
        self._fs_win.bind('<M>',      lambda e: self.toggle_mute())

        # Start hidden; will show on first mouse move
        self._fs_controls_showing = False

        # Switch VLC output to the fullscreen window
        self.switch_output(self._fs_video_frame.winfo_id())

    def _exit_fullscreen(self):
        if not self.is_fullscreen:
            return
        self.is_fullscreen = False

        # Cancel sync job
        if hasattr(self, '_fs_slider_sync_job') and self._fs_slider_sync_job:
            self.after_cancel(self._fs_slider_sync_job)
            self._fs_slider_sync_job = None

        # Cancel hide timer
        if hasattr(self, '_fs_hide_job') and self._fs_hide_job:
            self.after_cancel(self._fs_hide_job)
            self._fs_hide_job = None

        # Switch output back to main player frame
        self.switch_output(self.video_frame.winfo_id())

        # Destroy fullscreen window
        if hasattr(self, '_fs_win') and self._fs_win:
            self._fs_win.destroy()
            self._fs_win = None

    def _sync_fs_slider(self):
        """Keep the fullscreen progress slider in sync with the main player."""
        if not self.is_fullscreen or not hasattr(self, '_fs_slider'):
            return
        try:
            pos = self.time_slider.get()
            self._fs_slider.set(pos)
            if hasattr(self, '_fs_time_label'):
                self._fs_time_label.configure(text=self.time_label.cget('text'))
            if hasattr(self, '_fs_btn_play'):
                self._fs_btn_play.configure(text='⏸' if self.is_playing else '▶')
        except Exception:
            pass
        self._fs_slider_sync_job = self.after(500, self._sync_fs_slider)

    def _fs_on_mouse_move(self, event):
        self._fs_show_controls()
        self._fs_start_hide_timer()

    def _fs_show_controls(self):
        if not hasattr(self, '_fs_controls_bar'):
            return
        self._fs_controls_bar.place(relx=0, rely=1.0, anchor='sw', relwidth=1)
        self._fs_controls_bar.lift()
        self._fs_controls_showing = True

    def _fs_hide_controls(self):
        if hasattr(self, '_fs_controls_bar'):
            self._fs_controls_bar.place_forget()
        self._fs_controls_showing = False

    def _fs_start_hide_timer(self):
        if hasattr(self, '_fs_hide_job') and self._fs_hide_job:
            self.after_cancel(self._fs_hide_job)
        self._fs_hide_job = self.after(3000, self._fs_hide_controls)

    # ---- Legacy stubs kept so existing references don't break ----
    def on_mouse_move(self, event):
        pass  # fullscreen handled by _fs_on_mouse_move above

    def start_hide_timer(self):
        pass

    def hide_controls(self):
        pass

    def show_controls(self):
        pass



    def show_controls_info(self):
        info_window = ctk.CTkToplevel(self)
        info_window.title("Atajos de Teclado")
        info_window.geometry("300x350")
        info_window.resizable(False, False)
        
        # Centrar sobre la ventana principal
        root = self.winfo_toplevel()
        x = root.winfo_x() + (root.winfo_width() // 2) - 150
        y = root.winfo_y() + (root.winfo_height() // 2) - 175
        info_window.geometry(f"+{x}+{y}")
        
        info_window.transient(root)
        info_window.grab_set()
        
        ctk.CTkLabel(info_window, text="Controles del Reproductor", font=("Segoe UI", 16, "bold")).pack(pady=15)
        
        shortcuts = [
            ("Espacio", "Play / Pausa"),
            ("F", "Pantalla Completa"),
            ("Esc", "Salir / Modo Ventana"),
            ("Flecha Derecha", "Adelantar 5s"),
            ("Flecha Izquierda", "Retroceder 5s"),
            ("Flecha Arriba", "Subir Volumen"),
            ("Flecha Abajo", "Bajar Volumen"),
            ("M", "Silenciar (Mute)")
        ]
        
        frame = ctk.CTkFrame(info_window, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20)
        
        for key, desc in shortcuts:
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(row, text=key, font=("Consolas", 12, "bold"), text_color="#44AAFF").pack(side="left")
            ctk.CTkLabel(row, text=desc, font=("Segoe UI", 12)).pack(side="right")
            
        ctk.CTkButton(info_window, text="Entendido", command=info_window.destroy, width=100).pack(pady=20)
