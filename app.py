import os
import mysql.connector
import streamlit as st
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from streamlit_option_menu import option_menu
from PIL import Image
import numpy as np
from hashlib import sha256
from datetime import datetime
import pandas as pd
import plotly.express as px
import time

# Konfigurasi halaman
st.set_page_config(
    page_title="Sistem Deteksi Kerusakan Bangunan",
    page_icon="🏠",
    layout="wide"
)

# Konfigurasi database
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "user_management"
}

# Path model AI
MODEL_PATH = os.path.join(os.getcwd(), "model", "model_klasifikasirumah.h5")

# Fungsi koneksi database
def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        st.error(f"Koneksi ke database gagal: {err}")
        return None

# Fungsi hash password
def hash_password(password):
    return sha256(password.encode()).hexdigest()

# Fungsi untuk register pengguna
def register_user(email, password):
    conn = get_connection()
    if conn is None:
        return False
    cursor = conn.cursor()
    try:
        hashed_password = hash_password(password)
        cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, hashed_password))
        conn.commit()
        return True
    except mysql.connector.Error as err:
        st.error(f"Error menyimpan data: {err}")
        return False
    finally:
        cursor.close()
        conn.close()

# Fungsi untuk login pengguna
def login_user(email, password):
    conn = get_connection()
    if conn is None:
        return False
    cursor = conn.cursor(dictionary=True)
    try:
        hashed_password = hash_password(password)
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, hashed_password))
        user = cursor.fetchone()
        return user is not None
    except mysql.connector.Error as err:
        st.error(f"Error mengambil data: {err}")
        return False
    finally:
        cursor.close()
        conn.close()

# Fungsi memuat model AI
@st.cache_resource
def load_ai_model(model_path):
    try:
        return load_model(model_path)
    except Exception as e:
        st.error(f"Gagal memuat model AI: {e}")
        return None

# Fungsi prediksi kerusakan
def predict_image(model, image):
    try:
        img = image.resize((128, 128))
        img_array = img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        predictions = model.predict(img_array)
        predicted_index = np.argmax(predictions)
        confidence = predictions[0][predicted_index] * 100
        label = ["Rusak Berat", "Rusak Menengah", "Rusak Ringan"][predicted_index]
        return label, confidence
    except Exception as e:
        st.error(f"Error saat prediksi: {e}")
        return None, None

# Fungsi untuk menyimpan riwayat deteksi
def save_to_history(email, label, confidence, timestamp):
    conn = get_connection()
    if conn is None:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO detections (email, label, confidence, timestamp) VALUES (%s, %s, %s, %s)",
                       (email, label, confidence, timestamp))
        conn.commit()
        return True
    except mysql.connector.Error as err:
        st.error(f"Error menyimpan data deteksi: {err}")
        return False
    finally:
        cursor.close()
        conn.close()

# Halaman register
def register_page():
    st.title("🔐 Daftar Akun Baru")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Konfirmasi Password", type="password")
    if st.button("Daftar"):
        if not email or not password or not confirm_password:
            st.error("Semua kolom harus diisi!")
        elif password != confirm_password:
            st.error("Password dan konfirmasi password tidak sama!")
        elif register_user(email, password):
            st.success("Pendaftaran berhasil! Silakan login.")
            st.session_state["page"] = "login"

