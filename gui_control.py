import os
import sys
import time
import subprocess
import tkinter as tk
from tkinter import messagebox

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(BASE_DIR, "RAG_venv", "Scripts", "python.exe")

# Global process references
api_process = None
watcher_process = None
streamlit_process = None

# --- 1. API FUNCTIONS ---
def start_api():
    global api_process
    if api_process is None or api_process.poll() is not None:
        cmd = [VENV_PYTHON, "-m", "uvicorn", "main:app", "--reload"]
        api_process = subprocess.Popen(cmd, cwd=BASE_DIR, creationflags=subprocess.CREATE_NO_WINDOW)
        lbl_api_status.config(text="Status: RUNNING 🟢", fg="green")
        btn_start_api.config(state=tk.DISABLED)
        btn_stop_api.config(state=tk.NORMAL)

def stop_api():
    global api_process
    if api_process and api_process.poll() is None:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(api_process.pid)])
        api_process = None
        lbl_api_status.config(text="Status: STOPPED 🔴", fg="red")
        btn_start_api.config(state=tk.NORMAL)
        btn_stop_api.config(state=tk.DISABLED)

# --- 2. WATCHER FUNCTIONS ---
def start_watcher():
    global watcher_process
    if watcher_process is None or watcher_process.poll() is not None:
        cmd = [VENV_PYTHON, "folder_watcher.py"]
        watcher_process = subprocess.Popen(cmd, cwd=BASE_DIR, creationflags=subprocess.CREATE_NO_WINDOW)
        lbl_watch_status.config(text="Status: RUNNING 🟢", fg="green")
        btn_start_watch.config(state=tk.DISABLED)
        btn_stop_watch.config(state=tk.NORMAL)

def stop_watcher():
    global watcher_process
    if watcher_process and watcher_process.poll() is None:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(watcher_process.pid)])
        watcher_process = None
        lbl_watch_status.config(text="Status: STOPPED 🔴", fg="red")
        btn_start_watch.config(state=tk.NORMAL)
        btn_stop_watch.config(state=tk.DISABLED)

# --- 3. STREAMLIT FUNCTIONS ---
def start_streamlit():
    global streamlit_process
    if streamlit_process is None or streamlit_process.poll() is not None:
        cmd = [VENV_PYTHON, "-m", "streamlit", "run", "app.py"]
        streamlit_process = subprocess.Popen(cmd, cwd=BASE_DIR, creationflags=subprocess.CREATE_NO_WINDOW)
        lbl_st_status.config(text="Status: RUNNING 🟢", fg="green")
        btn_start_st.config(state=tk.DISABLED)
        btn_stop_st.config(state=tk.NORMAL)

def stop_streamlit():
    global streamlit_process
    if streamlit_process and streamlit_process.poll() is None:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(streamlit_process.pid)])
        streamlit_process = None
        lbl_st_status.config(text="Status: STOPPED 🔴", fg="red")
        btn_start_st.config(state=tk.NORMAL)
        btn_stop_st.config(state=tk.DISABLED)

# --- BATCH COMMANDS ---
def start_all():
    start_api()
    root.update()
    time.sleep(1.5)  # Pause to give API server time to spin up
    start_watcher()
    root.update()
    time.sleep(0.5)
    start_streamlit()

def stop_all():
    stop_streamlit()
    stop_watcher()
    stop_api()

def on_closing():
    stop_all()
    root.destroy()

# --- GUI WINDOW ---
root = tk.Tk()
root.title("Hub Control Panel")
root.geometry("460x390")
root.resizable(False, False)

# Title
title_label = tk.Label(root, text="🧠 Hub Control Panel", font=("Arial", 14, "bold"))
title_label.pack(pady=8)

# --- STEP 1: API SECTION ---
frame_api = tk.LabelFrame(root, text=" 1. FastAPI Server (main.py) ", font=("Arial", 9, "bold"), padx=10, pady=5)
frame_api.pack(fill="x", padx=15, pady=3)

btn_start_api = tk.Button(frame_api, text="Start API", command=start_api, width=13, bg="#e1f5fe")
btn_start_api.pack(side="left", padx=5)

btn_stop_api = tk.Button(frame_api, text="Stop API", command=stop_api, width=13, state=tk.DISABLED, bg="#ffebee")
btn_stop_api.pack(side="left", padx=5)

lbl_api_status = tk.Label(frame_api, text="Status: STOPPED 🔴", fg="red", font=("Arial", 9, "bold"))
lbl_api_status.pack(side="right", padx=5)

# --- STEP 2: WATCHER SECTION ---
frame_watch = tk.LabelFrame(root, text=" 2. Folder Watcher (folder_watcher.py) ", font=("Arial", 9, "bold"), padx=10, pady=5)
frame_watch.pack(fill="x", padx=15, pady=3)

btn_start_watch = tk.Button(frame_watch, text="Start Watcher", command=start_watcher, width=13, bg="#e1f5fe")
btn_start_watch.pack(side="left", padx=5)

btn_stop_watch = tk.Button(frame_watch, text="Stop Watcher", command=stop_watcher, width=13, state=tk.DISABLED, bg="#ffebee")
btn_stop_watch.pack(side="left", padx=5)

lbl_watch_status = tk.Label(frame_watch, text="Status: STOPPED 🔴", fg="red", font=("Arial", 9, "bold"))
lbl_watch_status.pack(side="right", padx=5)

# --- STEP 3: STREAMLIT SECTION ---
frame_st = tk.LabelFrame(root, text=" 3. Streamlit UI (app.py) ", font=("Arial", 9, "bold"), padx=10, pady=5)
frame_st.pack(fill="x", padx=15, pady=3)

btn_start_st = tk.Button(frame_st, text="Start UI", command=start_streamlit, width=13, bg="#e1f5fe")
btn_start_st.pack(side="left", padx=5)

btn_stop_st = tk.Button(frame_st, text="Stop UI", command=stop_streamlit, width=13, state=tk.DISABLED, bg="#ffebee")
btn_stop_st.pack(side="left", padx=5)

lbl_st_status = tk.Label(frame_st, text="Status: STOPPED 🔴", fg="red", font=("Arial", 9, "bold"))
lbl_st_status.pack(side="right", padx=5)

# --- BOTTOM ACTION BUTTONS ---
frame_actions = tk.Frame(root, pady=10)
frame_actions.pack(fill="x", padx=15)

btn_start_all = tk.Button(frame_actions, text="⚡ Start All", command=start_all, width=15, bg="#c8e6c9", font=("Arial", 9, "bold"))
btn_start_all.pack(side="left", padx=10)

btn_stop_all = tk.Button(frame_actions, text="🛑 Stop All", command=stop_all, width=15, bg="#ffcdd2", font=("Arial", 9, "bold"))
btn_stop_all.pack(side="right", padx=10)

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()