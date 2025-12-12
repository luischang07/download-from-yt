import threading
import os
from tkinter import messagebox, filedialog
from plyer import notification
from .model import DownloaderModel
from .view import DownloaderView

class DownloaderController:
    def __init__(self):
        self.model = DownloaderModel()
        self.view = DownloaderView(self)
        self.last_view = "home"
        self.all_files = []
        
        # Iniciar en la vista Home
        self.show_view("home")

    def run(self):
        self.view.mainloop()

    def check_clipboard(self, event=None):
        try:
            if self.last_view != "home": return
            
            clipboard_text = self.view.clipboard_get()
            if not clipboard_text: return
            
            if "youtube.com/watch" in clipboard_text or "youtu.be/" in clipboard_text:
                current_text = self.view.url_entry.get()
                if clipboard_text.strip() != current_text.strip():
                    self.view.url_entry.delete(0, "end")
                    self.view.url_entry.insert(0, clipboard_text)
                    self.fetch_formats()
        except: pass

    def fetch_formats(self):
        url = self.view.url_entry.get().strip()
        if not url: return
        
        self.view.fetch_button.configure(state="disabled")
        self.view.url_entry.configure(placeholder_text="Analizando enlace...")
        
        self.model.fetch_video_info(url, self._on_fetch_success, self._on_fetch_error)

    def _on_fetch_success(self, info):
        self.view.after(0, lambda: self._process_formats_ui(self.view.type_selector.get()))

    def _on_fetch_error(self, error_msg):
        self.view.after(0, lambda: [
            self.view.fetch_button.configure(state="normal"),
            self.view.url_entry.configure(placeholder_text="Pega el enlace de YouTube aquí..."),
            messagebox.showerror("Error", error_msg)
        ])

    def on_type_change(self, value):
        if self.model.current_video_info:
            self._process_formats_ui(value)
        else:
            self.view.results_card.pack_forget()

    def _process_formats_ui(self, mode):
        formats, title, thumb_url, _ = self.model.process_formats(mode)
        labels = [f['label'] for f in formats]
        
        # Load thumbnail in background
        def load_thumb():
            img = self.model.load_thumbnail_image(thumb_url) if thumb_url else None
            self.view.after(0, lambda: self.view.update_formats_ui(labels, title, img))
            self.view.after(0, lambda: [
                self.view.fetch_button.configure(state="normal"),
                self.view.url_entry.configure(placeholder_text="Pega el enlace de YouTube aquí...")
            ])
        
        threading.Thread(target=load_thumb, daemon=True).start()

    def start_download(self):
        url = self.view.url_entry.get().strip()
        if not url or not self.model.available_formats: return
        
        sel_label = self.view.quality_combo.get()
        sel_data = next((f for f in self.model.available_formats if f['label'] == sel_label), None)
        if not sel_data: return
        
        custom_name = self.view.filename_entry.get().strip()
        if not custom_name: custom_name = "video_download"
        custom_name = "".join([c for c in custom_name if c.isalnum() or c in (' ', '-', '_', '.')]).strip()
        
        mode = self.view.type_selector.get()
        ext = "mp3" if mode == "Audio" else "mp4"
        
        final_name = custom_name
        counter = 1
        while os.path.exists(os.path.join(self.model.download_path, f"{final_name}.{ext}")):
            final_name = f"{custom_name} (#{counter})"
            counter += 1
        
        self.view.download_button.configure(state="disabled", text="Descargando...")
        self.view.progress_container.pack(pady=20, padx=20, fill="x")
        self.view.progress_percent_lbl.configure(text="0%")
        self.view.progress_status_lbl.configure(text="Iniciando descarga...")
        self.view.completion_label.configure(text="")
        self.view.progress_bar.set(0)

        # Capture title for notification
        video_title = self.model.current_video_info.get('title', 'Video')

        self.model.download_video(url, sel_data, mode, final_name, 
                                  self._on_download_progress, 
                                  lambda: self._on_download_complete(video_title), 
                                  self._on_download_error)

    def _on_download_progress(self, p):
        self.view.after(0, self.view.progress_bar.set, p)
        self.view.after(0, lambda: self.view.progress_percent_lbl.configure(text=f"{int(p*100)}%"))
        self.view.after(0, lambda: self.view.progress_status_lbl.configure(text="Descargando..."))

    def _on_download_complete(self, video_title="Video"):
        self.view.after(0, lambda: [
            self.view.progress_bar.set(1),
            self.view.progress_percent_lbl.configure(text="100%"),
            self.view.progress_status_lbl.configure(text="Finalizado"),
            self.view.completion_label.configure(text="¡Archivo guardado correctamente!"),
            self.view.download_button.configure(state="normal", text="Descargar Ahora"),
            self.view.after(4000, self.view.progress_container.pack_forget)
        ])
        
        try:
            notification.notify(
                title="Descarga Completada",
                message=f"{video_title} se ha descargado correctamente.",
                app_name="YT Downloader",
                timeout=5
            )
        except: pass

    def _on_download_error(self, msg):
        self.view.after(0, lambda: [
            self.view.progress_container.pack_forget(),
            self.view.download_button.configure(state="normal", text="Descargar Ahora"),
            messagebox.showerror("Error", msg)
        ])

    def add_to_queue(self):
        if not self.model.current_video_info: return
        url = self.model.current_video_info.get('webpage_url')
        
        if not url or not self.model.available_formats: return
        
        sel_label = self.view.quality_combo.get()
        sel_data = next((f for f in self.model.available_formats if f['label'] == sel_label), None)
        if not sel_data: return
        
        custom_name = self.view.filename_entry.get().strip()
        if not custom_name: custom_name = "video_download"
        custom_name = "".join([c for c in custom_name if c.isalnum() or c in (' ', '-', '_', '.')]).strip()
        
        mode = self.view.type_selector.get()
        
        # Get title and thumbnail from model
        title = self.model.current_video_info.get('title', 'Video')
        thumbnail_url = self.model.current_video_info.get('thumbnail')

        idx = self.model.add_to_queue(url, sel_data, mode, custom_name, title, thumbnail_url)
        
        # Add to UI
        item_data = self.model.download_queue[idx]
        self.view.add_queue_item_widget(item_data, idx)
        
        self.view.show_toast("Video agregado a la cola")

    def start_queue(self):
        if not self.model.download_queue:
            messagebox.showinfo("Cola", "La cola está vacía")
            return
            
        self.show_view("queue")
        self.view.btn_start_queue.configure(state="disabled", text="Procesando...")
        
        self.model.process_queue(
            self._on_queue_progress,
            self._on_queue_item_complete,
            self._on_queue_all_complete,
            self._on_queue_error
        )

    def _on_queue_progress(self, index, p):
        self.view.after(0, lambda: self.view.update_queue_item_status(index, "downloading", p))

    def _on_queue_item_complete(self, index):
        self.view.after(0, lambda: self.view.update_queue_item_status(index, "completed"))

    def _on_queue_all_complete(self):
        self.view.after(0, lambda: [
            self.view.btn_start_queue.configure(state="normal", text="▶ Iniciar Cola"),
            self.view.show_toast("Todas las descargas han finalizado")
        ])
        
        try:
            notification.notify(
                title="Cola Finalizada",
                message="Todas las descargas de la cola han terminado.",
                app_name="YT Downloader",
                timeout=5
            )
        except: pass

    def _on_queue_error(self, index, msg):
        self.view.after(0, lambda: [
            self.view.update_queue_item_status(index, "error"),
            print(f"Error en item {index}: {msg}")
        ])

    def browse_folder(self):
        d = filedialog.askdirectory()
        if d:
            self.model.save_config(d)
            self.view.update_path_labels(d)
            
            # Si estamos en la biblioteca, recargarla para mostrar los archivos de la nueva carpeta
            if self.last_view == "library":
                self.show_view("library")

    def show_view(self, view_name):
        # Determine target view name
        if view_name == "last": 
            view_name = self.last_view
        elif view_name != "player":
            self.last_view = view_name
            
        # Check if we are leaving player view
        is_leaving_player = (self.view.active_view == self.view.player_frame and view_name != "player")
        is_entering_player = (view_name == "player")

        # Perform view switch
        self.view.show_view(view_name)
        
        # Mini Player Logic
        if is_leaving_player:
            # Solo activar si el reproductor está activo (Playing/Paused) y NO detenido explícitamente
            # Usamos is_playing del frame que rastrea el estado lógico, o consultamos a VLC
            player = self.view.player_frame.player
            should_minimize = False
            
            if player:
                state = player.get_state()
                # Estados válidos para minimizar: Playing, Paused, Buffering
                # Estados inválidos: Stopped, Ended, Error (que ocurren al cerrar con X)
                import vlc
                if state in [vlc.State.Playing, vlc.State.Paused, vlc.State.Buffering, vlc.State.Opening]:
                    should_minimize = True
            
            if should_minimize:
                # Show mini player
                self.view.show_mini_player()
                self.view.update_idletasks() # Ensure UI is updated
                # Switch output to mini player
                self.view.player_frame.switch_output(self.view.mini_video_container.winfo_id())
        
        elif is_entering_player:
            # Hide mini player
            self.view.hide_mini_player()
            self.view.update_idletasks()
            # Switch output back to main player
            self.view.player_frame.switch_output(self.view.player_frame.video_frame.winfo_id())
        
        # Asegurar que las etiquetas de ruta estén actualizadas en todas las vistas
        self.view.update_path_labels(self.model.download_path)
        
        if view_name == "library":
            self.all_files = self.model.get_library_files()
            self.view.render_library(self.all_files)
        elif view_name == "home":
            pass # Ya se actualizó arriba con update_path_labels

    def toggle_play(self):
        if hasattr(self.view, 'player_frame'):
            self.view.player_frame.toggle_play()

    def restore_player(self):
        self.show_view("player")

    def stop_mini_player(self):
        if hasattr(self.view, 'player_frame'):
            self.view.player_frame.stop()
        self.view.hide_mini_player()

    def filter_library(self, *args):
        q = self.view.search_var.get().lower()
        filtered = [f for f in self.all_files if q in f['name'].lower()]
        self.view.render_library(filtered)

    def play_preview(self):
        if self.model.preview_url:
            self.open_player(self.model.preview_url, "Previsualización", self.model.preview_formats)
        else:
            messagebox.showinfo("Aviso", "No se pudo obtener una URL de previsualización para este video.")

    def open_player(self, uri, title, formats=None):
        # Asegurar que el mini player esté oculto y el output reseteado antes de cargar nuevo video
        self.view.hide_mini_player()
        
        # Si venimos de otra vista, esto activará show_view("player")
        # Pero necesitamos asegurarnos de que NO intente hacer un switch_output erróneo
        self.show_view("player")
        
        self.view.update_idletasks()
        self.view.player_frame.load_media(uri, title, formats)

    # --- NUEVO: Lógica de Actualización ---
    def update_engine(self):
        self.view.show_toast("Buscando actualizaciones del motor...")
        # Ejecutar en hilo para no congelar la UI
        threading.Thread(target=self._update_engine_thread, daemon=True).start()

    def _update_engine_thread(self):
        success, message = self.model.update_ytdlp()
        # Mostrar resultado en el hilo principal
        self.view.after(0, lambda: self.view.show_toast(message))
        if success:
            self.view.after(0, lambda: self.view.show_toast("Reinicia la app para aplicar cambios"))
    # --------------------------------------
