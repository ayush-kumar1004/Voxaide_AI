🤖 Voxaide – AI-Powered Customer Service Assistant
Voxaide is an intelligent, voice-enabled customer service assistant that allows companies to automate support using conversational AI. Built using Firebase, React, Python (Flask), and Google Cloud services, Voxaide provides a seamless voice-based experience, reducing human workload and response time.


🚀 Live Demo
🌐 Frontend: https://voxaide.web.app
🧠 Backend: https://voxaide-ai.onrender.com

🎯 Features
✅ User Signup/Login with Firebase Authentication

🧠 Smart Voice Support using Google Cloud Vertex AI

📂 Company-specific Dataset Integration (order support, FAQs, etc.)

📞 Twilio Voice Call Integration

🌍 Multilingual Support (in-progress)

📧 Contact Form that saves queries to Firestore

🔒 Secure & Scalable Architecture via Firebase & Render

🛠️ Tech Stack
Layer	Tech
Frontend	React + TypeScript + Vite
Backend	Python Flask (REST API)
Database	Firebase Firestore
Auth	Firebase Authentication
Hosting	Firebase Hosting + Render (backend)
AI Engine	Google Cloud Vertex AI (Gemini)
Voice I/O	Google Cloud Speech + TTS

📂 Project Structure
bash
Copy
Edit
voxaide-main/
├── public/                # Firebase hosting root
├── dist/                  # Built frontend assets
├── voxaide-backend/       # Flask backend with Firestore integration
│   └── app.py
│   └── .env
├── src/                   # React frontend code
│   └── components/
│   └── pages/
├── firebase.json
├── firestore.rules
├── README.md
⚙️ Setup Instructions
🔧 Prerequisites
Node.js

Python 3.10+

Firebase CLI (npm install -g firebase-tools)

Google Cloud project with Vertex AI, Firestore, and STT/TTS enabled

Render.com or similar Python web hosting platform

💻 Frontend Setup
bash
Copy
Edit
cd voxaide-main
npm install
npm run dev   # Development
npm run build # For production
firebase deploy # Deploy frontend to Firebase Hosting
🧪 Backend Setup (Local or Render)
bash
Copy
Edit
cd voxaide-backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py
Make sure your .env file contains:

env
Copy
Edit
GOOGLE_APPLICATION_CREDENTIALS_JSON={...your firebase admin SDK JSON stringified...}
💬 Sample Use Cases
AI Customer Support for Startups

Order Resolution via Voice

Lead Generation via Contact Forms

AI Escalation to Human Agents

🤝 Contributing
Open to PRs for additional features like:

Chat history UI

Admin dashboard

Live human chat fallback

Language localization

📜 License
MIT License
