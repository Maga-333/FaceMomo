import os import cv2 import face_recognition import pickle import datetime import smtplib import imghdr from email.message import EmailMessage

=== CONFIG ===

KNOWN_FACES_DIR = "known_faces" ENCODINGS_FILE = "face_encodings.pkl" LOGS_DIR = "logs" UNKNOWN_DIR = "logs/unknown_faces" LOG_FILE = os.path.join(LOGS_DIR, "log.txt") ALERT_EMAIL = "youremail@example.com"   # Replace with your email ALERT_PASSWORD = "yourpassword"         # Replace with your email password RECEIVER_EMAIL = "receiver@example.com" # Where to send alerts

=== ENCODING KNOWN FACES ===

def encode_faces(): encodings = [] names = []

for filename in os.listdir(KNOWN_FACES_DIR):
    if filename.endswith(('.jpg', '.jpeg', '.png')):
        path = os.path.join(KNOWN_FACES_DIR, filename)
        image = face_recognition.load_image_file(path)
        try:
            encoding = face_recognition.face_encodings(image)[0]
            encodings.append(encoding)
            names.append(os.path.splitext(filename)[0])
            print(f"[ENCODED] {filename}")
        except IndexError:
            print(f"[WARNING] No face found in {filename}")

with open(ENCODINGS_FILE, "wb") as f:
    pickle.dump((encodings, names), f)
print("[INFO] All faces encoded and saved.")

=== LOAD ENCODINGS ===

def load_encodings(): with open(ENCODINGS_FILE, "rb") as f: return pickle.load(f)

=== SETUP LOGGING ===

def setup_logging(): os.makedirs(LOGS_DIR, exist_ok=True) os.makedirs(UNKNOWN_DIR, exist_ok=True) return open(LOG_FILE, "a")

=== EMAIL ALERT ===

def send_email_alert(image_path, timestamp): msg = EmailMessage() msg["Subject"] = f"Unknown Face Detected @ {timestamp}" msg["From"] = ALERT_EMAIL msg["To"] = RECEIVER_EMAIL msg.set_content("An unknown face was detected by FaceGuard. See attached image.")

with open(image_path, 'rb') as f:
    img_data = f.read()
    img_type = imghdr.what(f.name)
    msg.add_attachment(img_data, maintype='image', subtype=img_type, filename=os.path.basename(f.name))

try:
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(ALERT_EMAIL, ALERT_PASSWORD)
        smtp.send_message(msg)
    print("[EMAIL] Alert sent successfully.")
except Exception as e:
    print(f"[EMAIL ERROR] {e}")

=== START FACEGUARD ===

def start_faceguard(): print("[INFO] Starting FaceGuard... Press 'q' to exit.")

known_face_encodings, known_face_names = load_encodings()
video_capture = cv2.VideoCapture(0)
log_file = setup_logging()

while True:
    ret, frame = video_capture.read()
    if not ret:
        print("[ERROR] Failed to capture frame")
        break

    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small = small_frame[:, :, ::-1]

    face_locations = face_recognition.face_locations(rgb_small)
    face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"

        if True in matches:
            match_index = matches.index(True)
            name = known_face_names[match_index]

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"{timestamp} - {name}\n")
        log_file.flush()

        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        if name == "Unknown":
            filename = f"unknown_{timestamp.replace(':', '-')}.jpg"
            filepath = os.path.join(UNKNOWN_DIR, filename)
            cv2.imwrite(filepath, frame)
            send_email_alert(filepath, timestamp)

    cv2.imshow("🛡️ FaceGuard", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()
log_file.close()
print("[INFO] FaceGuard Stopped.")

=== MAIN ===

def main(): if not os.path.exists(ENCODINGS_FILE): encode_faces() start_faceguard()

if name == "main": main()
  
