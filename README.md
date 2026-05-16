# 🚀 Free AI Converter — Premium Python Backend

This is the high-performance, **100% Free & Local** Python backend for the Free AI Converter platform. It handles complex file conversions, AI image processing, and PDF manipulations without ever sending data to the cloud.

## ✨ Key Features
- **Premium PDF ↔ Excel**: Intelligent coordinate-based extraction with multi-row header support.
- **High-Fidelity AI Upscaler**: Local neural network models (FSRCNN) for image enhancement.
- **PDF ↔ Word**: Formatting-preserved conversion using native OS engines.
- **Zero API Costs**: No Google, Adobe, or AWS APIs required. Everything runs on your CPU.
- **Privacy First**: No user data is ever stored or transmitted externally.

---

## 🛠️ Installation & Setup

### 1. Prerequisites
- **Python 3.10+** installed.
- **Microsoft Office** (Optional, recommended for highest fidelity Word/Excel conversions on Windows).

### 2. Clone & Install
```bash
# Clone this repository
git clone https://github.com/your-username/free-ai-backend.git
cd free-ai-backend

# Create a virtual environment
python -m venv venv

# Activate the environment
# On Windows:
.\venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Server
```bash
python app.py
```
The backend will start at `http://localhost:5000`.

---

## 🔗 How to Integrate with the Frontend

To connect your Next.js frontend to this backend, follow these steps:

1. **Open the Frontend Project**: Go to your Next.js project directory.
2. **Locate the API Config**: Open the file `src/lib/api.ts`.
3. **Update the Base URL**:
   - If running **locally**, ensure it is set to:
     ```typescript
     const API_URL = 'http://localhost:5000';
     ```
   - If **deployed** (e.g., on Render/Railway), change it to your live URL:
     ```typescript
     const API_URL = 'https://your-backend-service.onrender.com';
     ```

---

## 🚀 Deployment Tips

### Deploying to Render / Railway / Heroku:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn -k gevent -w 4 app:app` (or use the included `Procfile`).
- **Environment Variables**:
  - `PORT`: 5000
  - `FLASK_ENV`: production

---

## 🛡️ Security
This backend includes built-in:
- **Rate Limiting**: Prevents API abuse.
- **CORS Protection**: Ensures only your frontend can call the API.
- **Secure File Handling**: Uses temporary directories that are wiped after conversion.

## 📄 License
This project is licensed under the MIT License.
