import os
import sys
import time
import logging
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "watcher.log")
WATCHED_FOLDER = os.path.join(BASE_DIR, "docs")

API_UPLOAD_URL = "http://localhost:8000/api/v1/upload"
API_DELETE_URL = "http://localhost:8000/api/v1/documents"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

class DocumentHandler(FileSystemEventHandler):

    def is_ignored(self, path):
        filename = os.path.basename(path)
        return (
            filename.startswith("~$") or 
            filename.startswith(".") or 
            filename.endswith(".tmp")
        )

    def on_created(self, event):
        if event.is_directory or self.is_ignored(event.src_path):
            return
        filename = os.path.basename(event.src_path)
        logging.info(f"[NOVA DATOTEKA] Detektirana datoteka: {filename}")
        time.sleep(1)
        self.upload_file(event.src_path)

    def on_modified(self, event):
        if event.is_directory or self.is_ignored(event.src_path):
            return
        filename = os.path.basename(event.src_path)
        logging.info(f"[IZMJENA DATOTEKE] Detektirana promjena: {filename}")
        time.sleep(1)
        self.upload_file(event.src_path)

    def on_deleted(self, event):
        if event.is_directory or self.is_ignored(event.src_path):
            return
        filename = os.path.basename(event.src_path)
        logging.info(f"[BRISANJE DATOTEKE] Detektirano brisanje: {filename}")
        self.delete_file_from_api(filename)

    def on_moved(self, event):
        if event.is_directory:
            return
        if self.is_ignored(event.src_path) and self.is_ignored(event.dest_path):
            return

        old_filename = os.path.basename(event.src_path)
        new_filename = os.path.basename(event.dest_path)

        logging.info(f"[PREIMENOVANJE] {old_filename} -> {new_filename}")
        self.delete_file_from_api(old_filename)
        time.sleep(1)
        self.upload_file(event.dest_path)

    # --- RETRY LOGIKA ZA UPLOAD ---
    def upload_file(self, file_path, retries=3, delay=5):
        filename = os.path.basename(file_path)
        
        for attempt in range(1, retries + 1):
            try:
                with open(file_path, "rb") as f:
                    files = {"file": (filename, f)}
                    response = requests.post(API_UPLOAD_URL, files=files, timeout=10)
                    
                if response.status_code in (200, 202):
                    logging.info(f"[API SUCCESS] Datoteka {filename} poslana na indeksiranje (Status: {response.status_code})")
                    return
                else:
                    logging.error(f"[API ERROR] Greška {response.status_code} za {filename}")
            except requests.exceptions.RequestException as e:
                logging.warning(f"[RETRY {attempt}/{retries}] API nedostupan za {filename}. Ponovni pokušaj za {delay}s... ({e})")
                time.sleep(delay)

        logging.error(f"[FAILED] Datoteka {filename} nije poslana na API nakon {retries} pokušaja. Bit će ponovno sinkronizirana pri pokretanju API-ja.")

    # --- RETRY LOGIKA ZA DELETE ---
    def delete_file_from_api(self, filename, retries=3, delay=5):
        url = f"{API_DELETE_URL}/{filename}"
        
        for attempt in range(1, retries + 1):
            try:
                response = requests.delete(url, timeout=10)
                if response.status_code in (200, 202):
                    logging.info(f"[API SUCCESS] Zahtjev za brisanje vektora za {filename} uspješan.")
                    return
                else:
                    logging.error(f"[API ERROR] Greška pri brisanju {filename}: Status {response.status_code}")
            except requests.exceptions.RequestException as e:
                logging.warning(f"[RETRY {attempt}/{retries}] API nedostupan za brisanje {filename}. Ponovni pokušaj za {delay}s... ({e})")
                time.sleep(delay)

        logging.error(f"[FAILED] Zahtjev za brisanje {filename} nije poslan nakon {retries} pokušaja.")

if __name__ == "__main__":
    os.makedirs(WATCHED_FOLDER, exist_ok=True)
    
    event_handler = DocumentHandler()
    observer = Observer()
    observer.schedule(event_handler, path=WATCHED_FOLDER, recursive=True)
    
    logging.info(f"Pokrenut napredni watcher servis s retry logikom. Pratim mapu: {WATCHED_FOLDER}")
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Zaustavljanje watcher servisa...")
        observer.stop()
    observer.join()