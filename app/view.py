import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from PIL import Image
from .player_frame import MediaPlayerFrame
import threading
from functools import lru_cache

class DownloaderView(ctk.CTk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.title("YouTube Downloader")
        
        # Centrar ventana al iniciar
        w = 1000
        h = 700
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        self.geometry('%dx%d+%d+%d' % (w, h, x, y))
        
        # Configuración de redimensionamiento mínimo
        self.minsize(800, 600)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.setup_main_layout()
        self.bind("<FocusIn>", self.controller.check_clipboard)
        
        self.active_view = None
        self.animation_running = False

    @lru_cache(maxsize=100)
    def load_cached_image(self, path, width, height):
        try:
            pil_img = Image.open(path)
            pil_img = pil_img.resize((width, height), Image.Resampling.LANCZOS)
            return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(width, height))
        except:
            return None

    def show_toast(self, message, duration=3000):
        """Muestra una notificación flotante en la esquina inferior derecha"""
        toast = ctk.CTkFrame(self, fg_color=("gray20", "gray10"), corner_radius=10, border_width=1, border_color=("gray40", "gray30"))
        
        # Icono y Texto
        ctk.CTkLabel(toast, text="ℹ️", font=("Arial", 20)).pack(side="left", padx=(15, 5), pady=10)
        ctk.CTkLabel(toast, text=message, font=("Segoe UI", 13), text_color="white").pack(side="left", padx=(0, 20), pady=10)
        
        # Posicionar en la esquina inferior derecha (con animación simple de entrada)
        # Usamos place relativo a la ventana principal
        toast.place(relx=0.98, rely=0.95, anchor="se")
        toast.lift() # Asegurar que esté encima de todo
        
        # Auto-destruir después de 'duration' ms
        self.after(duration, toast.destroy)

    def setup_main_layout(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=("gray90", "gray10"))
        self.sidebar.pack(side="left", fill="y")
        
        ctk.CTkLabel(self.sidebar, text="YT Downloader", font=("Arial Black", 18), text_color=("blue", "#44AAFF")).pack(pady=(30, 30))
        
        self.btn_home = self._create_nav_btn("🏠", "Descargar", lambda: self.controller.show_view("home"))
        self.btn_queue = self._create_nav_btn("📋", "Cola", lambda: self.controller.show_view("queue"))
        self.btn_lib = self._create_nav_btn("📂", "Biblioteca", lambda: self.controller.show_view("library"))
        
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(fill="y", expand=True)
        
        self.update_btn = ctk.CTkButton(self.sidebar, text="🔄 Actualizar Motor", width=160, height=30,
                                       fg_color="transparent", border_width=1, 
                                       text_color=("gray10", "gray90"),
                                       font=("Segoe UI", 12),
                                       command=self.controller.update_engine)
        self.update_btn.pack(pady=(0, 10))

        self.theme_btn = ctk.CTkButton(self.sidebar, text="🌗 Tema", width=100, height=30, 
                                      fg_color="transparent", text_color=("black", "white"),
                                      font=("Arial", 14), command=self.toggle_theme)
        self.theme_btn.pack(pady=20)

        # Content Area
        self.content_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_area.pack(side="right", fill="both", expand=True)
        
        self.init_home_view()
        self.init_queue_view()
        self.init_library_view()
        self.init_mini_player() # Inicializar Mini Player antes del Player View
        self.init_player_view()

    def init_mini_player(self):
        self._is_paused = False
        import tkinter as _tk
        _TRANS = '#010203'
        self._pip_trans_key = _TRANS

        self.mini_player_frame = ctk.CTkToplevel(self)
        self.mini_player_frame.title("Mini Player")
        self.mini_player_frame.geometry("320x180")
        self.mini_player_frame.overrideredirect(True)
        self.mini_player_frame.attributes('-topmost', True)
        self.mini_player_frame.withdraw()
        self.mini_player_frame.minsize(160, 90)
        self.mini_player_frame.configure(fg_color="black")

        # Create the separate controls window
        self.mini_controls_window = _tk.Toplevel(self.mini_player_frame)
        self.mini_controls_window.title("Mini Player Controls")
        self.mini_controls_window.overrideredirect(True)
        self.mini_controls_window.attributes('-topmost', True)
        self.mini_controls_window.configure(bg=_TRANS)
        self.mini_controls_window.wm_attributes('-transparentcolor', _TRANS)
        self.mini_controls_window.withdraw()

        # Apply rounded corners via DWM API on Windows
        self.mini_player_frame.update_idletasks()
        self.mini_controls_window.update_idletasks()
        self._round_window_corners(self.mini_player_frame)
        self._round_window_corners(self.mini_controls_window)

        # Bind geometry sync to player window movements
        self.mini_player_frame.bind("<Configure>", self._sync_controls_geometry)

        from tkinter import Frame as TkFrame
        self.mini_video_container = TkFrame(self.mini_player_frame, bg="black")
        self.mini_video_container.pack(fill="both", expand=True)
        
        # ---- Top-right strip on controls window ----
        self.mini_top_strip = _tk.Frame(self.mini_controls_window, bg=_TRANS)

        self.mini_expand_btn = _tk.Label(
            self.mini_top_strip, text="⛶",
            bg=_TRANS, fg="white", font=("Arial", 16), cursor="hand2")
        self.mini_expand_btn.pack(side="left", padx=(5, 2), pady=5)
        self.mini_expand_btn.bind("<Button-1>", lambda e: self.controller.restore_player())

        self.mini_close_btn = _tk.Label(
            self.mini_top_strip, text="✕",
            bg=_TRANS, fg="#ff5555", font=("Arial", 16), cursor="hand2")
        self.mini_close_btn.pack(side="left", padx=(2, 5), pady=5)
        self.mini_close_btn.bind("<Button-1>", lambda e: self.controller.stop_mini_player())

        # ---- Bottom playback controls on controls window ----
        self._pip_back_btn = _tk.Label(
            self.mini_controls_window, text="⏮",
            bg=_TRANS, fg='white', font=('Arial', 22, 'bold'),
            cursor='hand2', bd=0, highlightthickness=0)
        self._pip_back_btn.bind('<Button-1>', lambda e: self.controller.seek_delta(-5000))

        self.mini_playpause_btn = _tk.Label(
            self.mini_controls_window, text='⏸',
            bg=_TRANS, fg='white', font=('Arial', 26, 'bold'),
            cursor='hand2', bd=0, highlightthickness=0)
        self.mini_playpause_btn.bind('<Button-1>', lambda e: self.controller.toggle_play())

        self._pip_fwd_btn = _tk.Label(
            self.mini_controls_window, text='⏭',
            bg=_TRANS, fg='white', font=('Arial', 22, 'bold'),
            cursor='hand2', bd=0, highlightthickness=0)
        self._pip_fwd_btn.bind('<Button-1>', lambda e: self.controller.seek_delta(5000))

        # ---- Progress slider on controls window ----
        self.mini_progress_slider = ctk.CTkSlider(
            self.mini_controls_window,
            from_=0, to=100,
            command=self._on_mini_seek,
            height=14,
            bg_color=_TRANS,
            fg_color="#444444",            # Track color
            progress_color="#ff0000",      # Progress color (red)
            button_color="#ff0000",        # Thumb button color (red)
            button_hover_color="#ff4d4d",
            border_width=0
        )

        # Group for easy show/hide
        self._pip_ctrl_btns = [self._pip_back_btn, self.mini_playpause_btn, self._pip_fwd_btn]

        # Place the control overlays permanently in the controls window
        self.mini_top_strip.place(relx=1.0, rely=0.0, anchor="ne")
        for btn, x_off in zip(self._pip_ctrl_btns, (-52, 0, 52)):
            btn.place(relx=0.5, rely=1.0, anchor="s", x=x_off, y=-10)
        self.mini_progress_slider.place(relx=0.5, rely=1.0, anchor="s", relwidth=0.85, y=-55)

        # Drag on top strip still moves window; hover keeps overlay visible
        self.mini_top_strip.bind("<Button-1>",        self._start_drag)
        self.mini_top_strip.bind("<B1-Motion>",       self._do_drag)
        self.mini_top_strip.bind("<ButtonRelease-1>", lambda e: self._check_screen_bounds())
        self.mini_top_strip.bind("<Enter>",           self._show_mini_overlay)
        self.mini_top_strip.bind("<Leave>",           self._hide_mini_overlay)

        for btn in (self.mini_expand_btn, self.mini_close_btn,
                    self._pip_back_btn, self.mini_playpause_btn, self._pip_fwd_btn,
                    self.mini_progress_slider):
            btn.bind("<Enter>", self._show_mini_overlay)
            btn.bind("<Leave>", self._hide_mini_overlay)

        # Convenience alias
        self.mini_overlay = self.mini_top_strip

        # Eventos de Mouse
        # 1. Click para Pausar/Reproducir (con detección de arrastre)
        self.mini_video_container.bind("<Button-1>", self._start_drag)
        self.mini_video_container.bind("<B1-Motion>", self._do_drag)
        self.mini_video_container.bind("<ButtonRelease-1>", self._on_mini_click)
        
        # 2. Hover para mostrar controles
        self.mini_player_frame.bind("<Enter>", self._show_mini_overlay)
        self.mini_player_frame.bind("<Leave>", self._hide_mini_overlay)
        
        # Bind también al video container para asegurar detección
        self.mini_video_container.bind("<Enter>", self._show_mini_overlay)
        # No bind Leave en container para evitar parpadeo al pasar al overlay
        
        # Bind al overlay para asegurar que no desaparezca si estamos sobre él
        self.mini_overlay.bind("<Enter>", self._show_mini_overlay)
        self.mini_overlay.bind("<Leave>", self._hide_mini_overlay)

        # ---- Resize handles for the borderless PiP window ----
        # Edges first, corners last → corners are lift()-ed last and stay topmost.
        # This ensures a corner drag always fires the corner handler (both axes),
        # not the overlapping edge handler (single axis).
        from tkinter import Frame as TkFrame
        self._resize_edge = None
        E = 6   # edge handle thickness (px)
        C = 10  # corner handle size (px)
        handles_cfg = [
            # Edges first (placed below corners in z-order)
            ('e',  'size_we',    {'relx': 1.0, 'rely': 0.0, 'anchor': 'ne', 'relheight': 1.0, 'width': E}),
            ('w',  'size_we',    {'relx': 0.0, 'rely': 0.0, 'anchor': 'nw', 'relheight': 1.0, 'width': E}),
            ('n',  'size_ns',    {'relx': 0.0, 'rely': 0.0, 'anchor': 'nw', 'relwidth':  1.0, 'height': E}),
            ('s',  'size_ns',    {'relx': 0.0, 'rely': 1.0, 'anchor': 'sw', 'relwidth':  1.0, 'height': E}),
            # Corners last (lifted on top so they take priority over edges)
            ('se', 'size_nw_se', {'relx': 1.0, 'rely': 1.0, 'anchor': 'se', 'width': C, 'height': C}),
            ('sw', 'size_ne_sw', {'relx': 0.0, 'rely': 1.0, 'anchor': 'sw', 'width': C, 'height': C}),
            ('ne', 'size_ne_sw', {'relx': 1.0, 'rely': 0.0, 'anchor': 'ne', 'width': C, 'height': C}),
            ('nw', 'size_nw_se', {'relx': 0.0, 'rely': 0.0, 'anchor': 'nw', 'width': C, 'height': C}),
        ]
        self._resize_handles = []
        for name, cursor, place_cfg in handles_cfg:
            handle = TkFrame(
                self.mini_player_frame,
                bg='black',
                cursor=cursor,
            )
            handle.bind('<Button-1>',        lambda e, n=name: self._resize_start(e, n))
            handle.bind('<B1-Motion>',       self._resize_do)
            handle.bind('<ButtonRelease-1>', self._resize_end)
            self._resize_handles.append((handle, place_cfg))

    def _show_resize_handles(self):
        if hasattr(self, '_resize_handles'):
            for handle, place_cfg in self._resize_handles:
                handle.place(**place_cfg)
                handle.lift()

    def _hide_resize_handles(self):
        if hasattr(self, '_resize_handles'):
            for handle, _ in self._resize_handles:
                handle.place_forget()

    def _on_mini_click(self, event):
        if hasattr(self, '_drag_moved') and self._drag_moved:
            self._drag_moved = False
            self._check_screen_bounds()
            return
        self.controller.toggle_play()

    def _on_mini_seek(self, value):
        if hasattr(self, 'player_frame'):
            self.player_frame.on_seek(value)

    def _on_player_state_change(self, is_playing):
        self._is_paused = not is_playing
        if hasattr(self, 'mini_playpause_btn'):
            self.mini_playpause_btn.configure(text="▶" if self._is_paused else "⏸")
        if self._is_paused:
            self._show_mini_overlay(None)
            if hasattr(self, 'mini_controls_window') and self.mini_controls_window.winfo_exists():
                self.mini_controls_window.lift(self.mini_player_frame)
        else:
            self._hide_mini_overlay(None)

    def _start_drag(self, event):
        # Don't start a move-drag if a resize is in progress
        if getattr(self, '_resize_edge', None):
            return
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        
        # Guardar posición inicial de la ventana (Toplevel)
        self._widget_start_x = self.mini_player_frame.winfo_x()
        self._widget_start_y = self.mini_player_frame.winfo_y()
        self._drag_moved = False

    def _do_drag(self, event):
        if not hasattr(self, '_drag_start_x'): return
        if getattr(self, '_resize_edge', None): return
        
        dx = event.x_root - self._drag_start_x
        dy = event.y_root - self._drag_start_y
        
        # Solo mover si se supera un umbral mínimo para evitar movimientos accidentales al hacer clic
        if abs(dx) > 5 or abs(dy) > 5:
            self._drag_moved = True
            
        if self._drag_moved:
            new_x = self._widget_start_x + dx
            new_y = self._widget_start_y + dy
            # Mover ventana completa usando geometry con coordenadas físicas directamente (CustomTkinter no escala posición)
            self.mini_player_frame.geometry(f"+{int(new_x)}+{int(new_y)}")

    # ---- PiP resize helpers ----
    def _resize_start(self, event, edge):
        self._resize_edge = edge
        self._resize_start_x = event.x_root
        self._resize_start_y = event.y_root
        self._resize_orig_x = self.mini_player_frame.winfo_x()
        self._resize_orig_y = self.mini_player_frame.winfo_y()
        self._resize_orig_w = self.mini_player_frame.winfo_width()
        self._resize_orig_h = self.mini_player_frame.winfo_height()

    def _get_video_aspect_ratio(self):
        if hasattr(self, 'player_frame') and self.player_frame.player:
            try:
                w, h = self.player_frame.player.video_get_size(0)
                if w > 0 and h > 0:
                    return w / h
            except Exception:
                pass
        return 16 / 9  # Fallback to standard 16:9

    def _resize_do(self, event):
        if not self._resize_edge:
            return
        dx = event.x_root - self._resize_start_x
        dy = event.y_root - self._resize_start_y
        edge = self._resize_edge

        x_orig = self._resize_orig_x
        y_orig = self._resize_orig_y
        w_orig = self._resize_orig_w
        h_orig = self._resize_orig_h

        scaling = self.mini_player_frame._get_window_scaling()
        ratio = self._get_video_aspect_ratio()
        sh = self.winfo_screenheight() * scaling
        max_h = sh * 0.9
        max_w = max_h * ratio
        min_w = 320 * scaling  # doubled from 160, converted to physical

        x = x_orig
        y = y_orig
        w = w_orig
        h = h_orig

        if edge == 'e':
            w = max(min_w, min(max_w, w_orig + dx))
            h = w / ratio
        elif edge == 'w':
            w = max(min_w, min(max_w, w_orig - dx))
            x = x_orig + (w_orig - w)
            h = w / ratio
        elif edge == 's':
            h = max(min_w / ratio, min(max_h, h_orig + dy))
            w = h * ratio
        elif edge == 'n':
            h = max(min_w / ratio, min(max_h, h_orig - dy))
            y = y_orig + (h_orig - h)
            w = h * ratio
        elif edge == 'se':
            w = max(min_w, min(max_w, w_orig + dx))
            h = w / ratio
        elif edge == 'sw':
            w = max(min_w, min(max_w, w_orig - dx))
            x = x_orig + (w_orig - w)
            h = w / ratio
        elif edge == 'ne':
            w = max(min_w, min(max_w, w_orig + dx))
            h = w / ratio
            y = (y_orig + h_orig) - h
        elif edge == 'nw':
            w = max(min_w, min(max_w, w_orig - dx))
            x = (x_orig + w_orig) - w
            h = w / ratio
            y = (y_orig + h_orig) - h

        scaling = self.mini_player_frame._get_window_scaling()
        w_log = int(w / scaling)
        h_log = int(h / scaling)
        # Usar coordenadas de posición físicas directamente (CustomTkinter geometry no escala la posición)
        self.mini_player_frame.geometry(f"{w_log}x{h_log}+{int(x)}+{int(y)}")

    def _resize_end(self, event):
        self._resize_edge = None
        self._check_screen_bounds()

    def _check_screen_bounds(self):
        # Force pending window manager updates to ensure we have the absolute latest positions
        self.mini_player_frame.update_idletasks()
        w = self.mini_player_frame.winfo_width()
        h = self.mini_player_frame.winfo_height()
        x = self.mini_player_frame.winfo_x()
        y = self.mini_player_frame.winfo_y()

        scaling = self.mini_player_frame._get_window_scaling()
        
        # winfo_screenwidth/height return logical pixels, so multiply by scaling to get physical screen size
        sw = self.winfo_screenwidth() * scaling
        sh = self.winfo_screenheight() * scaling

        adjusted = False
        pull_back = 30 * scaling  # Pull back to leave 30px (logical) visible on screen

        # Check if less than 30px is visible on left
        if x + w < pull_back:
            x = pull_back - w
            adjusted = True
        # Check if less than 30px is visible on right
        elif x > sw - pull_back:
            x = sw - pull_back
            adjusted = True

        # Check if less than 30px is visible on top
        if y + h < pull_back:
            y = pull_back - h
            adjusted = True
        # Check if less than 30px is visible on bottom
        elif y > sh - pull_back:
            y = sh - pull_back
            adjusted = True

        if adjusted:
            # Mover de vuelta usando coordenadas de posición físicas directamente
            self.mini_player_frame.geometry(f"+{int(x)}+{int(y)}")
            self._sync_controls_geometry()

    def _show_mini_overlay(self, event):
        if hasattr(self, '_hide_overlay_job') and self._hide_overlay_job:
            self.after_cancel(self._hide_overlay_job)
            self._hide_overlay_job = None

        self._show_resize_handles()

        if hasattr(self, 'mini_controls_window') and self.mini_controls_window.winfo_exists():
            if self.mini_controls_window.state() == "withdrawn":
                self.mini_controls_window.deiconify()
                self._sync_controls_geometry()
            self.mini_controls_window.lift(self.mini_player_frame)

    def _hide_mini_overlay(self, event):
        # Si está pausado, NO ocultar los controles
        if getattr(self, '_is_paused', False):
            return

        # Usar un pequeño retraso para evitar parpadeos si el mouse sale y entra rápidamente
        self._hide_overlay_job = self.after(100, self._check_hide_overlay)

    def _check_hide_overlay(self):
        try:
            x, y = self.mini_player_frame.winfo_pointerxy()
            wx = self.mini_player_frame.winfo_rootx()
            wy = self.mini_player_frame.winfo_rooty()
            w  = self.mini_player_frame.winfo_width()
            h  = self.mini_player_frame.winfo_height()
            if not (wx <= x <= wx + w and wy <= y <= wy + h):
                self._hide_resize_handles()
                if hasattr(self, 'mini_controls_window') and self.mini_controls_window.winfo_exists():
                    self.mini_controls_window.withdraw()
        except Exception:
            pass

    def _sync_controls_geometry(self, event=None):
        if hasattr(self, 'mini_controls_window') and self.mini_controls_window.winfo_exists():
            if self.mini_player_frame.state() == "normal":
                w = self.mini_player_frame.winfo_width()
                h = self.mini_player_frame.winfo_height()
                x = self.mini_player_frame.winfo_x()
                y = self.mini_player_frame.winfo_y()
                self.mini_controls_window.geometry(f"{w}x{h}+{x}+{y}")

    def show_mini_player(self):
        # Mostrar ventana Toplevel del reproductor
        self.mini_player_frame.deiconify()
        
        # Posicionar inicialmente en la esquina inferior derecha de la pantalla si no tiene posición
        # O usar la última posición conocida
        if not hasattr(self, '_mini_pos_set'):
            scaling = self.mini_player_frame._get_window_scaling()
            sw_log = self.winfo_screenwidth()
            sh_log = self.winfo_screenheight()
            
            # Convert screen size to physical pixels
            sw_phys = sw_log * scaling
            sh_phys = sh_log * scaling
            
            ratio = self._get_video_aspect_ratio()
            w_log = 320
            h_log = int(w_log / ratio)
            
            # Compute window physical size
            w_phys = w_log * scaling
            h_phys = h_log * scaling
            
            # Position at bottom-right in physical coordinates
            x_phys = sw_phys - w_phys - 20 * scaling
            y_phys = sh_phys - h_phys - 60 * scaling
            
            self.mini_player_frame.geometry(f"{w_log}x{h_log}+{int(x_phys)}+{int(y_phys)}")
            self._mini_pos_set = True

        self.mini_player_frame.update_idletasks()
        
        if getattr(self, '_is_paused', False):
            self.mini_controls_window.deiconify()
            self._sync_controls_geometry()
            self.mini_controls_window.lift(self.mini_player_frame)
            self._show_resize_handles()
        else:
            self.mini_controls_window.withdraw()
            self._hide_resize_handles()

        self.mini_player_frame.lift()
        self._round_window_corners(self.mini_player_frame)
        if hasattr(self, 'mini_controls_window') and self.mini_controls_window.winfo_exists():
            self._round_window_corners(self.mini_controls_window)

    def _round_window_corners(self, window):
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(window.winfo_id()) or window.winfo_id()
            if hwnd:
                DWMWA_WINDOW_CORNER_PREFERENCE = 33
                DWMWCP_ROUND = 2
                val = ctypes.c_int(DWMWCP_ROUND)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    ctypes.c_void_p(hwnd),
                    ctypes.c_uint(DWMWA_WINDOW_CORNER_PREFERENCE),
                    ctypes.byref(val),
                    ctypes.sizeof(val)
                )
        except Exception:
            pass

    def hide_mini_player(self):
        self.mini_player_frame.withdraw()
        if hasattr(self, 'mini_controls_window') and self.mini_controls_window.winfo_exists():
            self.mini_controls_window.withdraw()

    def _create_nav_btn(self, icon, text, cmd):
        btn = ctk.CTkButton(self.sidebar, text=f"  {icon}   {text}", width=180, height=45, 
                           corner_radius=8, fg_color="transparent", anchor="w",
                           text_color=("gray40", "gray60"), font=("Segoe UI", 14, "bold"),
                           hover_color=("gray80", "gray20"), command=cmd)
        btn.pack(pady=5, padx=10)
        return btn

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "Light" if current == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)

    def init_home_view(self):
        self.home_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        
        # Scrollable wrapper so content doesn't get clipped when the window is small
        self._home_scroll = ctk.CTkScrollableFrame(self.home_frame, fg_color="transparent")
        self._home_scroll.pack(fill="both", expand=True, padx=0, pady=0)

        center_box = ctk.CTkFrame(self._home_scroll, fg_color="transparent")
        center_box.pack(fill="x", expand=True, pady=(60, 20), padx=80)
        
        ctk.CTkLabel(center_box, text="Descargar Video", font=("Segoe UI", 32, "bold"), text_color=("black", "white")).pack(pady=(0, 20))
        
        input_row = ctk.CTkFrame(center_box, fg_color="transparent")
        input_row.pack(fill="x", pady=10)
        
        self.url_entry = ctk.CTkEntry(input_row, height=50, placeholder_text="Pega el enlace de YouTube aquí...", 
                                    font=("Segoe UI", 14), border_width=0, corner_radius=25, fg_color=("white", "gray20"), text_color=("black", "white"))
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.fetch_button = ctk.CTkButton(input_row, text="🔍", width=50, height=50, corner_radius=25, 
                                        font=("Arial", 20), fg_color=("blue", "#44AAFF"), text_color="white",
                                        command=self.controller.fetch_formats)
        self.fetch_button.pack(side="left")

        self.results_card = ctk.CTkFrame(center_box, fg_color=("white", "gray15"), corner_radius=15)
        
        self.thumbnail_lbl = ctk.CTkLabel(self.results_card, text="", width=320, height=180)
        self.thumbnail_lbl.pack(pady=(20, 5), padx=20)
        
        self.preview_btn = ctk.CTkButton(self.results_card, text="▶ Previsualizar Video", width=160, height=30,
                                        fg_color="transparent", border_width=1, border_color=("gray50", "gray40"),
                                        text_color=("black", "white"), hover_color=("gray80", "gray20"),
                                        command=self.controller.play_preview)
        self.preview_btn.pack(pady=(0, 10))

        self.video_title_lbl = ctk.CTkLabel(self.results_card, text="Título del Video", font=("Segoe UI", 16, "bold"), text_color=("black", "white"), wraplength=600)
        self.video_title_lbl.pack(pady=(0, 10), padx=20)
        
        opts_row = ctk.CTkFrame(self.results_card, fg_color="transparent")
        opts_row.pack(pady=10)
        
        self.type_selector = ctk.CTkSegmentedButton(opts_row, values=["Video", "Audio"], command=self.controller.on_type_change, text_color=("black", "white"))
        self.type_selector.set("Video")
        self.type_selector.pack(side="left", padx=10)
        
        self.quality_combo = ctk.CTkOptionMenu(opts_row, values=["Calidad"], width=150, text_color=("black", "white"))
        self.quality_combo.pack(side="left", padx=10)
        
        self.filename_entry = ctk.CTkEntry(self.results_card, placeholder_text="Nombre del archivo", text_color=("black", "white"))
        self.filename_entry.pack(pady=10, padx=20, fill="x")
        
        self.download_button = ctk.CTkButton(self.results_card, text="Descargar Ahora", height=40, width=200, 
                                            font=("Segoe UI", 14, "bold"), fg_color=("green", "#00FF00"), text_color="white",
                                            command=self.controller.start_download)
        self.download_button.pack(pady=(20, 5))

        self.queue_add_btn = ctk.CTkButton(self.results_card, text="+ Agregar a Cola", width=200, height=30,
                                         fg_color="transparent", border_width=1, text_color=("black", "white"),
                                         command=self.controller.add_to_queue)
        self.queue_add_btn.pack(pady=(0, 20))
        
        self.path_frame = ctk.CTkFrame(self._home_scroll, fg_color=("gray90", "gray15"), corner_radius=10)
        self.path_frame.pack(fill="x", padx=40, pady=20)
        
        ctk.CTkLabel(self.path_frame, text="Guardar en:", font=("Segoe UI", 12, "bold"), text_color=("gray40", "gray60")).pack(side="left", padx=(15, 5), pady=10)
        
        self.path_label = ctk.CTkLabel(self.path_frame, text="", font=("Segoe UI", 12), text_color=("black", "white"))
        self.path_label.pack(side="left", pady=10)
        
        ctk.CTkButton(self.path_frame, text="Cambiar Carpeta", width=100, height=25, 
                    fg_color=("blue", "#44AAFF"), text_color="white", font=("Segoe UI", 11, "bold"),
                    command=self.controller.browse_folder).pack(side="right", padx=15, pady=10)

        self.progress_container = ctk.CTkFrame(self.results_card, fg_color=("white", "gray10"), corner_radius=15, border_width=1, border_color=("gray80", "gray30"))
        
        self.progress_percent_lbl = ctk.CTkLabel(self.progress_container, text="0%", font=("Arial Black", 32), text_color=("blue", "#44AAFF"))
        self.progress_percent_lbl.pack(pady=(20, 5))
        
        self.progress_status_lbl = ctk.CTkLabel(self.progress_container, text="Iniciando...", font=("Segoe UI", 12), text_color="gray")
        self.progress_status_lbl.pack(pady=(0, 10))
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_container, height=10, width=400, corner_radius=5, progress_color=("blue", "#44AAFF"))
        self.progress_bar.pack(pady=(0, 10), padx=30)
        self.progress_bar.set(0)

        self.completion_label = ctk.CTkLabel(self.progress_container, text="", font=("Segoe UI", 14, "bold"), text_color=("green", "#00FF00"))
        self.completion_label.pack(pady=(0, 20))

    def init_queue_view(self):
        self.queue_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        
        # Header
        header = ctk.CTkFrame(self.queue_frame, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=30)
        ctk.CTkLabel(header, text="Cola de Descargas", font=("Segoe UI", 24, "bold"), text_color=("black", "white")).pack(side="left")
        
        self.btn_start_queue = ctk.CTkButton(header, text="▶ Iniciar Cola", width=150, height=40, 
                                           fg_color=("green", "#2CC985"), text_color="white", font=("Arial", 14, "bold"),
                                           command=self.controller.start_queue)
        self.btn_start_queue.pack(side="right")

        # Scrollable List
        self.queue_scroll = ctk.CTkScrollableFrame(self.queue_frame, fg_color="transparent")
        self.queue_scroll.pack(fill="both", expand=True, padx=40, pady=(0, 40))

    def add_queue_item_widget(self, item_data, index):
        row = ctk.CTkFrame(self.queue_scroll, fg_color=("white", "gray15"), corner_radius=10)
        row.pack(fill="x", pady=5)
        
        # Thumbnail
        thumb_lbl = ctk.CTkLabel(row, text="", width=80, height=45)
        thumb_lbl.pack(side="left", padx=10, pady=5)
        
        if item_data.get('thumbnail_url'):
            # We might need to load this image. For now, just placeholder or if we have the image object.
            # The controller should probably pass the image object if available, or we load it here.
            # Since we don't want to block, we'll just show an icon for now or load it async if we had the mechanism.
            # But wait, the model has `load_thumbnail_image`.
            # For simplicity, let's just show an icon or text.
            thumb_lbl.configure(text="🎬" if item_data['mode'] == "Video" else "🎵", font=("Arial", 20))
        else:
            thumb_lbl.configure(text="🎬" if item_data['mode'] == "Video" else "🎵", font=("Arial", 20))

        # Info
        info_box = ctk.CTkFrame(row, fg_color="transparent")
        info_box.pack(side="left", fill="x", expand=True, padx=10)
        
        title = item_data['title']
        ctk.CTkLabel(info_box, text=title[:40] + "..." if len(title)>40 else title, 
                    font=("Segoe UI", 14, "bold"), anchor="w", text_color=("black", "white")).pack(fill="x")
        
        details = f"{item_data['mode']} | {item_data['format_data']['label']}"
        ctk.CTkLabel(info_box, text=details, font=("Segoe UI", 11), text_color="gray", anchor="w").pack(fill="x")

        # Status & Progress
        status_box = ctk.CTkFrame(row, fg_color="transparent", width=150)
        status_box.pack(side="right", padx=15)
        
        status_lbl = ctk.CTkLabel(status_box, text="Pendiente", font=("Segoe UI", 12), text_color="gray")
        status_lbl.pack(anchor="e")
        
        progress_bar = ctk.CTkProgressBar(status_box, width=100, height=8, progress_color=("blue", "#44AAFF"))
        progress_bar.pack(pady=5)
        progress_bar.set(0)
        
        # Store references to update later
        row.status_lbl = status_lbl
        row.progress_bar = progress_bar
        
        # We can store the widget in a list in the view to access it by index
        if not hasattr(self, 'queue_widgets'):
            self.queue_widgets = []
        self.queue_widgets.append(row)

    def update_queue_item_status(self, index, status, progress=0):
        if not hasattr(self, 'queue_widgets') or index >= len(self.queue_widgets): return
        
        widget = self.queue_widgets[index]
        
        if status == "downloading":
            widget.status_lbl.configure(text=f"Descargando {int(progress*100)}%", text_color=("blue", "#44AAFF"))
            widget.progress_bar.set(progress)
        elif status == "completed":
            widget.status_lbl.configure(text="Completado", text_color=("green", "#00FF00"))
            widget.progress_bar.set(1)
        elif status == "error":
            widget.status_lbl.configure(text="Error", text_color="red")
            widget.progress_bar.set(0)
        elif status == "pending":
            widget.status_lbl.configure(text="Pendiente", text_color="gray")
            widget.progress_bar.set(0)

    def init_library_view(self):
        self.library_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        
        header = ctk.CTkFrame(self.library_frame, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=30)
        
        ctk.CTkLabel(header, text="Mi Biblioteca", font=("Segoe UI", 24, "bold"), text_color=("black", "white")).pack(side="left")
        
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.controller.filter_library)
        search_entry = ctk.CTkEntry(header, textvariable=self.search_var, placeholder_text="Filtrar...", width=200, text_color=("black", "white"))
        search_entry.pack(side="right")
        
        ctk.CTkButton(header, text="↻", width=40, command=lambda: self.controller.show_view("library"), text_color="white").pack(side="right", padx=10)

        # --- NUEVO: Selector de Carpeta en Biblioteca ---
        path_frame = ctk.CTkFrame(self.library_frame, fg_color=("gray90", "gray15"), corner_radius=10, height=40)
        path_frame.pack(fill="x", padx=40, pady=(0, 20))
        
        ctk.CTkLabel(path_frame, text="Carpeta:", font=("Segoe UI", 12, "bold"), text_color=("gray40", "gray60")).pack(side="left", padx=(15, 5), pady=5)
        
        self.lib_path_label = ctk.CTkLabel(path_frame, text="", font=("Segoe UI", 12), text_color=("black", "white"))
        self.lib_path_label.pack(side="left", pady=5)
        
        ctk.CTkButton(path_frame, text="Cambiar", width=80, height=25, 
                    fg_color=("blue", "#44AAFF"), text_color="white", font=("Segoe UI", 11, "bold"),
                    command=self.controller.browse_folder).pack(side="right", padx=15, pady=5)
        # ------------------------------------------------

        self.lib_scroll = ctk.CTkScrollableFrame(self.library_frame, fg_color="transparent")
        self.lib_scroll.pack(fill="both", expand=True, padx=40, pady=(0, 40))

    def update_path_labels(self, path):
        name = os.path.basename(path)
        if hasattr(self, 'path_label'):
            self.path_label.configure(text=name)
        if hasattr(self, 'lib_path_label'):
            self.lib_path_label.configure(text=name)

    def init_player_view(self):
        self.player_frame = MediaPlayerFrame(self.content_area, close_callback=lambda: self.controller.show_view("last"))
        self.player_frame.set_state_callback(self._on_player_state_change)
        # Vincular UI del Mini Player
        if hasattr(self, 'mini_video_container'):
            self.player_frame.set_mini_ui(None, self.mini_progress_slider, self.mini_playpause_btn)

    def show_view(self, view_name):
        views = {
            "home": self.home_frame,
            "queue": self.queue_frame,
            "library": self.library_frame,
            "player": self.player_frame
        }
        
        next_frame = views.get(view_name)
        if not next_frame: return
        
        if self.active_view == next_frame:
            return

        # Cambio instantáneo pero fluido usando place (evita el parpadeo de pack)
        next_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        next_frame.lift()
        
        if self.active_view and self.active_view != next_frame:
            self.active_view.place_forget()
            
        self.active_view = next_frame
        self._update_nav_state(view_name)

    def _update_nav_state(self, view_name):
        # Reset
        self.btn_home.configure(text_color=("gray40", "gray60"), fg_color="transparent")
        self.btn_queue.configure(text_color=("gray40", "gray60"), fg_color="transparent")
        self.btn_lib.configure(text_color=("gray40", "gray60"), fg_color="transparent")
        
        if view_name == "home":
            self.btn_home.configure(text_color=("blue", "#44AAFF"), fg_color=("gray85", "gray15"))
        elif view_name == "queue":
            self.btn_queue.configure(text_color=("blue", "#44AAFF"), fg_color=("gray85", "gray15"))
        elif view_name == "library":
            self.btn_lib.configure(text_color=("blue", "#44AAFF"), fg_color=("gray85", "gray15"))

    def update_formats_ui(self, labels, title, thumbnail_img=None):
        self.video_title_lbl.configure(text=title[:50] + "..." if len(title)>50 else title)
        
        safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_', '.')]).strip()
        self.filename_entry.delete(0, "end")
        self.filename_entry.insert(0, safe_title)
        
        self.quality_combo.configure(values=labels)
        if labels: self.quality_combo.set(labels[0])
        
        if thumbnail_img:
            base_width = 320
            w_percent = (base_width / float(thumbnail_img.size[0]))
            h_size = int((float(thumbnail_img.size[1]) * float(w_percent)))
            pil_image = thumbnail_img.resize((base_width, h_size), Image.Resampling.LANCZOS)
            ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(base_width, h_size))
            self.thumbnail_lbl.configure(image=ctk_image, text="")
        else:
            self.thumbnail_lbl.configure(image=None, text="[Sin Imagen]")

        self.results_card.pack(pady=20, fill="x")

    def render_library(self, files):
        for w in self.lib_scroll.winfo_children(): w.destroy()
        
        def load_item_image(label, path):
            base_path = os.path.splitext(path)[0]
            thumb_path = None
            for ext in ['.jpg', '.webp', '.png']:
                if os.path.exists(base_path + ext):
                    thumb_path = base_path + ext
                    break
            
            if thumb_path:
                img = self.load_cached_image(thumb_path, 80, 45)
                if img:
                    self.after(0, lambda: label.configure(image=img, text=""))

        for item in files:
            row = ctk.CTkFrame(self.lib_scroll, fg_color=("white", "gray15"), corner_radius=10)
            row.pack(fill="x", pady=5)
            
            # Placeholder inicial
            thumb_lbl = ctk.CTkLabel(row, text="⏳", width=80, height=45, fg_color=("gray90", "gray20"), corner_radius=5)
            thumb_lbl.pack(side="left", padx=10, pady=5)
            
            # Cargar imagen en hilo separado
            threading.Thread(target=load_item_image, args=(thumb_lbl, item['path']), daemon=True).start()
            
            info_box = ctk.CTkFrame(row, fg_color="transparent")
            info_box.pack(side="left", fill="x", expand=True)
            
            ctk.CTkLabel(info_box, text=item['name'], font=("Segoe UI", 14, "bold"), anchor="w", text_color=("black", "white")).pack(fill="x")
            ctk.CTkLabel(info_box, text=item['type'], font=("Segoe UI", 11), text_color="gray", anchor="w").pack(fill="x")
            
            ctk.CTkButton(row, text="▶ Reproducir", width=100, fg_color=("blue", "#44AAFF"), text_color="white",
                         command=lambda p=item['path'], n=item['name']: self.controller.open_player(p, n)).pack(side="right", padx=15)

    def setup_sidebar(self):
        # --- EXISTENTE: Marco de la barra lateral ---
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=("gray90", "gray10"))
        self.sidebar_frame.pack(side="left", fill="y")
        
        # --- EXISTENTE: Título ---
        ctk.CTkLabel(self.sidebar_frame, text="YT Downloader", font=("Arial Black", 18), text_color=("blue", "#44AAFF")).pack(pady=(30, 10))
        
        # --- EXISTENTE: Botones de navegación ---
        self.home_btn = self._create_sidebar_btn("🏠", "Inicio", lambda: self.controller.show_view("home"))
        self.queue_btn = self._create_sidebar_btn("📥", "Cola", lambda: self.controller.show_view("queue"))
        self.library_btn = self._create_sidebar_btn("📚", "Biblioteca", lambda: self.controller.show_view("library"))
        
        # Botones de navegación existentes...
        self.library_btn.pack(pady=10, padx=20, fill="x")

        # --- NUEVO: Espaciador para empujar el botón al fondo ---
        spacer = ctk.CTkLabel(self.sidebar_frame, text="", height=10)
        spacer.pack(expand=True, fill="y")
        
        # --- NUEVO: Botón de Actualizar Motor ---
        self.update_btn = ctk.CTkButton(self.sidebar_frame, text="🔄 Actualizar Motor", 
                                       font=("Segoe UI", 12),
                                       fg_color="transparent", border_width=1, 
                                       text_color=("gray10", "gray90"),
                                       command=self.controller.update_engine)
        self.update_btn.pack(pady=(0, 20), padx=20, fill="x", side="bottom")
        
        # El botón de tema ya estaba ahí, asegúrate de que quede bien posicionado
        self.theme_btn = ctk.CTkButton(self.sidebar_frame, text="🌗 Tema", width=100, height=30, 
                                      fg_color="transparent", text_color=("black", "white"),
                                      font=("Arial", 14), command=self.toggle_theme)
        self.theme_btn.pack(pady=20, padx=20, fill="x", side="bottom")

    def load_library_items(self, items):
        # 1. Limpiar UI
        for widget in self.library_scroll.winfo_children(): widget.destroy()

        # 2. Cargar estructura básica (Rápido)
        for item in items:
            card = self.create_card_skeleton(item) # Crea la tarjeta con imagen gris
            card.pack()
            
            # 3. Lanzar hilo para cargar la imagen de esta tarjeta
            threading.Thread(target=self.load_image_async, args=(card, item['image_path']), daemon=True).start()

    def load_image_async(self, card_widget, image_path):
        # Esto ocurre en segundo plano sin congelar la app
        my_image = self.process_image(image_path) 
        # Actualizar la UI en el hilo principal
        self.after(0, lambda: card_widget.set_image(my_image))

    from functools import lru_cache

    @lru_cache(maxsize=100) # Guarda las últimas 100 imágenes en RAM
    def load_and_resize_image(path, width, height):
        # Tu código actual de PIL Image.open...
        return ctk_image
