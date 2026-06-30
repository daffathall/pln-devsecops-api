from flask import Flask, jsonify, request
import jwt
import datetime
import sqlite3
import os
import logging
from dotenv import load_dotenv
from database import init_db

load_dotenv()

app = Flask(__name__)
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-key-ganti-ini")

# ✅ Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security.log'),  # simpan ke file
        logging.StreamHandler()               # tampil di terminal
    ]
)
logger = logging.getLogger(__name__)

init_db()

USERS = {
    "budi":  {"password": "pass123", "id": 1,    "role": "pelanggan"},
    "siti":  {"password": "pass456", "id": 2,    "role": "pelanggan"},
    "agus":  {"password": "pass789", "id": 3,    "role": "pelanggan"},
    "admin": {"password": "admin99", "id": None, "role": "admin"},
}

def get_ip():
    return request.remote_addr

def get_token():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.split(" ")[1]
    return None

def verify_token():
    token = get_token()
    if not token:
        logger.warning(f"[UNAUTHORIZED] Akses tanpa token - IP: {get_ip()} - URL: {request.path}")
        return None, jsonify({"error": "Unauthorized - token tidak ada"}), 401
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload, None, None
    except jwt.ExpiredSignatureError:
        logger.warning(f"[EXPIRED TOKEN] IP: {get_ip()} - URL: {request.path}")
        return None, jsonify({"error": "Token expired, login lagi"}), 401
    except jwt.InvalidTokenError:
        logger.warning(f"[INVALID TOKEN] IP: {get_ip()} - URL: {request.path}")
        return None, jsonify({"error": "Token tidak valid"}), 401

@app.route('/')
def home():
    return jsonify({"message": "PLN API berjalan!", "version": "5.0"})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    user = USERS.get(username)

    if not user or user["password"] != password:
        # ✅ Catat login gagal
        logger.warning(f"[LOGIN GAGAL] Username: {username} - IP: {get_ip()}")
        return jsonify({"error": "Username atau password salah"}), 401

    # ✅ Catat login berhasil
    logger.info(f"[LOGIN BERHASIL] Username: {username} - IP: {get_ip()}")

    payload = {
        "username": username,
        "id": user["id"],
        "role": user["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return jsonify({"token": token, "expires_in": "1 jam"})

@app.route('/cari')
def cari_pelanggan():
    payload, error, code = verify_token()
    if error:
        return error, code

    if payload["role"] != "admin":
        logger.warning(f"[FORBIDDEN] User {payload['username']} coba akses /cari - IP: {get_ip()}")
        return jsonify({"error": "Forbidden"}), 403

    nama = request.args.get("nama", "")

    # ✅ Deteksi input mencurigakan
    karakter_berbahaya = ["'", '"', ";", "--", "OR", "DROP", "SELECT"]
    if any(k.lower() in nama.lower() for k in karakter_berbahaya):
        logger.critical(f"[SQL INJECTION ATTEMPT] Input: '{nama}' - IP: {get_ip()} - User: {payload['username']}")
        return jsonify({"error": "Input tidak valid"}), 400

    conn = sqlite3.connect('pln.db')
    c = conn.cursor()
    c.execute("SELECT * FROM pelanggan WHERE nama LIKE ?", (f'%{nama}%',))
    rows = c.fetchall()
    conn.close()

    logger.info(f"[SEARCH] User: {payload['username']} - Keyword: '{nama}' - IP: {get_ip()}")

    if not rows:
        return jsonify({"message": "Data tidak ditemukan"}), 404

    hasil = [{"id": r[0], "nama": r[1], "tarif": r[2], "tagihan": r[3]} for r in rows]
    return jsonify(hasil)

@app.route('/pelanggan')
def get_pelanggan():
    payload, error, code = verify_token()
    if error:
        return error, code

    logger.info(f"[AKSES] User: {payload['username']} - /pelanggan - IP: {get_ip()}")

    conn = sqlite3.connect('pln.db')
    c = conn.cursor()
    if payload["role"] == "admin":
        c.execute("SELECT * FROM pelanggan")
    else:
        c.execute("SELECT * FROM pelanggan WHERE id = ?", (payload["id"],))
    rows = c.fetchall()
    conn.close()

    hasil = [{"id": r[0], "nama": r[1], "tarif": r[2], "tagihan": r[3]} for r in rows]
    return jsonify(hasil)

@app.route('/pelanggan/<int:id>')
def get_pelanggan_by_id(id):
    payload, error, code = verify_token()
    if error:
        return error, code

    if payload["role"] != "admin" and payload["id"] != id:
        logger.warning(f"[FORBIDDEN] User {payload['username']} coba akses data id={id} - IP: {get_ip()}")
        return jsonify({"error": "Forbidden"}), 403

    logger.info(f"[AKSES] User: {payload['username']} - /pelanggan/{id} - IP: {get_ip()}")

    conn = sqlite3.connect('pln.db')
    c = conn.cursor()
    c.execute("SELECT * FROM pelanggan WHERE id = ?", (id,))
    row = c.fetchone()
    conn.close()

    if row:
        return jsonify({"id": row[0], "nama": row[1], "tarif": row[2], "tagihan": row[3]})
    return jsonify({"error": "Tidak ditemukan"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)