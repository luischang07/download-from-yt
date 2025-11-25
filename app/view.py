import os
import customtkinter as ctk
from tkinter import filedialog, messagebox, Frame

class DownloaderView(ctk.CTk):
    """UI layer of the application. All widgets are created here.
    The controller will assign callback functions to the public attributes.
    """

    def __init__(self):
        super().__init__()
        self.title("YouTube Downloader & Library")
        self.geometry("900x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Callbacks (to be set by controller)
        self.on_fetch = None          # (url, mode) -> None
        self.on_download = None       # (url, format_label, mode, path) -> None
        self.on_open_player = None    # (uri, title) -> None
        self.on_type_change = None    # (mode) -> None
        self.on_browse_folder = None  # () -> None
        self.on_cancel_search = None  # () -> None

        # Default download folder
        self.download_path = os.path.join(os.path.expanduser("~"), "Downloads")

        # Center the window on screen
        self.center_window()

        self.setup_main_layout()

    # ---------------------------------------------------------------------
    # Helper methods
    # ---------------------------------------------------------------------
    def center_window(self, width=900, height=700):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def set_fullscreen(self, fullscreen: bool):
        if fullscreen:
            self.sidebar.pack_forget()
        else:
            self.sidebar.pack(side="left", fill="y", before=self.content_area)

    # ---------------------------------------------------------------------
    # UI Construction
    # ---------------------------------------------------------------------
    def setup_main_layout(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        ctk.CTkLabel(self.sidebar, text="YT Downloader", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20, padx=10)
        self.btn_home = ctk.CTkButton(self.sidebar, text="🏠 Descargar", command=lambda: self.show_view("home"))
        self.btn_home.pack(pady=10, padx=20, fill="x")
        self.btn_lib = ctk.CTkButton(self.sidebar, text="📂 Biblioteca", command=lambda: self.show_view("library"))
        self.btn_lib.pack(pady=10, padx=20, fill="x")

        # Content area
        self.content_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_area.pack(side="right", fill="both", expand=True)

        # Sub‑views
        self.init_home_view()
        self.init_library_view()
        self.init_player_view()
        self.show_view("home")

    # ---------------------------------------------------------------------
    # Home view
    # ---------------------------------------------------------------------
    def init_home_view(self):
        self.home_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        # URL input
        url_frame = ctk.CTkFrame(self.home_frame, fg_color="transparent")
        url_frame.pack(pady=(20, 10))
        ctk.CTkLabel(url_frame, text="URL del video:").pack(anchor="w")
        input_box = ctk.CTkFrame(url_frame, fg_color="transparent")
        input_box.pack(pady=5)
        self.url_entry = ctk.CTkEntry(input_box, width=400, placeholder_text="https://youtube.com/…")
        self.url_entry.pack(side="left", padx=(0, 5))
        ctk.CTkButton(input_box, text="✖", width=30, fg_color="gray", command=lambda: self.url_entry.delete(0, "end")).pack(side="left")
        # Options
        opts_frame = ctk.CTkFrame(self.home_frame)
        opts_frame.pack(pady=20, padx=20, fill="x")
        self.type_selector = ctk.CTkSegmentedButton(opts_frame, values=["Video", "Audio"], command=self._type_changed)
        self.type_selector.set("Video")
        self.type_selector.pack(pady=10)
        # Search row
        search_row = ctk.CTkFrame(opts_frame, fg_color="transparent")
        search_row.pack(pady=5)
        self.fetch_button = ctk.CTkButton(search_row, text="🔍 Buscar Calidades", command=self._fetch_clicked)
        self.fetch_button.pack(side="left", padx=5)
        self.cancel_button = ctk.CTkButton(search_row, text="❌ Cancelar", fg_color="red", state="disabled", width=80, command=self._cancel_clicked)
        self.cancel_button.pack(side="left", padx=5)
        # Results combo
        results_frame = ctk.CTkFrame(opts_frame, fg_color="transparent")
        results_frame.pack(pady=10)
        self.quality_combo = ctk.CTkComboBox(results_frame, width=350, state="disabled", values=["Primero busca el video"])
        self.quality_combo.pack(side="left", padx=5)
        # Path selection (default to Downloads)
        path_frame = ctk.CTkFrame(self.home_frame, fg_color="transparent")
        path_frame.pack(pady=10)
        self.path_entry = ctk.CTkEntry(path_frame, width=300)
        self.path_entry.insert(0, self.download_path)
        self.path_entry.pack(side="left", padx=5)
        ctk.CTkButton(path_frame, text="Explorar", width=80, command=self._browse_clicked).pack(side="left")
        # Progress & status
        self.progress_bar = ctk.CTkProgressBar(self.home_frame, width=400)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        self.status_label = ctk.CTkLabel(self.home_frame, text="Listo", text_color="gray")
        self.status_label.pack()
        self.download_button = ctk.CTkButton(self.home_frame, text="⬇ Descargar", height=40, font=("Arial", 16, "bold"), command=self._download_clicked)
        self.download_button.pack(pady=20)

    # ---------------------------------------------------------------------
    # Library view
    # ---------------------------------------------------------------------
    def init_library_view(self):
        self.library_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        top_bar = ctk.CTkFrame(self.library_frame)
        top_bar.pack(fill="x", padx=10, pady=10)
        self.search_var = ctk.StringVar()
        ctk.CTkEntry(top_bar, textvariable=self.search_var, placeholder_text="Buscar archivo...").pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkButton(top_bar, text="🔄", width=40, command=self._reload_library).pack(side="right", padx=10)
        self.lib_tabs = ctk.CTkTabview(self.library_frame)
        self.lib_tabs.pack(fill="both", expand=True, padx=10, pady=5)
        for name in ["Todos", "Video", "Audio"]:
            self.lib_tabs.add(name)
        self.scroll_frames = {name: ctk.CTkScrollableFrame(self.lib_tabs.tab(name)) for name in ["Todos", "Video", "Audio"]}
        for f in self.scroll_frames.values():
            f.pack(fill="both", expand=True)

    def _load_library(self):
        # Clear existing items
        for frame in self.scroll_frames.values():
            for widget in frame.winfo_children():
                widget.destroy()
        # Scan download folder
        if not os.path.isdir(self.download_path):
            return
        exts = {
            "Video": [".mp4", ".mkv", ".webm", ".avi"],
            "Audio": [".mp3", ".m4a", ".wav", ".flac"]
        }
        all_files = []
        for f in os.listdir(self.download_path):
            fp = os.path.join(self.download_path, f)
            if not os.path.isfile(fp):
                continue
            ext = os.path.splitext(f)[1].lower()
            ftype = None
            for k, v in exts.items():
                if ext in v:
                    ftype = k
                    break
            if ftype:
                all_files.append({"name": f, "path": fp, "type": ftype})
        # Populate tabs
        for item in all_files:
            self._add_lib_item(self.scroll_frames["Todos"], item)
            self._add_lib_item(self.scroll_frames[item["type"]], item)

    def _add_lib_item(self, parent, item):
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", pady=2)
        icon = "📺" if item["type"] == "Video" else "🎵"
        ctk.CTkLabel(row, text=f"{icon} {item['name']}", anchor="w").pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkButton(row, text="▶", width=40, fg_color="green", command=lambda: self._open_player_from_lib(item)).pack(side="right", padx=5)

    def _open_player_from_lib(self, item):
        self.last_view = "library"
        self.on_open_player(item["path"], item["name"])

    def _reload_library(self):
        self._load_library()

    # ---------------------------------------------------------------------
    # Player view – wrapper around MediaPlayerFrame
    # ---------------------------------------------------------------------
    def init_player_view(self):
        from .player_frame import MediaPlayerFrame
        self.player_frame = MediaPlayerFrame(
            self.content_area, 
            close_callback=lambda: self.show_view("last"),
            fullscreen_callback=self.set_fullscreen
        )

    # ---------------------------------------------------------------------
    # View switching helpers
    # ---------------------------------------------------------------------
    def show_view(self, view_name: str):
        self.home_frame.pack_forget()
        self.library_frame.pack_forget()
        self.player_frame.pack_forget()
        self.btn_home.configure(fg_color="transparent", border_width=0)
        self.btn_lib.configure(fg_color="transparent", border_width=0)
        if view_name == "last":
            view_name = getattr(self, "last_view", "home")
        if view_name == "home":
            self.home_frame.pack(fill="both", expand=True)
            self.btn_home.configure(fg_color=("gray75", "gray25"))
            self.last_view = "home"
        elif view_name == "library":
            self.library_frame.pack(fill="both", expand=True)
            self.btn_lib.configure(fg_color=("gray75", "gray25"))
            self._load_library()
            self.last_view = "library"
        elif view_name == "player":
            self.player_frame.pack(fill="both", expand=True)
            self.last_view = "player"

    # ---------------------------------------------------------------------
    # UI event wrappers – delegate to controller callbacks
    # ---------------------------------------------------------------------
    def _type_changed(self, value):
        self.quality_combo.set("Primero busca el video")
        self.quality_combo.configure(state="disabled", values=["Primero busca el video"])
        if self.on_type_change:
            self.on_type_change(value)

    def _fetch_clicked(self):
        if self.on_fetch:
            self.on_fetch(self.url_entry.get().strip(), self.type_selector.get())

    def _cancel_clicked(self):
        if self.on_cancel_search:
            self.on_cancel_search()

    def _browse_clicked(self):
        if self.on_browse_folder:
            self.on_browse_folder()

    def _download_clicked(self):
        if self.on_download:
            url = self.url_entry.get().strip()
            fmt_label = self.quality_combo.get()
            mode = self.type_selector.get()
            path = self.path_entry.get().strip()
            self.on_download(url, fmt_label, mode, path)

    # ---------------------------------------------------------------------
    # Helper methods used by controller to update UI state
    # ---------------------------------------------------------------------
    def set_status(self, text: str, color: str = "gray"):
        self.status_label.configure(text=text, text_color=color)

    def set_progress(self, fraction: float):
        self.progress_bar.set(fraction)

    def enable_fetch(self, enable: bool):
        self.fetch_button.configure(state="normal" if enable else "disabled")
        self.cancel_button.configure(state="normal" if not enable else "disabled")

    def update_format_options(self, labels, title=""):
        self.quality_combo.configure(values=labels, state="readonly")
        if labels:
            self.quality_combo.set(labels[0])
        if title:
            self.set_status(f"Detectado: {title[:30]}...", "green")

    def show_error(self, msg: str):
        self.set_status("Error", "red")
        messagebox.showerror("Error", msg)

    def show_success(self, msg: str):
        self.set_status("¡Listo!", "green")
        messagebox.showinfo("Éxito", msg)

    def run(self):
        self.mainloop()
