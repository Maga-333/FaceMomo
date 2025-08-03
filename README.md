# 📸 FaceMomo Lite

**Soft on style, strong on security** – Real-time face recognition with known/unknown alerting, email notification, and optional alarm sound.

---

## 🚀 Quick Start

> Follow these steps to clone and launch FaceMomo with zero errors.  
> Tested and refined for *smooth setup experience* 💡.

---

### 📦 Step 1: Clone the Repository

```bash
git clone https://github.com/YourUsername/facemomo.git
cd facemomo

🧪 Step 2: Create Virtual Environment (Recommended)

python3 -m venv .venv
source .venv/bin/activate

📥 Step 3: Install All Required Libraries

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Or install manually if needed:
pip install opencv-python
pip install dlib
pip install face_recognition
pip install git+https://github.com/ageitgey/face_recognition_models

⚠️ Note:
The first time you install face_recognition_models, it will download pre-trained model files.
Depending on your internet, this may take a few minutes ⏳ – please wait patiently.

🛠️ Step 4: Prepare Folders

Ensure these folders exist in the root directory:

    known_faces/ → for known person face images (.jpg, .png)

    logs/unknown_faces/ → auto-saves new unknown face captures

You can add images like:

known_faces/
├── image1.jpg

▶️ Step 5: Run FaceMomo

python3 facemomo.py

Select camera(s) and alert email(s) using the GUI popups.
