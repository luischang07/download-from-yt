import customtkinter as ctk
from tkinter import Frame, messagebox
import os
import sys
import vlc

# Robust VLC configuration (same as original)
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
            import vlc as _vlc
            _vlc.Instance().release()
            VLC_AVAILABLE = True
        else:
            print("Aviso: No se encontró la instalación de VLC en rutas estándar.")
    else:
        import vlc as _vlc
        VLC_AVAILABLE = True
except Exception as e:
    print(f"Error inicializando motor de video: {e}")
    VLC_AVAILABLE = False

class MediaPlayerFrame(ctk.CTkFrame):
    """A reusable video player based on VLC and CustomTkinter."""

    def __init__(self, parent, close_callback, fullscreen_callback=None):
        super().__init__(parent)
        self.close_callback = close_callback
        self.fullscreen_callback = fullscreen_callback
        self.instance = None
        self.player = None
        self.is_playing = False
        self.update_timer = None
        self.setup_ui()

    def setup_ui(self):
        # Top bar with back button and title
        self.top_bar = ctk.CTkFrame(self, height=40, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(self.top_bar, text="⬅ Volver", width=80, command=self.stop_and_close).pack(side="left")
        self.title_label = ctk.CTkLabel(self.top_bar, text="Reproductor", font=("Arial", 16, "bold"))
        self.title_label.pack(side="left", padx=20)
        # Video container
        self.video_container = ctk.CTkFrame(self, fg_color="black")
        self.video_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.video_frame = Frame(self.video_container, bg="black")
        self.video_frame.pack(fill="both", expand=True)
        # Controls
        self.controls_frame = ctk.CTkFrame(self, height=100)
        self.controls_frame.pack(fill="x", side="bottom", padx=10, pady=10)
        timeline_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        timeline_frame.pack(fill="x", padx=10, pady=5)
        self.time_slider = ctk.CTkSlider(timeline_frame, from_=0, to=100, command=self.on_seek)
        self.time_slider.set(0)
        self.time_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.time_label = ctk.CTkLabel(timeline_frame, text="00:00 / 00:00", font=("Consolas", 12))
        self.time_label.pack(side="right")
        btn_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        btn_frame.pack(pady=5)
        ctk.CTkButton(btn_frame, text="⏪ -5s", width=60, command=lambda: self.seek_delta(-5000)).pack(side="left", padx=5)
        self.btn_play = ctk.CTkButton(btn_frame, text="⏸", width=60, command=self.toggle_play)
        self.btn_play.pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="+5s ⏩", width=60, command=lambda: self.seek_delta(5000)).pack(side="left", padx=5)
        # Fullscreen button
        ctk.CTkButton(btn_frame, text="⛶", width=40, command=self.toggle_fullscreen).pack(side="left", padx=5)
        ctk.CTkLabel(btn_frame, text="🔊").pack(side="left", padx=(20, 5))
        self.vol_slider = ctk.CTkSlider(btn_frame, from_=0, to=100, width=100, command=self.set_volume)
        self.vol_slider.set(70)
        self.vol_slider.pack(side="left", padx=5)

    def format_ms(self, ms):
        if ms < 0:
            ms = 0
        seconds = int(ms / 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def load_media(self, uri, title="Video"):
        self.title_label.configure(text=title)
        self.time_label.configure(text="00:00 / 00:00")
        # Bind 'f' for fullscreen and mouse events for hover
        self.winfo_toplevel().bind("<f>", self.toggle_fullscreen)
        self.winfo_toplevel().bind("<Escape>", self.exit_fullscreen)
        self.bind("<Motion>", self.on_mouse_move)
        self.video_container.bind("<Motion>", self.on_mouse_move)
        self.video_frame.bind("<Motion>", self.on_mouse_move)
        self.controls_frame.bind("<Motion>", self.on_mouse_move)
        
        if not VLC_AVAILABLE:
            self.show_internal_error()
            return
        try:
            if self.player:
                self.player.stop()
                self.player.release()
            args = [
                '--file-caching=1000',
                '--network-caching=1000',
                '--clock-jitter=0',
                '--clock-synchro=0',
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
        for widget in self.video_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.video_frame, text="⚠️ Error: VLC no encontrado", text_color="white").pack(expand=True)

    def play(self):
        if self.player:
            self.player.play()
            self.is_playing = True
            self.btn_play.configure(text="⏸")

    def toggle_play(self):
        if not self.player:
            return
        if self.player.get_state() == vlc.State.Ended:
            self.player.stop()
            self.player.play()
            self.btn_play.configure(text="⏸")
            self.is_playing = True
            return
        if self.is_playing:
            self.player.pause()
            self.btn_play.configure(text="▶")
            self.is_playing = False
        else:
            self.player.play()
            self.btn_play.configure(text="⏸")
            self.is_playing = True

    def toggle_fullscreen(self, event=None):
        top = self.winfo_toplevel()
        state = top.attributes("-fullscreen")
        new_state = not state
        top.attributes("-fullscreen", new_state)
        
        if self.fullscreen_callback:
            self.fullscreen_callback(new_state)
        
        # Hide/Show other UI elements for "True Fullscreen" feel
        if new_state:
            self.top_bar.pack_forget()
            self.controls_frame.pack_forget()
            self.video_container.pack(fill="both", expand=True, padx=0, pady=0)
        else:
            self.top_bar.pack(fill="x", padx=10, pady=5, side="top")
            self.video_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            self.controls_frame.pack(fill="x", side="bottom", padx=10, pady=10)

    def exit_fullscreen(self, event=None):
        top = self.winfo_toplevel()
        if top.attributes("-fullscreen"):
            self.toggle_fullscreen()

    def on_mouse_move(self, event=None):
        # Show controls on hover
        if self.winfo_toplevel().attributes("-fullscreen"):
            self.controls_frame.pack(fill="x", side="bottom", padx=10, pady=10, in_=self)
            self.controls_frame.lift()
            # Auto-hide after 3 seconds
            if hasattr(self, '_hide_timer'):
                self.after_cancel(self._hide_timer)
            self._hide_timer = self.after(3000, self.hide_controls)

    def hide_controls(self):
        if self.winfo_toplevel().attributes("-fullscreen"):
            self.controls_frame.pack_forget()

    def seek_delta(self, ms):
        if self.player:
            current_time = self.player.get_time()
            new_time = current_time + ms
            if new_time < 0:
                new_time = 0
            self.player.set_time(new_time)

    def stop_and_close(self):
        if self.update_timer:
            self.after_cancel(self.update_timer)
        if self.player:
            self.player.stop()
        # Ensure we exit fullscreen before closing
        if self.winfo_toplevel().attributes("-fullscreen"):
            self.toggle_fullscreen()
        self.close_callback()

    def set_volume(self, value):
        if self.player:
            self.player.audio_set_volume(int(value))

    def on_seek(self, value):
        if self.player:
            if self.player.get_state() == vlc.State.Ended:
                self.player.play()
                self.player.set_position(value / 100)
                self.btn_play.configure(text="⏸")
                self.is_playing = True
            else:
                self.player.set_position(value / 100)

    def update_ui_loop(self):
        if self.player:
            if self.player.get_state() == vlc.State.Ended and self.is_playing:
                self.is_playing = False
                self.btn_play.configure(text="▶")
                self.time_slider.set(100)
            if self.player.is_playing():
                try:
                    pos = self.player.get_position() * 100
                    self.time_slider.set(pos)
                    current_ms = self.player.get_time()
                    total_ms = self.player.get_length()
                    if total_ms > 0:
                        time_str = f"{self.format_ms(current_ms)} / {self.format_ms(total_ms)}"
                        self.time_label.configure(text=time_str)
                except Exception:
                    pass
        self.update_timer = self.after(1000, self.update_ui_loop)