# Halaman login
def login_page():
    st.title("🏠 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if login_user(email, password):
            st.session_state["logged_in"] = True
            st.session_state["email"] = email
            st.session_state["page"] = "main_app"
        else:
            st.error("Email atau password salah!")
    if st.button("Belum punya akun? Daftar di sini"):
        st.session_state["page"] = "register"

# Halaman utama aplikasi
def main_app(model):
    with st.sidebar:
        selected = option_menu(
            menu_title="Navigasi",
            options=["Beranda", "Deteksi", "Riwayat", "Statistik", "Tentang", "Logout"],
            icons=["house", "camera", "clock-history", "bar-chart", "info-circle", "door-closed"],
            menu_icon="menu-up",
            default_index=0,
        )

    if selected == "Beranda":
        st.title("🏠 Sistem Deteksi Kerusakan Bangunan")
        st.markdown("""
        Selamat datang di **Sistem Deteksi Kerusakan Bangunan**. Aplikasi ini dirancang untuk membantu Anda 
        menganalisis tingkat kerusakan bangunan berdasarkan foto yang diunggah. 
        """)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("🔍 **Deteksi Akurat**\nSistem ini memberikan hasil deteksi yang tepat untuk setiap kondisi bangunan.")
        with col2:
            st.info("⚡ **Proses Cepat**\nAnalisis cepat untuk membantu pengambilan keputusan tanpa menunggu lama.")
        with col3:
            st.info("📊 **Laporan Lengkap**\nMenyediakan laporan deteksi kerusakan lengkap")

    elif selected == "Deteksi":
        st.title("🔍 Deteksi Kerusakan Bangunan")
        uploaded_files = st.file_uploader("Upload Foto Bangunan", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        if uploaded_files:
            for uploaded_file in uploaded_files:
                image = Image.open(uploaded_file)
                st.image(image, caption=f"Gambar yang diunggah: {uploaded_file.name}", use_container_width=True)
                with st.spinner(f"Memproses gambar {uploaded_file.name}..."):
                    label, confidence = predict_image(model, image)
                    time.sleep(2)
                if label:
                    st.success(f"Hasil Deteksi: **{label}** ({confidence:.2f}% kepercayaan) untuk gambar {uploaded_file.name}")
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    save_to_history(st.session_state["email"], label, confidence, timestamp)
                    st.balloons()

    elif selected == "Riwayat":
        st.title("📜 Riwayat Deteksi")
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM detections WHERE email = %s ORDER BY timestamp DESC", (st.session_state["email"],))
            results = cursor.fetchall()
            conn.close()
            if results:
                for item in results:
                    with st.expander(f"{item['timestamp']} - {item['label']}"):
                        st.write(f"Hasil Deteksi: **{item['label']}**")
                        st.write(f"Tingkat Kepercayaan: **{item['confidence']:.2f}%**")
            else:
                st.info("Belum ada riwayat deteksi.")
        else:
            st.error("Gagal mengambil data riwayat dari database.")

    elif selected == "Statistik":
        st.title("📊 Statistik Deteksi")
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT label, confidence FROM detections WHERE email = %s", (st.session_state["email"],))
            results = cursor.fetchall()
            conn.close()
            if results:
                df = pd.DataFrame(results)
                st.subheader("Distribusi Deteksi")
                fig = px.pie(df, names="label", title="Distribusi Kategori Kerusakan")
                st.plotly_chart(fig)
                st.subheader("Rata-rata Tingkat Kepercayaan per Kategori")
                avg_confidence = df.groupby('label')['confidence'].mean().reset_index()
                fig = px.bar(avg_confidence, x='label', y='confidence', title='Rata-rata Tingkat Kepercayaan per Kategori')
                st.plotly_chart(fig)
            else:
                st.info("Belum ada data statistik.")
        else:
            st.error("Gagal mengambil data statistik dari database.")

    elif selected == "Tentang":
        st.title("📖 Tentang")
        st.markdown("""
        **Sistem Deteksi Kerusakan Bangunan** adalah aplikasi yang dirancang untuk membantu
        pengguna mendeteksi tingkat kerusakan bangunan dari foto yang diunggah. 
        yang dirancang untuk membantu pengguna mendeteksi tingkat kerusakan bangunan dari foto yang diunggah. 
        Tujuan utama aplikasi ini adalah untuk memberikan hasil yang cepat, akurat, dan efisien 
        dalam mendukung penilaian kondisi bangunan.
        """)
        st.markdown("### **Komponen Pendukung Aplikasi**")
        st.write("- **Deep Learning** untuk mendeteksi tingkat kerusakan bangunan.")
        st.write("- **Framework TensorFlow/Keras** untuk memproses dan menganalisis data gambar.")
        st.write("- **Streamlit** untuk antarmuka pengguna berbasis web.")
        st.write("- **MySQL** untuk menyimpan data pengguna dan riwayat deteksi.")
        st.markdown("### **Fitur Utama**")
        st.write("- 🚀 Deteksi kerusakan dalam tiga kategori: **Rusak Berat**, **Rusak Menengah**, dan **Rusak Ringan**.")
        st.write("- 📜 Menyimpan dan menampilkan riwayat deteksi")
        st.write("- 📊 Menampilkan statistik deteksi")
        st.markdown("### **Pengembang**")
        st.write("""
        Sistem ini dikembangkan oleh **Nabila Mumtaz** dan **Tasyfia Farhah Subrina Lubis** sebagai bagian dari 
        proyek magang di **BPK RI**.""")

    elif selected == "Logout":
        st.session_state["logged_in"] = False
        st.session_state["page"] = "login"

# Inisialisasi session state
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "login"

# Load model
model = load_ai_model(MODEL_PATH)

# Routing Halaman
if st.session_state["logged_in"]:
    main_app(model)
elif st.session_state["page"] == "register":
    register_page()
else:
    login_page()
