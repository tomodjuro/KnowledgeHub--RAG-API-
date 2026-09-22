import os
import sys
import time
import threading
import uvicorn
import psutil

# Nužno za sprečavanje rekurzije na Windowsima
import multiprocessing
multiprocessing.freeze_support()

# Postavljanje radnog direktorija (podržava i .py i PyInstaller .exe okruženje)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)

def start_backend():
    """Pokreće FastAPI poslužitelj."""
    print("[INIT] Pokrećem FastAPI Backend na portu 8000...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="error")

def start_watcher():
    """Pokreće Folder Watcher."""
    print("[INIT] Pokrećem Folder Watcher...")
    try:
        import folder_watcher
        if hasattr(folder_watcher, 'main'):
            folder_watcher.main()
    except Exception as e:
        print(f"[ERROR] Watcher greška: {e}")

def start_streamlit():
    """Pokreće Streamlit izravno iz Python koda bez subprocess petlje."""
    print("[INIT] Pokrećem Streamlit UI na portu 8501...")
    
    # Postavljanje argumenata koje Streamlit inače prima iz CLI-ja
    # Dodan --server.fileWatcherType=none za izbjegavanje torchvision ModuleNotFoundError greške
    sys.argv = [
        "streamlit",
        "run",
        os.path.join(BASE_DIR, "app.py"),
        "--server.port=8501",
        "--server.headless=true",
        "--global.developmentMode=false",
        "--server.fileWatcherType=none"
    ]
    
    from streamlit.web import cli as stcli
    stcli.main()

def sprijeci_rekurziju():
    # Prebroj koliko je run_app.exe procesa trenutno aktivno
    moj_naziv = os.path.basename(sys.executable)
    broj_procesa = sum(1 for p in psutil.process_iter(['name']) if p.info['name'] == moj_naziv)
    
    if broj_procesa > 2: # Ako ih ima više od 2 (glavni + 1 radni), prekini!
        print(f"[SIGURNOST] Detektirano {broj_procesa} procesa! Prisilno gašenje radi spriječavanja rušenja PC-a.")
        sys.exit(1)

if __name__ == "__main__":
    sprijeci_rekurziju()
    # 1. Pokreni FastAPI u zasebnoj niti (Thread)
    api_thread = threading.Thread(target=start_backend, daemon=True)
    api_thread.start()

    # 2. Pokreni Watcher u zasebnoj niti (Thread)
    watcher_thread = threading.Thread(target=start_watcher, daemon=True)
    watcher_thread.start()

    # Kratka stanka da se backend stabilizira
    time.sleep(2)

    # 3. Pokreni Streamlit u glavnoj niti
    start_streamlit()