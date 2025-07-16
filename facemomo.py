import tkinter as tk
import cv2
import face_recognition
import numpy as np
import threading
import signal
import os
import sys
from datetime import datetime
import pygame
import time

# Ctrl+C handler
def signal_handler(sig, frame):
    print("\n🛑 Exit requested. Closing FaceMomo...")
    stop_scanning()
    app.quit()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Paths
KNOWN_FOLDER = "known_faces"
UNKNOWN_FOLDER = "logs/unknown_faces"
LOG_FILE = os.path.join(UNKNOWN_FOLDER, "logs.txt")
ALARM_SOUND = "police_alarm.wav"

os.makedirs(UNKNOWN_FOLDER, exist_ok=True)

# Init alarm
pygame.mixer.init()
alarm = pygame.mixer.Sound(ALARM_SOUND) if os.path.exists(ALARM_SOUND) else None

# GUI Setup
app = tk.Tk()
app.title("😎 FaceMomo - Real-Time Face Detector")
app.configure(bg="black")
app.geometry("900x550")
app.resizable(True, True)

# Entry (not used for now)
entry = tk.Entry(app, width=70, bg="white", fg="black", relief=tk.FLAT)
entry.pack(pady=5)

# Output box
output = tk.Text(app, width=110, height=25, bg="black", fg="lightgreen", relief=tk.FLAT, bd=0)
output.pack(padx=10, pady=5)

# Button frame
button_frame = tk.Frame(app, bg="black")
button_frame.pack(pady=5)

def log_message(msg):
    output.insert(tk.END, msg + "\n")
    output.see(tk.END)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")

# Load known faces
known_encodings = []
known_names = []

def load_known_faces():
    for filename in os.listdir(KNOWN_FOLDER):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            path = os.path.join(KNOWN_FOLDER, filename)
            img = face_recognition.load_image_file(path)
            encodings = face_recognition.face_encodings(img)
            if encodings:
                known_encodings.append(encodings[0])
                known_names.append(os.path.splitext(filename)[0])
    log_message(f"✅ Loaded {len(known_encodings)} known faces.")

# Flags and memory
scanning = False
last_saved_time = 0
cooldown_seconds = 5

detected_known_encodings = []
detected_unknown_encodings = []

def is_new_face(face_encoding, detected_list, tolerance=0.5):
    return not any(face_recognition.compare_faces([enc], face_encoding, tolerance=tolerance)[0] for enc in detected_list)

def start_scanning():
    global scanning
    scanning = True
    thread = threading.Thread(target=run_face_detection)
    thread.start()

def stop_scanning():
    global scanning
    scanning = False

def run_face_detection():
    global last_saved_time
    log_message("🟢 Starting webcam...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        log_message("❌ Failed to open webcam.")
        return

    while scanning:
        ret, frame = cap.read()
        if not ret:
            log_message("⚠️ Failed to read frame.")
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb)
        face_encodings = face_recognition.face_encodings(rgb, face_locations)

        for face_encoding, face_location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
            name = "Unknown"

            if True in matches:
                index = matches.index(True)
                if is_new_face(face_encoding, detected_known_encodings):
                    name = known_names[index]
                    detected_known_encodings.append(face_encoding)
                    log_message(f"😀 Known face detected: {name}")
            else:
                if is_new_face(face_encoding, detected_unknown_encodings):
                    current_time = time.time()
                    if current_time - last_saved_time >= cooldown_seconds:
                        top, right, bottom, left = face_location
                        face_image = frame[top:bottom, left:right]
                        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        filename = f"unknown_face_{timestamp}.jpg"
                        save_path = os.path.join(UNKNOWN_FOLDER, filename)
                        cv2.imwrite(save_path, face_image)

                        if alarm:
                            pygame.mixer.Sound.play(alarm)

                        log_message(f"🚨 Unknown face at {timestamp} → saved: {filename}")
                        detected_unknown_encodings.append(face_encoding)
                        last_saved_time = current_time

        app.update_idletasks()
        app.update()

    cap.release()
    log_message("📴 Webcam stopped.")

# Load knowns
load_known_faces()

# Buttons side by side
start_button = tk.Button(button_frame, text="▶️ Start Scan", command=start_scanning, bg="green", fg="white", width=20)
start_button.grid(row=0, column=0, padx=10)

stop_button = tk.Button(button_frame, text="⏹️ Stop Scan", command=stop_scanning, bg="red", fg="white", width=20)
stop_button.grid(row=0, column=1, padx=10)

# GUI start
try:
    app.mainloop()
except KeyboardInterrupt:
    signal_handler(None, None)
