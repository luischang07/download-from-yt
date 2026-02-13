from app.controller import DownloaderController
import ctypes

if __name__ == "__main__":
    try:
        # Configurar AppUserModelID para que Windows reconozca la app y sus notificaciones
        myappid = 'YT Downloader'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass
        
    app = DownloaderController()
    app.run()
