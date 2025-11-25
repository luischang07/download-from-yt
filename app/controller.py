import threading
import re
from .model import DownloaderModel
from .view import DownloaderView


class DownloaderController:
    """Controller that wires the Model and View together.

    It handles user actions from the view, delegates work to the model,
    and updates the view accordingly. All long‑running operations are
    executed in background threads to keep the UI responsive.
    """

    def __init__(self, model: DownloaderModel, view: DownloaderView):
        self.model = model
        self.view = view
        # Wire callbacks from the view to controller methods
        self.view.on_fetch = self.handle_fetch
        self.view.on_download = self.handle_download
        self.view.on_type_change = self.handle_type_change
        self.view.on_browse_folder = self.handle_browse_folder
        self.view.on_cancel_search = self.handle_cancel_search
        self.view.on_open_player = self.handle_open_player
        # Internal state
        self.is_searching = False
        self.search_thread = None
        self.download_thread = None

    # ---------------------------------------------------------------------
    # Callback implementations
    # ---------------------------------------------------------------------
    def handle_type_change(self, mode: str):
        """Reset format options when the user switches between Video/Audio."""
        self.view.update_format_options(["Primero busca el video"], title="")
        self.view.set_status("Modo cambiado", "gray")

    def handle_fetch(self, url: str, mode: str):
        """Fetch available formats for the given URL.

        The formats are sorted from highest to lowest resolution before
        being presented to the user.
        """
        if not url:
            self.view.set_status("URL vacía", "red")
            return
        # Prevent multiple concurrent searches
        if self.is_searching:
            self.view.set_status("Búsqueda en curso", "orange")
            return
        self.is_searching = True
        self.view.set_status("Analizando...", "blue")
        self.view.enable_fetch(False)

        def fetch_thread():
            try:
                formats, title = self.model.fetch_formats(url, mode)
                # Sort formats by numeric height (largest first)
                def height(label):
                    m = re.search(r"(\d+)", label)
                    return int(m.group(1)) if m else 0
                formats.sort(key=lambda f: height(f["label"]), reverse=True)
                # Add "Best Quality" option
                if formats:
                    best = formats[0].copy()
                    best["label"] = "Mejor calidad (Automático)"
                    formats.insert(0, best)
                labels = [f["label"] for f in formats]
                # Store formats for later download lookup
                self.view.available_formats = formats
                # Update UI on the main thread
                self.view.after(0, lambda: self.view.update_format_options(labels, title))
            except Exception as e:
                self.view.after(0, lambda: self.view.show_error(str(e)))
            finally:
                self.is_searching = False
                self.view.after(0, lambda: self.view.enable_fetch(True))

        self.search_thread = threading.Thread(target=fetch_thread, daemon=True)
        self.search_thread.start()

    def handle_download(self, url: str, fmt_label: str, mode: str, path: str):
        """Download the selected format to the chosen folder.

        The progress bar and percentage text are updated in real time.
        The percentage text colour is set to white for better contrast.
        """
        if not url or not fmt_label or not path:
            self.view.set_status("Datos incompletos", "red")
            return
        # Locate the format dict from the previously fetched list
        fmt = next((f for f in getattr(self.view, "available_formats", []) if f["label"] == fmt_label), None)
        if not fmt:
            self.view.set_status("Formato no encontrado", "red")
            return
        format_id = fmt["format_id"]
        self.view.set_status("Descargando...", "blue")
        self.view.download_button.configure(state="disabled")

        def progress_hook(d):
            if d.get('status') == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 1
                downloaded = d.get('downloaded_bytes', 0)
                fraction = downloaded / total
                # Update progress bar and percentage label on the UI thread
                self.view.after(0, lambda: self.view.set_progress(fraction))
                self.view.after(0, lambda: self.view.set_status(f"{fraction*100:.0f}%", "white"))

        def download_thread():
            try:
                self.model.download(url, format_id, path, mode, progress_hook)
                self.view.after(0, lambda: self.view.set_status("¡Listo!", "green"))
                self.view.after(0, lambda: self.view.set_progress(1.0))
                # Show a brief success message
                self.view.after(0, lambda: self.view.show_success("Descarga completada"))
            except Exception as e:
                msg = str(e)
                self.view.after(0, lambda: self.view.show_error(msg))
            finally:
                self.view.after(0, lambda: self.view.download_button.configure(state="normal"))

        self.download_thread = threading.Thread(target=download_thread, daemon=True)
        self.download_thread.start()

    def handle_browse_folder(self):
        """Open a folder chooser and update the download path entry."""
        from tkinter import filedialog
        folder = filedialog.askdirectory()
        if folder:
            self.view.download_path = folder
            self.view.path_entry.delete(0, "end")
            self.view.path_entry.insert(0, folder)

    def handle_cancel_search(self):
        """Attempt to cancel an ongoing format search.

        The yt‑dlp fetch runs in a thread; we simply flip the flag so the UI
        knows the operation was aborted. The thread will finish naturally.
        """
        if self.is_searching:
            self.is_searching = False
            self.view.set_status("Cancelado", "orange")
            self.view.enable_fetch(True)

    def handle_open_player(self, uri: str, title: str = "Video"):
        """Show the media player view and load the selected media."""
        self.view.show_view("player")
        if hasattr(self.view, "player_frame"):
            self.view.player_frame.load_media(uri, title)
