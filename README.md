# 🧠 Voxaide – AI-Powered Customer Service Assistant

Voxaide is an intelligent, voice-enabled customer service assistant that allows companies to automate support using conversational AI. Built using **Firebase**, **React**, **Python (Flask)**, and **Google Cloud services**, Voxaide provides a seamless voice-based experience, reducing human workload and response time.

---

## 🚀 Live Demo
- 🌐 Frontend: [https://voxaide.web.app](https://voxaide.web.app)
- 🖥️ Backend: [https://voxaide-ai.onrender.com](https://voxaide-ai.onrender.com)

---

## ✨ Features
- ✅ **User Signup/Login** with Firebase Authentication
- 🗣️ Smart Voice Support using **Google Cloud Vertex AI**
- 🗂️ Company-specific Dataset Integration (order support, FAQs, etc.)
- 📞 **Twilio Voice Call Integration**
- 🌍 Multilingual Support *(in-progress)*
- 📝 Contact Form that saves queries to **Firestore**
- 🔒 Secure & Scalable Architecture via **Firebase & Render**

---

## 🧑‍💻 Tech Stack

| Layer         | Tech                                               |
| ------------- | -------------------------------------------------- |
| **Frontend**  | React + TypeScript + Vite                          |
| **Backend**   | Python Flask (REST API)                            |
| **Database**  | Firebase Firestore                                 |
| **Auth**      | Firebase Authentication                           |
| **Hosting**   | Firebase Hosting + Render (backend)                |
| **AI Engine** | Google Cloud Vertex AI (Gemini) + Google Cloud TTS |

---

## 📂 Project Structure
```bash
voxaide-main/
 ├── public/               # Firebase hosting root
 ├── dist/                 # Built frontend assets
 ├── voxaide-backend/      # Flask backend with Firestore integration
 │    ├── app.py
 │    └── .env
 ├── src/                  # React frontend code
 │    ├── components/
 │    └── pages/
 ├── firebase.json
 ├── firestore.rules
 └── README.md
