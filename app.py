from flask import Flask, jsonify, request
import jwt
import datetime
import sqlite3
from database import init_db

app = Flask(__name__)
SECRET_KEY = "pln-secret-key-2026"

# Inisialisasi database saat startup
init_db()

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
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload, None, None
    except jwt.ExpiredSignatureError:
        return None, jsonify({"error": "Token expired, login lagi"}), 401
    except jwt.InvalidTokenError:
        return None, jsonify({"error": "Token tidak valid"}), 401

@app.route('/')
def home():
    return jsonify({"message": "PLN API berjalan!", "version": "4.0"})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    user = USERS.get(username)
    if not user or user["password"] != password:
        return jsonify({"error": "Username atau password salah"}), 401
    payload = {
        "username": username,
        "id": user["id"],
        "role": user["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return jsonify({"token": token, "expires_in": "1 jam"})

# ❌ VULNERABLE - SQL Injection!
@app.route('/cari')
def cari_pelanggan():
    payload, error, code = verify_token()
    if error:
        return error, code
    
    if payload["role"] != "admin":
        return jsonify({"error": "Forbidden"}), 403

    nama = request.args.get("nama", "")
    
    conn = sqlite3.connect('pln.db')
    c = conn.cursor()
    
    # ❌ INI BERBAHAYA - string langsung digabung!
    ##query = f"SELECT * FROM pelanggan WHERE nama LIKE '%{nama}%'"
    ## c.execute(query)
    
    #✅ AMAN - gunakan parameterized query
    c.execute("SELECT * FROM pelanggan WHERE nama LIKE ?", (f'%{nama}%',))
    # print(f"Query: {query}")
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        return jsonify({"message": "Data tidak ditemukan"}), 404
    
    hasil = [{"id": r[0], "nama": r[1], "tarif": r[2], "tagihan": r[3]} for r in rows]
    return jsonify(hasil)

@app.route('/pelanggan')
def get_pelanggan():
    payload, error, code = verify_token()
    if error:
        return error, code
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
        return jsonify({"error": "Forbidden"}), 403
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