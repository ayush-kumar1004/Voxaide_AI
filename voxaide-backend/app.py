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
import requests


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

# Parse and format the service account key (replace escaped newlines if present)
try:
    key_dict = json.loads(firebase_key_json)
    if "private_key" in key_dict:
        key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")
except Exception as parse_err:
    raise Exception(f"[ERROR] Failed to parse credentials JSON: {parse_err}")

# Set up local key file for Firebase authentication
os.makedirs("keys", exist_ok=True)
key_file_path = os.path.abspath("keys/voxaide-service-account.json")
with open(key_file_path, "w") as f:
    json.dump(key_dict, f, indent=2)

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

# -------------------- DATABASE TOOLS FOR GEMINI --------------------
def get_order_details(order_id: str, email: str) -> str:
    """
    Retrieves the details and tracking information of a customer's order from the Firestore database.
    
    Args:
        order_id: The unique ID of the order (e.g., ZMT1003).
        email: The email address of the customer associated with the order.
    """
    try:
        doc = db.collection("orders").document(order_id).get()
        if not doc.exists:
            return json.dumps({"error": f"Order {order_id} not found."})
        
        data = doc.to_dict()
        # Verify ownership
        if data.get("customer_email") != email:
            return json.dumps({"error": "Access denied. Order email mismatch."})
            
        return json.dumps({
            "order_id": data.get("order_id"),
            "status": data.get("status"),
            "items": data.get("items"),
            "total": data.get("total"),
            "carrier": data.get("carrier"),
            "tracking_number": data.get("tracking_number"),
            "estimated_delivery": data.get("estimated_delivery")
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to retrieve order details: {str(e)}"})

def cancel_order(order_id: str, email: str, reason: str) -> str:
    """
    Cancels a customer's order in the Firestore database if it is not already shipped or delivered.
    
    Args:
        order_id: The unique ID of the order to cancel (e.g., ZMT1003).
        email: The email address of the customer associated with the order.
        reason: The reason why the order is being cancelled.
    """
    try:
        doc_ref = db.collection("orders").document(order_id)
        doc = doc_ref.get()
        if not doc.exists:
            return json.dumps({"error": f"Order {order_id} not found."})
        
        data = doc.to_dict()
        # Verify ownership
        if data.get("customer_email") != email:
            return json.dumps({"error": "Access denied. Order email mismatch."})
            
        status = data.get("status")
        if status in ["Shipped", "Delivered"]:
            return json.dumps({"error": f"Order {order_id} cannot be cancelled because it is already '{status}'."})
            
        if status == "Cancelled":
            return json.dumps({"success": True, "message": f"Order {order_id} is already cancelled."})
            
        # Update status to Cancelled
        doc_ref.update({
            "status": "Cancelled",
            "cancellation_reason": reason,
            "cancelled_at": datetime.utcnow().strftime('%d %B %Y at %H:%M:%S UTC')
        })
        return json.dumps({"success": True, "message": f"Order {order_id} has been cancelled successfully."})
    except Exception as e:
        return json.dumps({"error": f"Failed to cancel order: {str(e)}"})

# Initialize model with tool functions registered
generative_model = genai.GenerativeModel(
    "gemini-2.5-flash",
    tools=[get_order_details, cancel_order]
)


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


def synthesize_speech(text: str, lang_code: str, filepath: str):
    """
    Synthesizes speech from text. Tries to use ElevenLabs if API key is present,
    otherwise falls back to gTTS.
    """
    elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY")
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel default voice
    
    if elevenlabs_key:
        print("[Voxaide Backend] Synthesizing speech with ElevenLabs...")
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "xi-api-key": elevenlabs_key,
                "Content-Type": "application/json",
                "accept": "audio/mpeg"
            }
            payload = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(response.content)
                print("[Voxaide Backend] ElevenLabs synthesis successful!")
                return True
            else:
                print(f"[Voxaide Backend] ElevenLabs failed with status {response.status_code}: {response.text}")
        except Exception as e:
            print(f"[Voxaide Backend] ElevenLabs exception: {str(e)}")
            
    print("[Voxaide Backend] Falling back to gTTS...")
    try:
        tts = gTTS(text=text, lang=lang_code)
        tts.save(filepath)
        print("[Voxaide Backend] gTTS synthesis successful!")
        return True
    except Exception as e:
        print(f"[Voxaide Backend] gTTS failed: {str(e)}")
        return False


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
        email = request.form.get("email", "")
        
        # 1. Feed audio directly to Gemini 2.5 Flash
        audio_payload = {
            "mime_type": "audio/wav",
            "data": audio_bytes
        }
        prompt = f"""
        You are Voxaide, a smart voice-enabled customer service AI assistant.
        Listen to the customer's audio input.
        First, transcribe exactly what the customer said.
        Second, generate a friendly, helpful, and concise response to the customer's query.
        
        Language Behavior:
        Automatically detect the language used by the customer. If they speak Hindi or mixed Hindi-English (Hinglish), respond in natural Hindi.
        
        Active Customer Context:
        * Active customer email: '{email}'
        
        Database Integration Guidelines:
        * If they ask about orders (status, details, cancellation, tracking), use the appropriate tool.
        * You MUST pass the active customer email '{email}' as the 'email' parameter to the tools.
        * If the email is empty or not provided, verbally ask the customer for their email address and order number, then do NOT call any tools yet (return a response saying you need this information).
        
        Return your answer as a JSON object with exactly three fields:
        {{
          "transcription": "...",
          "response": "...",
          "language": "en" or "hi"
        }}
        Do not include markdown code block formatting (like ```json) in your reply. Return ONLY raw JSON text.
        """
        
        # Start a chat session to enable automatic function calling/tool execution
        chat = generative_model.start_chat(enable_automatic_function_calling=True)
        gemini_response = chat.send_message([prompt, audio_payload])
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
            lang_code = data.get("language", "en")
        except Exception as parse_err:
            print("Failed to parse Gemini response as JSON:", response_text, str(parse_err))
            transcription = "Voice message"
            ai_reply = response_text
            lang_code = "en"
        
        # 2. Convert Gemini's text response to speech using ElevenLabs (with gTTS fallback)
        os.makedirs("static/audio", exist_ok=True)
        filename = f"response_{uuid.uuid4().hex}.mp3"
        filepath = os.path.join("static", "audio", filename)
        synthesize_speech(ai_reply, lang_code, filepath)
        
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
