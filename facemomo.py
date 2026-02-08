import tkinter as tk
import threading
import customtkinter as ctk
from tkinter import messagebox, filedialog, simpledialog
from PIL import Image, ImageTk
import cv2
import face_recognition
import numpy as np
import signal
import os
import sys
from datetime import datetime
import pygame
import time
import smtplib
from email.message import EmailMessage

ctk.set_appearance_mode("dark")  # Overall dark mode
ctk.set_default_color_theme("blue")

# ==== Config ====
KNOWN_FOLDER = "known_faces"
UNKNOWN_FOLDER = "logs/unknown_faces"
ALARM_SOUND = "police_alarm.wav"
EMAIL_SENDER = "facemomoalert@gmail.com"
EMAIL_PASSWORD = "favkyryhuxbqwasp"

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

# ==== Face Scan Logic ====
scanning = False
cooldown = 5
last_saved = {}
known_detected_global = []
unknown_detected_global = []

def is_new_face(face_encoding, detected_list):
    return not any(face_recognition.compare_faces([enc], face_encoding, tolerance=0.5)[0] for enc in detected_list)

def run_camera(cam_ip, log_callback, progress_callback, status_callback):
    while scanning:
        ret, frame = cap.read()
        if not ret:
            log_callback(f"⚠️ Frame error from {cam_ip}")
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
                if is_new_face(encoding, known_detected_global):
                    known_detected_global.append(encoding)
                    log_callback(f"✅ Known face '{name}' on {cam_ip}", "green")
                    status_callback("green")
                    for email in email_list:
                        send_email(email, f"📸 KNOWN FACE DETECTED: {name}", f"{name} seen at {timestamp} on {cam_ip}")
            else:
                if is_new_face(encoding, unknown_detected_global):
                    if time.time() - last_saved.get(cam_ip, 0) >= cooldown:
                        top, right, bottom, left = [v * 4 for v in loc]
                        face_img = frame[top:bottom, left:right]
                        filename = f"{str(cam_ip).replace(':','_').replace('/','_')}_unknown_{timestamp}.jpg"
                        save_path = os.path.join(UNKNOWN_FOLDER, filename)
                        cv2.imwrite(save_path, face_img)

                        status_callback("red")
                        if alarm:
                            pygame.mixer.Sound.play(alarm)

                        for email in email_list:
                            send_email(email, "🚨 UNKNOWN FACE ALERT", f"A stranger was seen on {cam_ip} at {timestamp}", save_path)

                        log_callback(f"🚨 Unknown face @ {cam_ip} → emailed & saved", "red")
                        unknown_detected_global.append(encoding)
                        last_saved[cam_ip] = time.time()

        progress_callback(50)

    cap.release()
    log_callback(f"📴 Camera {cam_ip} disconnected.")

