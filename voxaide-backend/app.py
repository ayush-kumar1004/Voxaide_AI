from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from firebase_admin import credentials, firestore, initialize_app
from utils import hash_password, check_password
from datetime import datetime
import os
import json
from dotenv import load_dotenv
import uuid

# Gemini API & gTTS imports
import google.generativeai as genai
from gtts import gTTS

load_dotenv()
print("[Voxaide Backend] Starting backend...")

app = Flask(__name__)
# Enable CORS globally for all frontend origins
CORS(app, resources={r"/*": {"origins": [
    "http://localhost:5173",
    "http://localhost:8080",
    "https://voxaide.web.app",
    "https://voxaide-main.vercel.app"
]}})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "version": "2.0.0-gemini-gtts"}), 200


firebase_key_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if not firebase_key_json:
    raise Exception("[ERROR] Environment variable for Firebase credentials not set!")

# Set up local key file for Firebase authentication
os.makedirs("keys", exist_ok=True)
key_file_path = os.path.abspath("keys/voxaide-service-account.json")
with open(key_file_path, "w") as f:
    f.write(firebase_key_json)

# Unset GOOGLE_APPLICATION_CREDENTIALS to prevent standard Google client libraries
# from trying to use the Firebase service account key for the Gemini API.
if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
    del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

cred = credentials.Certificate(key_file_path)
initialize_app(cred)
db = firestore.client()

# Initialize Gemini SDK
gemini_api_key = os.environ.get("GEMINI_API_KEY")
if not gemini_api_key:
    raise Exception("[ERROR] GEMINI_API_KEY environment variable not set! Set it in Render dashboard.")
genai.configure(api_key=gemini_api_key)
generative_model = genai.GenerativeModel("gemini-2.5-flash")


# -------------------- SIGNUP --------------------
@app.route('/api/signup', methods=['POST'])
@cross_origin(origin='http://localhost:8080')
def signup():
    try:
        data = request.get_json()
        print("[Signup] Received JSON:", data)

        if not data:
            return jsonify({'message': 'No data received'}), 400

        # Extract fields with exact frontend keys
        first_name = data.get("firstName")
        last_name = data.get("lastName")
        email = data.get("email")
        company_name = data.get("company")
        password = data.get("password")

        # Check for missing fields
        missing_fields = []
        if not first_name: missing_fields.append("firstName")
        if not last_name: missing_fields.append("lastName")
        if not email: missing_fields.append("email")
        if not company_name: missing_fields.append("company")
        if not password: missing_fields.append("password")

        if missing_fields:
            print("[Signup] Missing fields:", missing_fields)
            return jsonify({
                'message': 'Missing required fields',
                'missingFields': missing_fields
            }), 400

        # Check if user already exists
        user_query = db.collection('users').where('email', '==', email).limit(1).get()
        if user_query:
            print(f"[Signup] User with email {email} already exists")
            return jsonify({'message': 'User already exists'}), 409

        # Add new user
        db.collection('users').add({
            'firstName': first_name,
            'lastName': last_name,
            'email': email,
            'companyName': company_name,
            'password': password,  # NOTE: You should hash this in production!
            'createdAt': datetime.now().strftime('%d %B %Y at %H:%M:%S UTC+5:30')
        })

        print(f"[Signup] User {email} registered successfully.")
        return jsonify({'message': 'User registered successfully'}), 200

    except Exception as e:
        print("[Signup] Error in /api/signup:", str(e))
        return jsonify({'message': 'Signup failed', 'error': str(e)}), 500

# -------------------- LOGIN --------------------
@app.route('/api/login', methods=['POST'])
@cross_origin(origin='http://localhost:8080')
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not all([email, password]):
        return jsonify({"error": "Email and password required"}), 400

    users_ref = db.collection('users')
    users = users_ref.where('email', '==', email).get()
    if not users:
        return jsonify({"error": "User not found"}), 404

    user_data = users[0].to_dict()
    if user_data["password"] != password:
        return jsonify({"error": "Incorrect password"}), 401

    return jsonify({"message": "Login successful", "user": user_data}), 200

# -------------------- CONTACT FORM --------------------
@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.get_json()

    contact_data = {
        'fullName': data.get('fullName'),
        'email': data.get('email'),
        'company': data.get('company'),
        'inquiryType': data.get('inquiryType'),
        'message': data.get('message'),
        'createdAt': datetime.utcnow()
    }

    db.collection('contacts').add(contact_data)
    return jsonify({'success': True, 'message': 'Message received. We’ll get back to you soon.'})


# -------------------- CUSTOMER CHAT VOICE SUPPORT --------------------
@app.route('/talk', methods=['POST'])
def talk():
    try:
        # Check if the post request has the file part
        if 'audio' not in request.files:
            return jsonify({'message': 'No audio file received'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'message': 'No selected file'}), 400

        audio_bytes = audio_file.read()
        
        # 1. Feed audio directly to Gemini 2.5 Flash
        audio_payload = {
            "mime_type": "audio/wav",
            "data": audio_bytes
        }
        prompt = """
        You are Voxaide, a smart voice-enabled customer service AI assistant.
        Listen to the customer's audio input.
        First, transcribe exactly what the customer said.
        Second, generate a friendly, helpful, and concise response to the customer's query.
        Return your answer as a JSON object with exactly two fields:
        {
          "transcription": "...",
          "response": "..."
        }
        Do not include markdown code block formatting (like ```json) in your reply. Return ONLY raw JSON text.
        """
        
        gemini_response = generative_model.generate_content([prompt, audio_payload])
        response_text = gemini_response.text.strip()
        
        # Parse the JSON response
        try:
            # Strip markdown block quotes if Gemini returns them
            if response_text.startswith("```"):
                lines = response_text.splitlines()
                if lines[0].startswith("```json"):
                    response_text = "\n".join(lines[1:-1])
                elif lines[0].startswith("```"):
                    response_text = "\n".join(lines[1:-1])
            data = json.loads(response_text)
            transcription = data.get("transcription", "")
            ai_reply = data.get("response", "")
        except Exception as parse_err:
            print("Failed to parse Gemini response as JSON:", response_text, str(parse_err))
            transcription = "Voice message"
            ai_reply = response_text
        
        # 2. Convert Gemini's text response to speech using gTTS
        tts = gTTS(text=ai_reply, lang='en')
        
        # Save output MP3 file to static/audio directory
        os.makedirs("static/audio", exist_ok=True)
        filename = f"response_{uuid.uuid4().hex}.mp3"
        filepath = os.path.join("static", "audio", filename)
        tts.save(filepath)
        
        # Construct the audio URL dynamically based on request host
        audio_url = f"{request.host_url}static/audio/{filename}"
        
        return jsonify({
            'user_message': transcription,
            'response': ai_reply,
            'audio_url': audio_url
        }), 200
        
    except Exception as e:
        print("[Talk] Error in /talk:", str(e))
        return jsonify({'message': 'Processing failed', 'error': str(e)}), 500


@app.route('/reset', methods=['POST'])
def reset_session():
    # Stub response for resetting conversation session
    return jsonify({'success': True, 'message': 'Session reset successfully.'}), 200


if __name__ == '__main__':
    app.run(debug=True)
