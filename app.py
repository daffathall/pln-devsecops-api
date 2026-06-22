from flask import Flask, jsonify

app = Flask(__name__)

# Data dummy pelanggan PLN
pelanggan = [
    {"id": 1, "nama": "Budi Santoso", "tarif": "R1", "tagihan": 150000},
    {"id": 2, "nama": "Siti Rahayu", "tarif": "R2", "tagihan": 320000},
    {"id": 3, "nama": "Agus Wijaya", "tarif": "B1", "tagihan": 875000},
]

@app.route('/')
def home():
    return jsonify({"message": "PLN API berjalan!", "version": "1.0"})

@app.route('/pelanggan')
def get_pelanggan():
    return jsonify(pelanggan)

@app.route('/pelanggan/<int:id>')
def get_pelanggan_by_id(id):
    data = next((p for p in pelanggan if p["id"] == id), None)
    if data:
        return jsonify(data)
    return jsonify({"error": "Pelanggan tidak ditemukan"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)