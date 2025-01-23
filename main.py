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
import io
import pandas as pd
import plotly.express as px

# Konfigurasi halaman
st.set_page_config(
    page_title="BRIXFIX - Sistem Deteksi Kerusakan Bangunan",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS untuk styling
def load_css():
    st.markdown("""
        <style>
            /* Main container styling */
            .main > div {
                padding-top: 2rem;
            }
            
            /* Auth container styling */
            .auth-container {
                max-width: 800px;
                margin: 0 auto;
                padding: 2rem;
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            
            /* Form styling */
            .stTextInput > div > div > input {
                border-radius: 5px;
            }
            
            /* Button styling */
            .stButton>button {
                width: 100%;
                border-radius: 5px;
                height: 3rem;
                font-weight: bold;
            }
            
            /* Title styling */
            .title {
                font-size: 2.5rem;
                font-weight: bold;
                text-align: center;
                margin-bottom: 1rem;
            }
            
            .subtitle {
                font-size: 1.2rem;
                text-align: center;
                color: #666;
                margin-bottom: 2rem;
            }
            
            /* Hide Streamlit elements */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .css-1rs6os {visibility: hidden;}
            .css-17zmdxb {display: none;}
            
            /* Card styling */
            .card {
                padding: 1.5rem;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 1rem;
            }
            
            /* Alert styling */
            .alert {
                padding: 1rem;
                border-radius: 5px;
                margin-bottom: 1rem;
            }
            
            .alert-success {
                background-color: #d1e7dd;
                color: #0f5132;
                border: 1px solid #badbcc;
            }
            
            .alert-error {
                background-color: #f8d7da;
                color: #842029;
                border: 1px solid #f5c2c7;
            }
        </style>
    """, unsafe_allow_html=True)

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
        st.error(f"❌ Koneksi ke database gagal: {err}")
        return None

# Fungsi hash password
def hash_password(password):
    return sha256(password.encode()).hexdigest()

# Fungsi validasi email
def is_valid_email(email):
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

# Fungsi untuk register pengguna
def register_user(email, password, confirm_password):
    if not is_valid_email(email):
        return False, "Format email tidak valid!"
    
    if password != confirm_password:
        return False, "Password tidak cocok!"
        
    if len(password) < 6:
        return False, "Password minimal 6 karakter!"
    
    conn = get_connection()
    if conn is None:
        return False, "Koneksi database gagal!"
    
    cursor = conn.cursor()
    try:
        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return False, "Email sudah terdaftar!"
        
        hashed_password = hash_password(password)
        cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, hashed_password))
        conn.commit()
        return True, "Registrasi berhasil!"
    except mysql.connector.Error as err:
        return False, f"Error: {err}"
    finally:
        cursor.close()
        conn.close()

# Fungsi login pengguna
def login_user(email, password):
    if not email or not password:
        return False, "Email dan password harus diisi!"
    
    conn = get_connection()
    if conn is None:
        return False, "Koneksi database gagal!"
    
    cursor = conn.cursor(dictionary=True)
    try:
        hashed_password = hash_password(password)
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, hashed_password))
        user = cursor.fetchone()
        if user:
            return True, "Login berhasil!"
        return False, "Email atau password salah!"
    except mysql.connector.Error as err:
        return False, f"Error: {err}"
    finally:
        cursor.close()
        conn.close()

# Fungsi untuk mendapatkan nomor gambar terakhir
def get_last_image_number(cursor):
    try:
        cursor.execute("SELECT MAX(CAST(SUBSTRING(image_name, 5) AS UNSIGNED)) FROM detections WHERE image_name LIKE 'img_%'")
        result = cursor.fetchone()
        if result and result[0]:
            return result[0]
        return 0
    except mysql.connector.Error:
        return 0

# Fungsi untuk generate nama gambar unik
def generate_unique_image_name(cursor):
    last_number = get_last_image_number(cursor)
    new_number = last_number + 1
    return f"img_{new_number}"

# Fungsi menyimpan riwayat deteksi
def save_detection(email, label, confidence, timestamp, image):
    conn = get_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    try:
        # Generate unique image name
        image_name = generate_unique_image_name(cursor)
        
        # Convert image to PNG format
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_blob = img_byte_arr.getvalue()

        query = """
            INSERT INTO detections (email, label, confidence, timestamp, image_data, image_name)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (email, label, confidence, timestamp, img_blob, image_name))
        conn.commit()
        return True
    except mysql.connector.Error as err:
        st.error(f"❌ Error menyimpan data deteksi: {err}")
        return False
    finally:
        cursor.close()
        conn.close()

# Fungsi mengambil riwayat deteksi
def get_detection_history(email):
    conn = get_connection()
    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, label, confidence, timestamp, image_data, image_name 
            FROM detections 
            WHERE email = %s 
            ORDER BY timestamp DESC
        """, (email,))
        return cursor.fetchall()
    except mysql.connector.Error as err:
        st.error(f"❌ Error mengambil riwayat: {err}")
        return []
    finally:
        cursor.close()
        conn.close()

