from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from PIL import Image
from hashlib import sha256
import mysql.connector
import numpy as np
import os
import datetime
import logging

# Inisialisasi Flask
app = Flask(__name__)

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)

# Konfigurasi database
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "user_management"
}

# Path ke model TensorFlow
MODEL_PATH = os.path.join(os.getcwd(), "model", "model_klasifikasirumah.h5")

# Load model TensorFlow
try:
    model = load_model(MODEL_PATH)
    logging.info("Model berhasil dimuat.")
except Exception as e:
    logging.error(f"Error saat memuat model: {e}")
    model = None

# Label kategori kerusakan
LABELS = ["Rusak Berat", "Rusak Menengah", "Rusak Ringan"]

# Direktori sementara untuk file yang diunggah
TEMP_DIR = os.path.join(os.getcwd(), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# Fungsi koneksi database
def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        logging.error(f"Koneksi ke database gagal: {err}")
        return None

# Fungsi hash password
def hash_password(password):
    return sha256(password.encode()).hexdigest()

# Fungsi prediksi gambar
def predict_image(image_path):
    try:
        img = Image.open(image_path).resize((128, 128))
        img_array = img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        predictions = model.predict(img_array)
        predicted_index = np.argmax(predictions)
        confidence = predictions[0][predicted_index] * 100
        label = LABELS[predicted_index]
        return label, confidence
    except Exception as e:
        logging.error(f"Error saat prediksi: {e}")
        return None, None

# Endpoint: Home (dokumentasi API)
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "Selamat datang di API Sistem Deteksi Kerusakan Bangunan",
        "endpoints": {
            "/register": "POST - Registrasi pengguna baru",
            "/login": "POST - Login pengguna",
            "/predict": "POST - Prediksi kerusakan berdasarkan gambar",
            "/history": "GET - Lihat riwayat deteksi pengguna",
            "/stats": "GET - Statistik deteksi kerusakan"
        }
    })

# Endpoint: Register pengguna baru
@app.route('/register', methods=['POST'])
def register_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email dan password harus diisi"}), 400

    hashed_password = hash_password(password)
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, hashed_password))
            conn.commit()
            return jsonify({"message": "Pendaftaran berhasil"}), 201
        except mysql.connector.Error as err:
            return jsonify({"error": f"Gagal menyimpan data: {err}"}), 500
        finally:
            cursor.close()
            conn.close()
    else:
        return jsonify({"error": "Koneksi database gagal"}), 500

# Endpoint: Login pengguna
@app.route('/login', methods=['POST'])
def login_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email dan password harus diisi"}), 400

    hashed_password = hash_password(password)
    conn = get_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, hashed_password))
            user = cursor.fetchone()
            if user:
                return jsonify({"message": "Login berhasil"}), 200
            else:
                return jsonify({"error": "Email atau password salah"}), 401
        finally:
            cursor.close()
            conn.close()
    else:
        return jsonify({"error": "Koneksi database gagal"}), 500

# Endpoint: Prediksi gambar
@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        logging.error("Key 'file' tidak ditemukan di request.files")
        return jsonify({"error": "Tidak ada file yang diunggah"}), 400

    file = request.files['file']
    email = request.form.get('email')

    if not email:
        return jsonify({"error": "Email harus disertakan"}), 400

    if file.filename == '':
        return jsonify({"error": "Nama file kosong"}), 400

    if not file.content_type.startswith('image/'):
        return jsonify({"error": "File bukan gambar"}), 400

    file_path = os.path.join(TEMP_DIR, file.filename)
    try:
        file.save(file_path)
        logging.info(f"File berhasil disimpan di {file_path}")
        label, confidence = predict_image(file_path)
        if label is None:
            raise Exception("Gagal memproses gambar")

        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO detections (email, label, confidence, timestamp) VALUES (%s, %s, %s, %s)",
                           (email, label, confidence, timestamp))
            conn.commit()
            cursor.close()
            conn.close()

        return jsonify({
            "label": label,
            "confidence": round(confidence, 2)
        }), 200
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# Endpoint: Riwayat deteksi
@app.route('/history', methods=['GET'])
def get_history():
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "Email harus disertakan"}), 400

    conn = get_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM detections WHERE email = %s ORDER BY timestamp DESC", (email,))
            results = cursor.fetchall()
            return jsonify(results), 200
        finally:
            cursor.close()
            conn.close()
    else:
        return jsonify({"error": "Koneksi database gagal"}), 500

# Endpoint: Statistik deteksi
@app.route('/stats', methods=['GET'])
def get_stats():
    conn = get_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT label, COUNT(*) AS count FROM detections GROUP BY label")
            stats = cursor.fetchall()
            return jsonify(stats), 200
        finally:
            cursor.close()
            conn.close()
    else:
        return jsonify({"error": "Koneksi database gagal"}), 500

# Jalankan aplikasi Flask
if __name__ == '__main__':
    if model is None:
        logging.error("Gagal memulai API karena model tidak dimuat.")
    else:
        app.run(debug=True)
