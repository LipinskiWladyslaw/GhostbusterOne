import time
from PyQt5.QtCore import QThread, pyqtSignal

class FileReaderThread(QThread):
    data_ready = pyqtSignal(list)

    def __init__(self, file_path, interval=5):
        super().__init__()
        self.file_path = file_path
        self.interval = interval
        self._running = True

    def run(self):
        while self._running:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                frequencies = []
                for line in lines:
                    parts = line.strip().split(";")
                    if len(parts) > 1:
                        freq = parts[1].strip()
                        frequencies.append(freq)
                    self.data_ready.emit(frequencies)
            except Exception as e:
                print(f"Error reading file: {e}")
            time.sleep(self.interval)

    def stop(self):
        self._running = False

