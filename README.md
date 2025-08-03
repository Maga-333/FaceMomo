# 📸 FaceMomo - Soft on Style, Strong on Security

FaceMomo is a smart face-recognition-based alert system that:

- 📷 Detects known vs unknown faces in real-time  
- 🔊 Plays alert sounds when intruders are found  
- 🧠 Uses face encoding for recognition  
- 📁 Logs images of unknown visitors  
- 🖼️ Shows GUI or terminal results instantly  

---

# 🔧 How to Install

## 1. Clone the repository

git clone https://github.com/Maga-333/FaceMomo.git

## 2. Navigate into the project directory

cd FaceMomo

## 3. Create a Python virtual environment

python3 -m venv .venv

## 4. Activate the virtual environment

source .venv/bin/activate

## 5. Install all required libraries

pip install -r requirements.txt

## 6. Upgrade pip and install all required libraries

pip install --upgrade pip setuptools wheel

pip install opencv-python

pip install dlib

pip install face_recognition

pip install git+https://github.com/ageitgey/face_recognition_models

## 7. Change Email & Password in facemomo.py

    ✅ Open the file:

nano facemomo.py

or use your preferred editor like VS Code.

## 8. 🔍 Find the section with email settings — It will look similar to this:

EMAIL_SENDER = "youremail@example.com"

EMAIL_PASSWORD = "yourpassword"

## 9. ✏️ Update the values:
Replace the dummy emails and password with your real ones (preferably use a secure app-specific password if using Gmail).

Example:

EMAIL_SENDER = "facemomo@gmail.com"

EMAIL_PASSWORD = "your_app_specific_password"

    ⚠️ Important: If you're using Gmail, you must enable 2-step verification and use an App Password. Do not use your actual login password.

💾 Save the file and exit.

## 10. Start the FaceMomo alert system

python3 facemomo.py

## 11. To deactivate the virtual environment

deactivate

👨‍💻 Developed 💛 by LNT
