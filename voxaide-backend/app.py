from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from flask_cors import CORS
from firebase_admin import credentials, firestore, initialize_app
from firestore import db
from utils import hash_password, check_password
from datetime import datetime
print("🚀 Starting backend...")

app = Flask(__name__)
CORS(app, origins=["http://localhost:8080"])  # ✅ Allow frontend
cred = credentials.Certificate("keys/voxaide-a16c10119181.json")  # ✅ Replace with your file name
initialize_app(cred)
db = firestore.client()


# -------------------- SIGNUP --------------------
@app.route('/api/signup', methods=['POST'])
@cross_origin(origin='http://localhost:8080')
def signup():
    try:
        data = request.get_json()
        print("🟢 Received JSON:", data)

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
            print("🔴 Missing fields:", missing_fields)
            return jsonify({
                'message': 'Missing required fields',
                'missingFields': missing_fields
            }), 400

        # Check if user already exists
        user_query = db.collection('users').where('email', '==', email).limit(1).get()
        if user_query:
            print(f"⚠️ User with email {email} already exists")
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

        print(f"✅ User {email} registered successfully.")
        return jsonify({'message': 'User registered successfully'}), 200

    except Exception as e:
        print("🔥 Error in /api/signup:", str(e))
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


if __name__ == '__main__':
    app.run(debug=True)
