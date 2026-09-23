import os
import sys
import time
import threading
import uvicorn
import psutil
import multiprocessing

# Nužno za sprečavanje rekurzije na Windowsima
multiprocessing.freeze_support()

# Radni direktorij (podržava i .py i PyInstaller .exe okruženje)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)

# Automatsko kreiranje docs mape uz .exe
DOCS_DIR = os.path.join(BASE_DIR, "docs")
os.makedirs(DOCS_DIR, exist_ok=True)

def sprijeci_rekurziju():
    """Sigurnosni kočnik u slučaju neočekivanog umnažanja procesa."""
    moj_naziv = os.path.basename(sys.executable)
    broj_procesa = sum(1 for p in psutil.process_iter(['name']) if p.info['name'] == moj_naziv)
    
    # Dozvoljavamo maksimalno 2 procesa (glavni .exe + eventualni Streamlit worker)
    if broj_procesa > 2:
        print(f"[SIGURNOST] Detektirano {broj_procesa} procesa! Prisilno gašenje radi spriječavanja rušenja PC-a.")
        sys.exit(1)

def start_backend():
    """Pokreće FastAPI poslužitelj."""
    print("[INIT] Pokrećem FastAPI Backend na http://127.0.0.1:8000...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="info")

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
    """Pokreće Streamlit s točnom putanjom do app.py u PyInstaller okruženju."""
    print("[INIT] Pokrećem Streamlit UI na http://127.0.0.1:8501...")
    
    # Ako je zapakirano u .exe, PyInstaller stavlja dodane datoteke u _internal ili sys._MEIPASS
    if getattr(sys, 'frozen', False):
        internal_dir = getattr(sys, '_MEIPASS', os.path.join(BASE_DIR, "_internal"))
        app_path = os.path.join(internal_dir, "app.py")
        if not os.path.exists(app_path):
            # Sigurnosna provjera ako je app.py slučajno ručno kopiran uz run_app.exe
            app_path = os.path.join(BASE_DIR, "app.py")
    else:
        app_path = os.path.join(BASE_DIR, "app.py")
    
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--server.port=8501",
        "--server.headless=true",
        "--global.developmentMode=false",
        "--server.fileWatcherType=none"
    ]
    
    from streamlit.web import cli as stcli
    stcli.main()

if __name__ == "__main__":
    # Provjera osigurača prije bilo kakvog pokretanja niti
    sprijeci_rekurziju()

    # 1. Pokreni FastAPI u zasebnoj dretvi
    api_thread = threading.Thread(target=start_backend, daemon=True)
    api_thread.start()

    # 2. Pokreni Watcher u zasebnoj dretvi
    watcher_thread = threading.Thread(target=start_watcher, daemon=True)
    watcher_thread.start()

    # Kratka stanka da se backend inicijalizira
    time.sleep(2)

    # 3. Pokreni Streamlit UI u glavnoj niti
    start_streamlit()