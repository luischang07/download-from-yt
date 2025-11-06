import customtkinter as ctk
from tkinter import filedialog, messagebox
import yt_dlp
import threading
import os


class YouTubeDownloader:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("YouTube Video Downloader")
        self.window.geometry("700x500")
        
        # Configurar tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Inicializar variables antes de setup_ui
        self.download_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.available_formats = []
        
        self.setup_ui()
        
    def setup_ui(self):
        # Frame principal
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame, 
            text="YouTube Video Downloader", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=10)
        
        # URL Input
        url_label = ctk.CTkLabel(main_frame, text="URL del video de YouTube:")
        url_label.pack(pady=(10, 5))
        
        self.url_entry = ctk.CTkEntry(main_frame, width=500, placeholder_text="https://www.youtube.com/watch?v=...")
        self.url_entry.pack(pady=5)
        
        # Botón para obtener formatos
        self.fetch_button = ctk.CTkButton(
            main_frame, 
            text="Obtener Calidades Disponibles",
            command=self.fetch_formats
        )
        self.fetch_button.pack(pady=10)
        
        # Selector de calidad
        quality_label = ctk.CTkLabel(main_frame, text="Seleccionar Calidad:")
        quality_label.pack(pady=(10, 5))
        
        self.quality_combo = ctk.CTkComboBox(
            main_frame, 
            width=400,
            state="disabled",
            values=["Primero obten las calidades disponibles"]
        )
        self.quality_combo.pack(pady=5)
        
        # Frame para ruta de descarga
        path_frame = ctk.CTkFrame(main_frame)
        path_frame.pack(pady=10, fill="x", padx=20)
        
        path_label = ctk.CTkLabel(path_frame, text="Guardar en:")
        path_label.pack(side="left", padx=5)
        
        self.path_entry = ctk.CTkEntry(path_frame, width=350)
        self.path_entry.insert(0, self.download_path)
        self.path_entry.pack(side="left", padx=5)
        
        browse_button = ctk.CTkButton(
            path_frame, 
            text="Explorar", 
            width=80,
            command=self.browse_folder
        )
        browse_button.pack(side="left", padx=5)
        
        # Barra de progreso
        self.progress_bar = ctk.CTkProgressBar(main_frame, width=500)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        # Label de estado
        self.status_label = ctk.CTkLabel(main_frame, text="Listo para descargar", text_color="gray")
        self.status_label.pack(pady=5)
        
        # Botón de descarga
        self.download_button = ctk.CTkButton(
            main_frame,
            text="Descargar Video",
            command=self.start_download,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.download_button.pack(pady=20)
        
    def fetch_formats(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Advertencia", "Por favor ingresa una URL válida")
            return
        
        self.fetch_button.configure(state="disabled")
        self.status_label.configure(text="Obteniendo información del video...", text_color="blue")
        
        thread = threading.Thread(target=self._fetch_formats_thread, args=(url,))
        thread.daemon = True
        thread.start()
        
    def _fetch_formats_thread(self, url):
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Diccionario para almacenar las mejores opciones por resolución
                formats_dict = {}
                
                # Debug: Imprimir todos los formatos disponibles
                print("\n=== FORMATOS DISPONIBLES ===")
                for f in info.get('formats', []):
                    fid = f.get('format_id', 'N/A')
                    height = f.get('height')
                    vcodec = f.get('vcodec', 'N/A')
                    acodec = f.get('acodec', 'N/A')
                    ext = f.get('ext', 'N/A')
                    height_str = f"{height}p" if height else "N/A"
                    print(f"ID: {fid:6} | {height_str:6} | Video: {vcodec:15} | Audio: {acodec:15} | Ext: {ext}")
                print("=" * 80)
                
                # Buscar TODOS los formatos de video (con o sin audio)
                for f in info.get('formats', []):
                    vcodec = f.get('vcodec', 'none')
                    has_video = vcodec and vcodec != 'none'
                    height = f.get('height')
                    format_id = f.get('format_id')
                    ext = f.get('ext', 'mp4')
                    
                    # Incluir todos los formatos con video
                    if has_video and height and format_id:
                        resolution = f"{height}p"
                        
                        # Guardar el mejor formato para cada resolución
                        if resolution not in formats_dict:
                            formats_dict[resolution] = {
                                'label': resolution,
                                'format_id': format_id,
                                'height': height,
                                'ext': ext
                            }
                        elif ext == 'mp4' and formats_dict[resolution]['ext'] != 'mp4':
                            # Preferir mp4 sobre webm
                            formats_dict[resolution] = {
                                'label': resolution,
                                'format_id': format_id,
                                'height': height,
                                'ext': ext
                            }
                
                print(f"\n=== RESOLUCIONES DETECTADAS: {list(formats_dict.keys())} ===\n")
                
                # Convertir a lista y ordenar
                format_list = []
                
                # Agregar opción de mejor calidad (la más segura)
                format_list.append(('best_auto', {
                    'label': '🏆 Mejor calidad disponible (automático)',
                    'format_id': 'bv*+ba/b',  # Mejor video + mejor audio / mejor combinado
                    'height': 999999
                }))
                
                # Agregar las resoluciones encontradas con múltiples fallbacks
                sorted_formats = sorted(formats_dict.items(), key=lambda x: x[1]['height'], reverse=True)
                for key, data in sorted_formats:
                    format_id = data['format_id']
                    height = data['height']
                    # Usar formato con múltiples fallbacks
                    fallback_format = f'bv*[height<={height}]+ba/b[height<={height}]/bv*+ba/b'
                    format_list.append((key, {
                        'label': f"{key}",
                        'format_id': fallback_format,
                        'height': data['height']
                    }))
                
                self.available_formats = format_list
                format_labels = [f[1]['label'] for f in format_list]
                
                # Actualizar UI
                self.window.after(0, self._update_formats_ui, format_labels, info.get('title', 'Video'))
                
        except Exception as e:
            self.window.after(0, self._show_error, f"Error al obtener información: {str(e)}")
        finally:
            self.window.after(0, lambda: self.fetch_button.configure(state="normal"))
    
    def _update_formats_ui(self, format_labels, title):
        self.quality_combo.configure(values=format_labels, state="readonly")
        if format_labels:
            self.quality_combo.set(format_labels[0])
        self.status_label.configure(text=f"Video: {title[:50]}...", text_color="green")
        
    def _show_error(self, message):
        self.status_label.configure(text="Error", text_color="red")
        messagebox.showerror("Error", message)
        
    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_path)
        if folder:
            self.download_path = folder
            self.path_entry.delete(0, 'end')
            self.path_entry.insert(0, folder)
            
    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Advertencia", "Por favor ingresa una URL válida")
            return
        
        if not self.available_formats:
            messagebox.showwarning("Advertencia", "Primero obtén las calidades disponibles")
            return
        
        selected_quality = self.quality_combo.get()
        if not selected_quality or selected_quality == "Primero obten las calidades disponibles":
            messagebox.showwarning("Advertencia", "Por favor selecciona una calidad")
            return
        
        # Encontrar el format_id seleccionado
        format_id = None
        for fmt_key, fmt_data in self.available_formats:
            if fmt_data['label'] == selected_quality:
                format_id = fmt_data['format_id']
                break
        
        if not format_id:
            messagebox.showerror("Error", "No se pudo determinar el formato seleccionado")
            return
        
        self.download_button.configure(state="disabled")
        self.fetch_button.configure(state="disabled")
        
        thread = threading.Thread(
            target=self._download_thread, 
            args=(url, format_id, self.download_path)
        )
        thread.daemon = True
        thread.start()
        
    def _download_thread(self, url, format_id, output_path):
        try:
            def progress_hook(d):
                if d['status'] == 'downloading':
                    if 'total_bytes' in d:
                        progress = d['downloaded_bytes'] / d['total_bytes']
                        self.window.after(0, self.progress_bar.set, progress)
                        percent = progress * 100
                        self.window.after(
                            0, 
                            self.status_label.configure, 
                            {"text": f"Descargando: {percent:.1f}%", "text_color": "blue"}
                        )
                    elif 'downloaded_bytes' in d:
                        mb = d['downloaded_bytes'] / (1024*1024)
                        self.window.after(
                            0, 
                            self.status_label.configure, 
                            {"text": f"Descargando: {mb:.1f}MB", "text_color": "blue"}
                        )
                elif d['status'] == 'finished':
                    self.window.after(0, self.progress_bar.set, 1.0)
                    self.window.after(
                        0, 
                        self.status_label.configure, 
                        {"text": "Procesando video con ffmpeg...", "text_color": "orange"}
                    )
            
            ydl_opts = {
                'format': format_id,
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'nocheckcertificate': True,
                'merge_output_format': 'mp4',
                'postprocessor_args': [
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-b:a', '192k',
                ],
                'http_chunk_size': 10485760,  # 10MB chunks
                'retries': 15,
                'fragment_retries': 15,
                'skip_unavailable_fragments': True,
                'keepvideo': False,
                'noprogress': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            self.window.after(0, self._download_complete, output_path)
            
        except Exception as e:
            self.window.after(0, self._download_error, str(e))
        finally:
            self.window.after(0, lambda: self.download_button.configure(state="normal"))
            self.window.after(0, lambda: self.fetch_button.configure(state="normal"))
    
    def _download_complete(self, output_path):
        self.progress_bar.set(0)
        self.status_label.configure(text="¡Descarga completada!", text_color="green")
        messagebox.showinfo(
            "Éxito", 
            f"Video descargado exitosamente en:\n{output_path}"
        )
        
    def _download_error(self, error_message):
        self.progress_bar.set(0)
        self.status_label.configure(text="Error en la descarga", text_color="red")
        messagebox.showerror("Error", f"Error al descargar el video:\n{error_message}")
        
    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = YouTubeDownloader()
    app.run()
