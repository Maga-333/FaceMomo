# === FaceMomo Lite: Face Alert – Known vs Unknown ===
# 🛠️ Modified for Wei Wuxi – August 2025

import tkinter as tk
from tkinter import simpledialog
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
import smtplib
from email.message import EmailMessage

# ==== Config ====
KNOWN_FOLDER = "known_faces"
UNKNOWN_FOLDER = "logs/unknown_faces"
ALARM_SOUND = "police_alarm.wav"
EMAIL_SENDER = "facemomoalert@gmail.com"       # ✅ Your sender Gmail
EMAIL_PASSWORD = "favkyryhuxbqwasp "       # ✅ App password from https://myaccount.google.com/apppasswords

# ==== Setup ====
os.makedirs(UNKNOWN_FOLDER, exist_ok=True)
pygame.mixer.init()
alarm = pygame.mixer.Sound(ALARM_SOUND) if os.path.exists(ALARM_SOUND) else None
known_encodings, known_names = [], []

# ==== Load Known Faces ====
def load_known_faces():
    known_encodings.clear()
    known_names.clear()
    for filename in os.listdir(KNOWN_FOLDER):
        if filename.lower().endswith(('.jpg', '.png', '.jpeg')):
            path = os.path.join(KNOWN_FOLDER, filename)
            img = face_recognition.load_image_file(path)
            enc = face_recognition.face_encodings(img)
            if enc:
                known_encodings.append(enc[0])
                known_names.append(os.path.splitext(filename)[0])

# ==== Email Sender ====
def send_email(to_email, subject, body, image_path=None):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = to_email
    msg.set_content(body)
    if image_path and os.path.exists(image_path):
        with open(image_path, 'rb') as f:
            img_data = f.read()
            msg.add_attachment(img_data, maintype='image', subtype='jpeg', filename=os.path.basename(image_path))
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print(f"❌ Email failed: {e}")

# ==== GUI Setup ====
app = tk.Tk()
app.title("📷 FaceMomo Lite")
app.configure(bg="black")
app.geometry("1000x650")

output = tk.Text(app, width=120, height=30, bg="black", fg="lightgreen", relief=tk.FLAT)
output.pack(pady=5)

def log(msg):
    output.insert(tk.END, msg + "\n")
    output.see(tk.END)

def flash_alert(color="red", duration=0.2):
    original = app['bg']
    app['bg'] = color
    app.update()
    time.sleep(duration)
    app['bg'] = original
    app.update()

# ==== Input Section ====
camera_list = []
email_list = []

def get_inputs():
    camera_list.clear()
    email_list.clear()

    while True:
        try:
            cam_count = int(simpledialog.askstring("Cameras", "How many cameras (0 for webcam)?"))
            break
        except:
            log("❌ Invalid number of cameras")
            continue

    for i in range(cam_count):
        cam_ip = simpledialog.askstring("Camera IP", f"Enter IP or '0' for webcam of Camera {i+1}")
        if cam_ip:
            if cam_ip == '0':
                camera_list.append(0)
            else:
                if not cam_ip.endswith("/video"):
                    cam_ip = cam_ip.rstrip('/') + "/video"
                camera_list.append(cam_ip)

    while True:
        try:
            mail_count = int(simpledialog.askstring("Emails", "How many email addresses for alerts?"))
            break
        except:
            log("❌ Invalid number of emails")
            continue

    for j in range(mail_count):
        mail = simpledialog.askstring("Email", f"Enter Email ID {j+1}")
        if mail:
            email_list.append(mail)

# ==== Face Scan ====
scanning = True
cooldown = 5
last_saved = {}

def is_new_face(face_encoding, detected_list):
    return not any(face_recognition.compare_faces([enc], face_encoding, tolerance=0.5)[0] for enc in detected_list)

def start_scan():
    load_known_faces()
    get_inputs()
    for cam_ip in camera_list:
        threading.Thread(target=run_camera, args=(cam_ip,), daemon=True).start()

def run_camera(cam_ip):
    known_detected = []
    unknown_detected = []

    log(f"🎥 Connecting to camera: {cam_ip}")
    cap = cv2.VideoCapture(0 if cam_ip == 0 else str(cam_ip))
    if not cap.isOpened():
        log(f"❌ Failed to open {cam_ip}")
        return

    while scanning:
        ret, frame = cap.read()
        if not ret:
            log(f"⚠️ Frame error from {cam_ip}")
            break

        small_rgb = cv2.cvtColor(cv2.resize(frame, (0, 0), fx=0.25, fy=0.25), cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(small_rgb)
        face_encodings = face_recognition.face_encodings(small_rgb, face_locations)

        for encoding, loc in zip(face_encodings, face_locations):
            name = "Unknown"
            matches = face_recognition.compare_faces(known_encodings, encoding)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            if True in matches:
                index = matches.index(True)
                name = known_names[index]
                if is_new_face(encoding, known_detected):
                    known_detected.append(encoding)
                    log(f"✅ Known face '{name}' on {cam_ip}")
                    flash_alert("green")
                    if alarm:
                        pygame.mixer.Sound.play(alarm)
                    for email in email_list:
                        send_email(email, f"📸 KNOWN FACE DETECTED: {name}", f"{name} seen at {timestamp} on {cam_ip}")
            else:
                if is_new_face(encoding, unknown_detected):
                    if time.time() - last_saved.get(cam_ip, 0) >= cooldown:
                        top, right, bottom, left = [v * 4 for v in loc]
                        face_img = frame[top:bottom, left:right]
                        filename = f"{str(cam_ip).replace(':','_').replace('/','_')}_unknown_{timestamp}.jpg"
                        save_path = os.path.join(UNKNOWN_FOLDER, filename)
                        cv2.imwrite(save_path, face_img)

                        flash_alert("red")
                        if alarm:
                            pygame.mixer.Sound.play(alarm)

                        for email in email_list:
                            send_email(email, "🚨 UNKNOWN FACE ALERT", f"A stranger was seen on {cam_ip} at {timestamp}", save_path)

                        log(f"🚨 Unknown face @ {cam_ip} → emailed & saved")
                        unknown_detected.append(encoding)
                        last_saved[cam_ip] = time.time()

        app.update_idletasks()
        app.update()

    cap.release()
    log(f"📴 Camera {cam_ip} disconnected.")

def stop_scan():
    global scanning
    scanning = False
    log("🛑 Scanning stopped.")

# ==== Buttons ====
btn_frame = tk.Frame(app, bg="black")
btn_frame.pack(pady=10)
tk.Button(btn_frame, text="▶️ Start Scan", command=start_scan, bg="green", fg="white", width=25).grid(row=0, column=0, padx=10)
tk.Button(btn_frame, text="⏹️ Stop", command=stop_scan, bg="red", fg="white", width=25).grid(row=0, column=1, padx=10)

# ==== Signal Handling ====
def signal_handler(sig, frame):
    stop_scan()
    app.quit()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

# ==== Launch ====
try:
    app.mainloop()
except KeyboardInterrupt:
    signal_handler(None, None)
