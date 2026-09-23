import os
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import firebase_admin
from firebase_admin import credentials, firestore
import google.generativeai as genai
from gtts import gTTS
import requests
from dotenv import load_dotenv

load_dotenv()

def create_app():
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
        return jsonify({"status": "healthy", "version": "2.1.0-agent-orchestrator"}), 200

    # Firebase Admin SDK Initialization
    db = None
    firebase_key_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if firebase_key_json and not firebase_admin._apps:
        try:
            key_dict = json.loads(firebase_key_json)
            if "private_key" in key_dict:
                key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")
            
            os.makedirs("keys", exist_ok=True)
            key_file_path = os.path.abspath("keys/voxaide-service-account.json")
            with open(key_file_path, "w") as f:
                json.dump(key_dict, f, indent=2)
            
            if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
                del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

            cred = credentials.Certificate(key_file_path)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
        except Exception as parse_err:
            print(f"[VoxAide Backend] Warning: Firebase init error: {parse_err}")
    elif firebase_admin._apps:
        try:
            db = firestore.client()
        except Exception:
            pass

    # Initialize Gemini SDK if key present
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if gemini_api_key:
        try:
            genai.configure(api_key=gemini_api_key)
        except Exception as e:
            print(f"[VoxAide Backend] Warning: Gemini configure error: {e}")

    # Register Multi-Tenant Core Blueprints
    from app.api.company_routes import company_bp
    from app.api.agent_routes import agent_bp
    from app.api.knowledge_routes import knowledge_bp
    from app.api.appointment_routes import appointment_bp
    from app.api.telephony_routes import telephony_bp
    app.register_blueprint(company_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(knowledge_bp)
    app.register_blueprint(appointment_bp)
    app.register_blueprint(telephony_bp)


    # -------------------- DATABASE TOOLS FOR GEMINI (LEGACY DEMO) --------------------
    def get_order_details(order_id: str, email: str) -> str:
        if not db:
            return json.dumps({"error": "Database not initialized"})
        try:
            doc = db.collection("orders").document(order_id).get()
            if not doc.exists:
                return json.dumps({"error": f"Order {order_id} not found."})
            data = doc.to_dict()
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
        if not db:
            return json.dumps({"error": "Database not initialized"})
        try:
            doc_ref = db.collection("orders").document(order_id)
            doc = doc_ref.get()
            if not doc.exists:
                return json.dumps({"error": f"Order {order_id} not found."})
            data = doc.to_dict()
            if data.get("customer_email") != email:
                return json.dumps({"error": "Access denied. Order email mismatch."})
            status = data.get("status")
            if status in ["Shipped", "Delivered"]:
                return json.dumps({"error": f"Order {order_id} cannot be cancelled because it is already '{status}'."})
            if status == "Cancelled":
                return json.dumps({"success": True, "message": f"Order {order_id} is already cancelled."})
            doc_ref.update({
                "status": "Cancelled",
                "cancellation_reason": reason,
                "cancelled_at": datetime.utcnow().strftime('%d %B %Y at %H:%M:%S UTC')
            })
            return json.dumps({"success": True, "message": f"Order {order_id} has been cancelled successfully."})
        except Exception as e:
            return json.dumps({"error": f"Failed to cancel order: {str(e)}"})

    # -------------------- CONTACT FORM --------------------
    @app.route('/api/contact', methods=['POST'])
    def contact():
        data = request.get_json() or {}
        contact_data = {
            'fullName': data.get('fullName'),
            'email': data.get('email'),
            'company': data.get('company'),
            'inquiryType': data.get('inquiryType'),
            'message': data.get('message'),
            'createdAt': datetime.utcnow()
        }
        if db:
            db.collection('contacts').add(contact_data)
        return jsonify({'success': True, 'message': 'Message received. We’ll get back to you soon.'})

    def synthesize_speech(text: str, lang_code: str, filepath: str):
        elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY")
        voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        if elevenlabs_key:
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
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
                }
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                if response.status_code == 200:
                    with open(filepath, "wb") as f:
                        f.write(response.content)
                    return True
            except Exception:
                pass
        try:
            tts = gTTS(text=text, lang=lang_code)
            tts.save(filepath)
            return True
        except Exception:
            return False

    # -------------------- LEGACY CUSTOMER CHAT VOICE SUPPORT --------------------
    @app.route('/talk', methods=['POST'])
    def talk():
        try:
            if 'audio' not in request.files:
                return jsonify({'message': 'No audio file received'}), 400
            audio_file = request.files['audio']
            if audio_file.filename == '':
                return jsonify({'message': 'No selected file'}), 400

            audio_bytes = audio_file.read()
            email = request.form.get("email", "")

            audio_payload = {
                "mime_type": "audio/wav",
                "data": audio_bytes
            }
            prompt = f"""
            You are Voxaide, a smart voice-enabled customer service AI assistant.
            Listen to the customer's audio input.
            First, transcribe exactly what the customer said.
            Second, generate a friendly, helpful, and concise response to the customer's query.
            Active customer email: '{email}'
            Return raw JSON with: transcription, response, language.
            """
            generative_model = genai.GenerativeModel(
                "gemini-2.5-flash",
                tools=[get_order_details, cancel_order]
            )
            chat = generative_model.start_chat(enable_automatic_function_calling=True)
            gemini_response = chat.send_message([prompt, audio_payload])
            response_text = gemini_response.text.strip()

            try:
                if response_text.startswith("```"):
                    lines = response_text.splitlines()
                    if lines[0].startswith("```json") or lines[0].startswith("```"):
                        response_text = "\n".join(lines[1:-1])
                data = json.loads(response_text)
                transcription = data.get("transcription", "")
                ai_reply = data.get("response", "")
                lang_code = data.get("language", "en")
            except Exception:
                transcription = "Voice message"
                ai_reply = response_text
                lang_code = "en"

            os.makedirs("static/audio", exist_ok=True)
            filename = f"response_{uuid.uuid4().hex}.mp3"
            filepath = os.path.join("static", "audio", filename)
            synthesize_speech(ai_reply, lang_code, filepath)
            audio_url = f"{request.host_url}static/audio/{filename}"

            return jsonify({
                'user_message': transcription,
                'response': ai_reply,
                'audio_url': audio_url
            }), 200
        except Exception as e:
            return jsonify({'message': 'Processing failed', 'error': str(e)}), 500

    @app.route('/reset', methods=['POST'])
    def reset_session():
        return jsonify({'success': True, 'message': 'Session reset successfully.'}), 200

    return app

app = create_app()
