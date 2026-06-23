from flask import Flask, jsonify, request
import jwt
import datetime

app = Flask(__name__)

# Secret key untuk sign token
# Di production ini harus disimpan di environment variable, BUKAN di kode!
SECRET_KEY = "pln-secret-key-2026"

pelanggan = [
    {"id": 1, "nama": "Budi Santoso", "tarif": "R1", "tagihan": 150000},
    {"id": 2, "nama": "Siti Rahayu", "tarif": "R2", "tagihan": 320000},
    {"id": 3, "nama": "Agus Wijaya", "tarif": "B1", "tagihan": 875000},
]

# Simulasi database user
USERS = {
    "budi":  {"password": "pass123", "id": 1,    "role": "pelanggan"},
    "siti":  {"password": "pass456", "id": 2,    "role": "pelanggan"},
    "agus":  {"password": "pass789", "id": 3,    "role": "pelanggan"},
    "admin": {"password": "admin99", "id": None, "role": "admin"},
}

def get_token():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.split(" ")[1]
    return None

def verify_token():
    token = get_token()
    if not token:
        return None, jsonify({"error": "Unauthorized - token tidak ada"}), 401
    try:
        # Decode & verifikasi token (cek signature + expiry otomatis)
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload, None, None
    except jwt.ExpiredSignatureError:
        return None, jsonify({"error": "Token sudah expired, login lagi"}), 401
    except jwt.InvalidTokenError:
        return None, jsonify({"error": "Token tidak valid"}), 401

@app.route('/')
def home():
    return jsonify({"message": "PLN API berjalan!", "version": "3.0"})

# Endpoint login → dapat JWT token
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = USERS.get(username)
    if not user or user["password"] != password:
        return jsonify({"error": "Username atau password salah"}), 401

    # Buat JWT token dengan expiry 1 jam
    payload = {
        "username": username,
        "id": user["id"],
        "role": user["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return jsonify({"token": token, "expires_in": "1 jam"})

@app.route('/pelanggan')
def get_pelanggan():
    payload, error, code = verify_token()
    if error:
        return error, code

    if payload["role"] == "admin":
        return jsonify(pelanggan)

    id_user = payload["id"]
    data = next((p for p in pelanggan if p["id"] == id_user), None)
    return jsonify([data])

@app.route('/pelanggan/<int:id>')
def get_pelanggan_by_id(id):
    payload, error, code = verify_token()
    if error:
        return error, code

    if payload["role"] != "admin" and payload["id"] != id:
        return jsonify({"error": "Forbidden - kamu tidak berhak akses data ini"}), 403

    data = next((p for p in pelanggan if p["id"] == id), None)
    if data:
        return jsonify(data)
    return jsonify({"error": "Pelanggan tidak ditemukan"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)