# ================= CUTE & PROFESSIONAL GUI ================= #
class FaceMomoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📷 FaceMomo Lite - Face Alert")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        self.cute_font = ("Comic Sans MS", 14)
        self.prof_font = ("Arial", 12)
        self.scanning = False
        self.camera_list = []
        self.email_list = []
        self.caps = []  # To hold camera captures for continuation
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(root, width=250, corner_radius=15)
        self.sidebar.pack(side="left", fill="y", padx=15, pady=15)
        
        # Logo
        try:
            logo_img = Image.open("logo.png").resize((120, 120))
            self.logo = ImageTk.PhotoImage(logo_img)
            logo_label = ctk.CTkLabel(self.sidebar, image=self.logo, text="")
            logo_label.pack(pady=15)
        except:
            pass
        
        # Sidebar Buttons
        self.start_button = ctk.CTkButton(self.sidebar, text="▶️ Start Scan 😄", command=self.start_scan, fg_color="green", hover_color="lightgreen", corner_radius=25, font=self.cute_font)
        self.start_button.pack(pady=15)
        
        self.stop_button = ctk.CTkButton(self.sidebar, text="⏹️ Stop Scan", command=self.stop_scan, fg_color="red", hover_color="darkred", corner_radius=25, font=self.cute_font, state="disabled")
        self.stop_button.pack(pady=15)
        
        self.continue_button = ctk.CTkButton(self.sidebar, text="▶️ Continue Scanning", command=self.continue_scan, fg_color="blue", hover_color="lightblue", corner_radius=25, font=self.cute_font, state="disabled")
        self.continue_button.pack(pady=15)
        
        self.clear_button = ctk.CTkButton(self.sidebar, text="🧹 Clear Logs", command=self.clear_logs, fg_color="orange", corner_radius=25, font=self.cute_font)
        self.clear_button.pack(pady=15)
        
        self.export_button = ctk.CTkButton(self.sidebar, text="💾 Export Logs", command=self.export_logs, fg_color="blue", corner_radius=25, font=self.cute_font)
        self.export_button.pack(pady=15)
        
        self.exit_button = ctk.CTkButton(self.sidebar, text="👋 Exit 😘", command=self.exit_app, fg_color="red", hover_color="pink", corner_radius=25, font=self.cute_font)
        self.exit_button.pack(pady=15)
        
        # Main Frame
        self.main_frame = ctk.CTkFrame(root, corner_radius=15)
        self.main_frame.pack(side="right", fill="both", expand=True, padx=15, pady=15)
        
        # Tabs
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Results Tab (Full Light Mode)
        self.results_tab = self.tabview.add("📊 Scan Results & Logs")
        self.results_text = tk.Text(self.results_tab, wrap="word", font=self.prof_font, bg="white", fg="black", relief="flat", padx=10, pady=10)
        self.results_text.pack(fill="both", expand=True, padx=15, pady=15)
        # Configure tags for light mode
        self.results_text.tag_config("green", foreground="darkgreen")
        self.results_text.tag_config("red", foreground="darkred")
        self.results_text.tag_config("info", foreground="blue")
        
        # Progress & Status
        self.progress = ctk.CTkProgressBar(self.main_frame, width=700, corner_radius=15)
        self.progress.pack(pady=15)
        self.progress.set(0)
        
        self.status_label = ctk.CTkLabel(self.main_frame, text="Ready to scan! 🐶", font=self.cute_font)
        self.status_label.pack(pady=10)
        
        # Spinner
        self.spinner = ctk.CTkLabel(self.main_frame, text="⏳", font=("Arial", 24))
        self.spinner.pack(pady=10)
        self.spinner.pack_forget()
        
        load_known_faces()
        self.get_initial_inputs()  # Auto-get inputs and start
        self.start_scan()
    
    def get_initial_inputs(self):
        self.camera_list.clear()
        self.email_list.clear()
        
        while True:
            try:
                cam_count = int(simpledialog.askstring("Cameras", "How many cameras (0 for webcam)?"))
                break
            except:
                messagebox.showerror("Invalid", "❌ Invalid number of cameras")
                continue
        
        for i in range(cam_count):
            cam_ip = simpledialog.askstring("Camera IP", f"Enter IP or '0' for webcam of Camera {i+1}")
            if cam_ip:
                if cam_ip == '0':
                    self.camera_list.append(0)
                else:
                    if not cam_ip.endswith("/video"):
                        cam_ip = cam_ip.rstrip('/') + "/video"
                    self.camera_list.append(cam_ip)
        
        while True:
            try:
                mail_count = int(simpledialog.askstring("Emails", "How many email addresses for alerts?"))
                break
            except:
                messagebox.showerror("Invalid", "❌ Invalid number of emails")
                continue
        
        for j in range(mail_count):
            mail = simpledialog.askstring("Email", f"Enter Email ID {j+1}")
            if mail:
                self.email_list.append(mail)
    
    def log(self, message, tag="info"):
        self.results_text.insert("end", f"{message}\n", tag)
        self.results_text.see("end")
    
    def update_progress(self, value):
        self.progress.set(value / 100)
    
    def flash_status(self, color):
        original = self.root.cget("bg")
        self.root.configure(bg=color)
        self.root.update()
        time.sleep(0.2)
        self.root.configure(bg=original)
        self.root.update()
    
    def start_scan(self):
        if self.scanning:
            messagebox.showwarning("Scanning", "Already scanning! 😅")
            return
        if not self.camera_list:
            messagebox.showerror("No Cameras", "No cameras configured! 😟")
            return
        self.scanning = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.continue_button.configure(state="disabled")
        self.status_label.configure(text="Scanning started... 🔍")
        self.spinner.pack(pady=10)
        self.caps = []
        for cam_ip in self.camera_list:
            cap = cv2.VideoCapture(0 if cam_ip == 0 else str(cam_ip))
            if cap.isOpened():
                self.caps.append(cap)
                threading.Thread(target=self.run_camera_thread, args=(cap, cam_ip), daemon=True).start()
            else:
                self.log(f"❌ Failed to open {cam_ip}")
    
    def run_camera_thread(self, cap, cam_ip):
        while self.scanning:
            ret, frame = cap.read()
            if not ret:
                self.log(f"⚠️ Frame error from {cam_ip}")
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
                    if is_new_face(encoding, known_detected_global):
                        known_detected_global.append(encoding)
                        self.log(f"✅ Known face '{name}' on {cam_ip}", "green")
                        self.flash_status("green")
                        for email in self.email_list:
                            send_email(email, f"📸 KNOWN FACE DETECTED: {name}", f"{name} seen at {timestamp} on {cam_ip}")
                else:
                    if is_new_face(encoding, unknown_detected_global):
                        if time.time() - last_saved.get(cam_ip, 0) >= cooldown:
                            top, right, bottom, left = [v * 4 for v in loc]
                            face_img = frame[top:bottom, left:right]
                            filename = f"{str(cam_ip).replace(':','_').replace('/','_')}_unknown_{timestamp}.jpg"
                            save_path = os.path.join(UNKNOWN_FOLDER, filename)
                            cv2.imwrite(save_path, face_img)
                            
                            self.flash_status("red")
                            if alarm:
                                pygame.mixer.Sound.play(alarm)
                            
                            for email in self.email_list:
                                send_email(email, "🚨 UNKNOWN FACE ALERT", f"A stranger was seen on {cam_ip} at {timestamp}", save_path)
                            
                            self.log(f"🚨 Unknown face @ {cam_ip} → emailed & saved", "red")
                            unknown_detected_global.append(encoding)
                            last_saved[cam_ip] = time.time()
            
            self.update_progress(50)
        
        cap.release()
        self.log(f"📴 Camera {cam_ip} disconnected.")
    
    def stop_scan(self):
        self.scanning = False
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.continue_button.configure(state="normal")
        self.status_label.configure(text="Scanning stopped! 🛑")
        self.spinner.pack_forget()
    
    def continue_scan(self):
        if self.scanning:
            messagebox.showwarning("Scanning", "Already scanning! 😅")
            return
        self.scanning = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.continue_button.configure(state="disabled")
        self.status_label.configure(text="Continuing scan... 🔄")
        self.spinner.pack(pady=10)
        for cap, cam_ip in zip(self.caps, self.camera_list):
            if cap.isOpened():
                threading.Thread(target=self.run_camera_thread, args=(cap, cam_ip), daemon=True).start()
            else:
                cap = cv2.VideoCapture(0 if cam_ip == 0 else str(cam_ip))
                if cap.isOpened():
                    self.caps.append(cap)
                    threading.Thread(target=self.run_camera_thread, args=(cap, cam_ip), daemon=True).start()
                else:
                    self.log(f"❌ Failed to reopen {cam_ip}")
    
    def clear_logs(self):
        self.results_text.delete(1.0, tk.END)
        self.progress.set(0)
        self.status_label.configure(text="Logs cleared! 🧹")
    
    def export_logs(self):
        content = self.results_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("No Logs", "No logs to export! 😟")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "w") as f:
                f.write(content)
            messagebox.showinfo("Exported", "Logs exported! 📄")
    
    def exit_app(self):
        self.scanning = False
        for cap in self.caps:
            cap.release()
        self.root.quit()

# ================= MAIN ================= #
if __name__ == "__main__":
    root = ctk.CTk()
    app = FaceMomoGUI(root)
    root.mainloop()