# Fungsi memuat model AI
@st.cache_resource
def load_ai_model(model_path):
    try:
        return load_model(model_path)
    except Exception as e:
        st.error(f"❌ Gagal memuat model AI: {e}")
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
        label = ["🏚 Rusak Berat", "🏠 Rusak Menengah", "🛠 Rusak Ringan"][predicted_index]
        return label, confidence
    except Exception as e:
        st.error(f"❌ Error saat prediksi: {e}")
        return None, None

# Halaman login
def login_page():
    load_css()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<h1 class="title">BRIXFIX</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Sistem Deteksi Kerusakan Bangunan</p>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown("### 🔐 Login")
            email = st.text_input("📧 Email")
            password = st.text_input("🔑 Password", type="password")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                submit_button = st.form_submit_button("🔓 Login", use_container_width=True)
                if submit_button:
                    success, message = login_user(email, password)
                    if success:
                        st.session_state["logged_in"] = True
                        st.session_state["email"] = email
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            
            with col_btn2:
                register_button = st.form_submit_button("📝 Daftar Akun", use_container_width=True)
                if register_button:
                    st.session_state["show_register"] = True
                    st.rerun()

# Halaman register
def register_page():
    load_css()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<h1 class="title">BRIXFIX</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Sistem Deteksi Kerusakan Bangunan</p>', unsafe_allow_html=True)
        
        with st.form("register_form"):
            st.markdown("### 📋 Register")
            email = st.text_input("📧 Email")
            password = st.text_input("🔑 Password", type="password")
            confirm_password = st.text_input("🔐 Konfirmasi Password", type="password")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                submit_button = st.form_submit_button("📝 Daftar", use_container_width=True)
                if submit_button:
                    success, message = register_user(email, password, confirm_password)
                    if success:
                        st.success(message)
                        st.session_state["show_register"] = False
                        st.rerun()
                    else:
                        st.error(message)
            
            with col_btn2:
                back_button = st.form_submit_button("🔙 Kembali ke Login", use_container_width=True)
                if back_button:
                    st.session_state["show_register"] = False
                    st.rerun()

