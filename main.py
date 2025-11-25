from app.model import DownloaderModel
from app.view import DownloaderView
from app.controller import DownloaderController


def main():
    model = DownloaderModel()
    view = DownloaderView()
    controller = DownloaderController(model, view)
    # Start the UI loop
    view.run()


if __name__ == "__main__":
    main()
