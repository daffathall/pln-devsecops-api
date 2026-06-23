from flask import Flask, jsonify, request

app = Flask(__name__)

# Simulasi token per pelanggan
# Di dunia nyata ini dari database
VALID_TOKENS = {
    "token-budi-001": 1,   # token milik Budi → hanya bisa akses id 1
    "token-siti-002": 2,   # token milik Siti → hanya bisa akses id 2
    "token-agus-003": 3,   # token milik Agus → hanya bisa akses id 3
    "token-admin-999": None # admin → bisa akses semua
}

pelanggan = [
    {"id": 1, "nama": "Budi Santoso", "tarif": "R1", "tagihan": 150000},
    {"id": 2, "nama": "Siti Rahayu", "tarif": "R2", "tagihan": 320000},
    {"id": 3, "nama": "Agus Wijaya", "tarif": "B1", "tagihan": 875000},
]

def get_token():
    # Ambil token dari header request
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.split(" ")[1]
    return None

@app.route('/')
def home():
    return jsonify({"message": "PLN API berjalan!", "version": "2.0"})

@app.route('/pelanggan')
def get_pelanggan():
    token = get_token()
    
    # Cek token valid
    if token not in VALID_TOKENS:
        return jsonify({"error": "Unauthorized - token tidak valid"}), 401
    
    # Admin bisa lihat semua
    if VALID_TOKENS[token] is None:
        return jsonify(pelanggan)
    
    # Pelanggan biasa hanya lihat datanya sendiri
    id_berhak = VALID_TOKENS[token]
    data = next((p for p in pelanggan if p["id"] == id_berhak), None)
    return jsonify([data])

@app.route('/pelanggan/<int:id>')
def get_pelanggan_by_id(id):
    token = get_token()
    
    # Cek token valid
    if token not in VALID_TOKENS:
        return jsonify({"error": "Unauthorized - token tidak valid"}), 401
    
    # Cek apakah berhak akses id ini
    id_berhak = VALID_TOKENS[token]
    if id_berhak is not None and id_berhak != id:
        return jsonify({"error": "Forbidden - kamu tidak berhak akses data ini"}), 403
    
    data = next((p for p in pelanggan if p["id"] == id), None)
    if data:
        return jsonify(data)
    return jsonify({"error": "Pelanggan tidak ditemukan"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)