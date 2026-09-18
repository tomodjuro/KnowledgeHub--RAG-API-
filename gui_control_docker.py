import os
import sys
import time
import subprocess
import tkinter as tk
from tkinter import messagebox

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Global process tracking
is_running = False

def check_docker_installed():
    """Checks if Docker is installed and accessible."""
    try:
        subprocess.run(["docker", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

# --- DOCKER CONTAINER ACTIONS ---
def start_all():
    global is_running
    if not check_docker_installed():
        messagebox.showerror("Docker Error", "Docker Desktop is not running or not installed!")
        return

    try:
        # Executes 'docker compose up -d --build' in the background
        cmd = ["docker", "compose", "up", "-d"]
        subprocess.Popen(cmd, cwd=BASE_DIR, shell=True)
        
        is_running = True
        
        # Update UI Labels
        lbl_api_status.config(text="Status: RUNNING 🟢", fg="green")
        lbl_watch_status.config(text="Status: RUNNING 🟢", fg="green")
        lbl_st_status.config(text="Status: RUNNING 🟢", fg="green")
        
        btn_start_all.config(state=tk.DISABLED)
        btn_stop_all.config(state=tk.NORMAL)
    except Exception as e:
        messagebox.showerror("Execution Error", f"Failed to start Docker containers:\n{str(e)}")

def stop_all():
    global is_running
    try:
        # Executes 'docker compose down' to gracefully stop containers
        cmd = ["docker", "compose", "down"]
        subprocess.Popen(cmd, cwd=BASE_DIR, shell=True)
        
        is_running = False
        
        # Update UI Labels
        lbl_api_status.config(text="Status: STOPPED 🔴", fg="red")
        lbl_watch_status.config(text="Status: STOPPED 🔴", fg="red")
        lbl_st_status.config(text="Status: STOPPED 🔴", fg="red")
        
        btn_start_all.config(state=tk.NORMAL)
        btn_stop_all.config(state=tk.DISABLED)
    except Exception as e:
        messagebox.showerror("Execution Error", f"Failed to stop Docker containers:\n{str(e)}")

def on_closing():
    if is_running:
        if messagebox.askokcancel("Exit", "Containers are still running. Do you want to stop them before exiting?"):
            stop_all()
            root.destroy()
    else:
        root.destroy()

# --- GUI WINDOW SETUP ---
root = tk.Tk()
root.title("DocuBrain Docker Panel")
root.geometry("460x390")
root.resizable(False, False)

# Main Title
title_label = tk.Label(root, text="🐳 DocuBrain Docker Panel", font=("Arial", 14, "bold"))
title_label.pack(pady=8)

# --- STEP 1: API CONTAINER SECTION ---
frame_api = tk.LabelFrame(root, text=" 1. FastAPI Backend Container ", font=("Arial", 9, "bold"), padx=10, pady=5)
frame_api.pack(fill="x", padx=15, pady=3)

lbl_api_desc = tk.Label(frame_api, text="Port: 8000 | Endpoint: /api/v1", font=("Arial", 8), fg="gray")
lbl_api_desc.pack(side="left", padx=5)

lbl_api_status = tk.Label(frame_api, text="Status: STOPPED 🔴", fg="red", font=("Arial", 9, "bold"))
lbl_api_status.pack(side="right", padx=5)

# --- STEP 2: WATCHER CONTAINER SECTION ---
frame_watch = tk.LabelFrame(root, text=" 2. Folder Watcher Container ", font=("Arial", 9, "bold"), padx=10, pady=5)
frame_watch.pack(fill="x", padx=15, pady=3)

lbl_watch_desc = tk.Label(frame_watch, text="Monitors: ./docs directory", font=("Arial", 8), fg="gray")
lbl_watch_desc.pack(side="left", padx=5)

lbl_watch_status = tk.Label(frame_watch, text="Status: STOPPED 🔴", fg="red", font=("Arial", 9, "bold"))
lbl_watch_status.pack(side="right", padx=5)

# --- STEP 3: STREAMLIT CONTAINER SECTION ---
frame_st = tk.LabelFrame(root, text=" 3. Streamlit UI Container ", font=("Arial", 9, "bold"), padx=10, pady=5)
frame_st.pack(fill="x", padx=15, pady=3)

lbl_st_desc = tk.Label(frame_st, text="Port: 8501 | Web Interface", font=("Arial", 8), fg="gray")
lbl_st_desc.pack(side="left", padx=5)

lbl_st_status = tk.Label(frame_st, text="Status: STOPPED 🔴", fg="red", font=("Arial", 9, "bold"))
lbl_st_status.pack(side="right", padx=5)

# --- ACTION BUTTONS SECTION ---
frame_actions = tk.Frame(root, pady=15)
frame_actions.pack(fill="x", padx=15)

btn_start_all = tk.Button(
    frame_actions, 
    text="⚡ Start Stack", 
    command=start_all, 
    width=16, 
    bg="#c8e6c9", 
    font=("Arial", 10, "bold")
)
btn_start_all.pack(side="left", padx=10)

btn_stop_all = tk.Button(
    frame_actions, 
    text="🛑 Stop Stack", 
    command=stop_all, 
    width=16, 
    bg="#ffcdd2", 
    font=("Arial", 10, "bold"), 
    state=tk.DISABLED
)
btn_stop_all.pack(side="right", padx=10)

# Window close event protocol
root.protocol("WM_DELETE_WINDOW", on_closing)

# Run GUI application
root.mainloop()