# Halaman deteksi
def detection_page(model):
    st.title("🔍 Deteksi Kerusakan Bangunan")
    
    with st.container():
        st.markdown("""
        <div class="card">
            <h3>Panduan Penggunaan:</h3>
            <ol>
                <li>Upload foto bangunan yang ingin dianalisis</li>
                <li>Sistem akan memproses gambar secara otomatis</li>
                <li>Hasil deteksi akan ditampilkan beserta tingkat kepercayaan</li>
                <li>Data deteksi akan tersimpan secara otomatis</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
    uploaded_files = st.file_uploader(
        "Upload Foto Bangunan",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            image = Image.open(uploaded_file)
            st.image(image, caption=f"🖼 Gambar yang diunggah: {uploaded_file.name}", use_container_width=True)
            
            with st.spinner(f"⚙ Memproses gambar {uploaded_file.name}..."):
                label, confidence = predict_image(model, image)
                
            if label:
                st.markdown(f"""
                <div class="alert alert-success">
                    ✅ Hasil Deteksi: {label} ({confidence:.2f}% kepercayaan)
                </div>
                """, unsafe_allow_html=True)
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if save_detection(st.session_state["email"], label, confidence, timestamp, image):
                    st.success("📂 Data berhasil disimpan ke database!")
                    st.balloons()

# Halaman riwayat
def history_page():
    st.title("📜 Riwayat Deteksi")
    history = get_detection_history(st.session_state["email"])
    
    if history:
        for item in history:
            with st.expander(f"🕒 {item['timestamp']} - {item['label']} ({item['image_name']})"):
                col1, col2 = st.columns([1, 2])
                with col1:
                    if item['image_data']:
                        img = Image.open(io.BytesIO(item['image_data']))
                        st.image(img, caption=f"🖼 {item['image_name']}")
                with col2:
                    st.markdown(f"""
                    <div class="card">
                        <h4>Tingkat Kepercayaan:</h4>
                        <p>{item['confidence']:.2f}%</p>
                        <h4>Nama File:</h4>
                        <p>{item['image_name']}</p>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("ℹ Belum ada riwayat deteksi.")

# Halaman statistik
def statistics_page():
    st.title("📊 Statistik Deskriptif Deteksi")
    
    conn = get_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT label, confidence FROM detections WHERE email = %s", (st.session_state["email"],))
        results = cursor.fetchall()
        conn.close()
        
        if results:
            df = pd.DataFrame(results)
            
            with st.container():
                st.subheader("Distribusi Deteksi")
                fig = px.pie(
                    df,
                    names="label",
                    title="Distribusi Kategori Kerusakan",
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                    height=500
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("Rata-rata Tingkat Kepercayaan per Kategori")
                avg_confidence = df.groupby('label')['confidence'].mean().reset_index()
                fig = px.bar(
                    avg_confidence,
                    x='label',
                    y='confidence',
                    title='Rata-rata Tingkat Kepercayaan per Kategori',
                    color='label',
                    color_discrete_sequence=px.colors.qualitative.Set2,
                    height=600
                )
                fig.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
                st.plotly_chart(fig, use_container_width=True)

                # Ringkasan statistik
                st.subheader("Ringkasan Statistik")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total_detections = len(df)
                    st.metric("Total Deteksi", total_detections)
                
                with col2:
                    avg_confidence_total = df['confidence'].mean()
                    st.metric("Rata-rata Kepercayaan", f"{avg_confidence_total:.1f}%")
                
                with col3:
                    most_common = df['label'].mode()[0]
                    st.metric("Kategori Terbanyak", most_common)
        else:
            st.info("ℹ Belum ada data untuk ditampilkan.")
    else:
        st.error("❌ Gagal mengambil data statistik dari database.")

# Halaman tentang
def about_page():
    st.title("📖 Tentang BRIXFIX")
    
    st.markdown("""
    <div class="card">
        <p>BRIXFIX adalah aplikasi berbasis web yang dirancang untuk membantu pengguna
        mendeteksi tingkat kerusakan bangunan berdasarkan foto yang diunggah. Aplikasi ini menggunakan teknologi
        deep learning untuk memproses data gambar dan memberikan hasil yang cepat serta akurat.</p>    
        <h3>🌟 Fitur Utama</h3>
        <ul>
            <li><strong>🏚 Deteksi Akurat:</strong> Mendukung identifikasi tiga kategori kerusakan:
                <ul>
                    <li>Rusak Berat</li>
                    <li>Rusak Menengah</li>
                    <li>Rusak Ringan</li>
                </ul>
            </li>
            <li><strong>⚡ Proses Cepat:</strong> Analisis dan prediksi dilakukan dalam waktu singkat.</li>
            <li><strong>📊 Riwayat dan Statistik:</strong> Menyimpan dan menganalisis riwayat deteksi untuk pengguna.</li>
            <li><strong>🔒 Keamanan:</strong> Sistem login dan manajemen pengguna yang aman.</li>
        </ul>    
        <h3>🔧 Teknologi yang Digunakan</h3>
        <ul>
            <li>TensorFlow/Keras: Framework untuk deep learning</li>
            <li>Streamlit: Antarmuka web interaktif</li>
            <li>MySQL: Basis data untuk menyimpan informasi</li>
            <li>Plotly: Visualisasi data interaktif</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Halaman utama aplikasi
def main_app(model):
    with st.sidebar:
        selected = option_menu(
            menu_title="🌐 Navigasi",
            options=["🏠 Beranda", "🔍 Deteksi", "📜 Riwayat", "📊 Statistik", "📖 Tentang", "🚪 Logout"],
            icons=["house", "camera", "clock-history", "bar-chart", "info-circle", "door-closed"],
            menu_icon="menu-up",
            default_index=0,
            styles={
                "container": {"padding": "1rem"},
                "icon": {"font-size": "1rem"},
                "nav-link": {"font-size": "0.9rem", "text-align": "left", "margin": "0.5rem 0"},
                "nav-link-selected": {"background-color": "#1f77b4"},
            }
        )

    if selected == "🏠 Beranda":
        st.title("🏗 BRIXFIX")

        st.markdown("""
        <div class="card">
            <h3>👋 Selamat datang di BRIXFIX</h3>
            <p>Sistem ini dirancang untuk membantu Anda menganalisis tingkat kerusakan bangunan 
            secara cepat dan akurat menggunakan teknologi AI.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="card">
                <h4>🔍 Deteksi Akurat</h4>
                <p>Sistem menggunakan AI canggih untuk menganalisis foto bangunan dan menentukan tingkat kerusakan.</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div class="card">
                <h4>⚡ Proses Cepat</h4>
                <p>Hasil deteksi tersedia dalam hitungan detik untuk membantu pengambilan keputusan.</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown("""
            <div class="card">
                <h4>📊 Laporan Lengkap</h4>
                <p>Dapatkan laporan detail tentang kondisi bangunan beserta tingkat kepercayaan hasil deteksi.</p>
            </div>
            """, unsafe_allow_html=True)

    elif selected == "🔍 Deteksi":
        detection_page(model)
    elif selected == "📜 Riwayat":
        history_page()
    elif selected == "📊 Statistik":
        statistics_page()
    elif selected == "📖 Tentang":
        about_page()
    elif selected == "🚪 Logout":
        st.session_state["logged_in"] = False
        st.session_state["email"] = None
        st.rerun()

# Load model
model = load_ai_model(MODEL_PATH)

# Inisialisasi session state
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "show_register" not in st.session_state:
    st.session_state["show_register"] = False
if "email" not in st.session_state:
    st.session_state["email"] = None

# Main routing
if st.session_state["logged_in"]:
    main_app(model)
else:
    if st.session_state["show_register"]:
        register_page()
    else:
        login_page()
