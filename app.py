import os
import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from PIL import Image
import numpy as np
import time
from datetime import datetime
import requests

# Konfigurasi halaman
st.set_page_config(
    page_title="Sistem Deteksi Kerusakan Bangunan Berbasis Website",
    page_icon="🏠",
    layout="wide"
)

# Path ke model (relatif, jika ada secara lokal)
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "model_klasifikasirumah.h5")
# URL RAW dari GitHub untuk file model
MODEL_URL = "https://raw.githubusercontent.com/nabilamumtaz/house-damage-detection/main/model/model_klasifikasirumah.h5"

# Fungsi untuk mengunduh model dari GitHub jika belum ada
def download_model(model_url, model_path):
    if not os.path.exists(model_path):
        st.info("📥 Mengunduh model dari GitHub...")
        response = requests.get(model_url)
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        with open(model_path, "wb") as f:
            f.write(response.content)

# Unduh model jika belum ada
download_model(MODEL_URL, MODEL_PATH)

# Inisialisasi session state
if 'history' not in st.session_state:
    st.session_state.history = []

# Fungsi untuk memuat model
@st.cache_resource
def load_model_from_file(model_path):
    try:
        model = load_model(model_path)
        return model
    except Exception as e:
        st.error(f"❌ Error loading model: {e}")
        return None

# Load model saat aplikasi berjalan
model = load_model_from_file(MODEL_PATH)

# Fungsi prediksi
def predict_image(model, image):
    try:
        img = image.resize((128, 128))
        img_array = img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        predictions = model.predict(img_array)
        predicted_index = np.argmax(predictions)
        confidence = predictions[0][predicted_index] * 100
        label = ["Rusak Berat", "Rusak Menengah", "Rusak Ringan"][predicted_index]

        # Validasi gambar rumah
        if label not in ["Rusak Berat", "Rusak Menengah", "Rusak Ringan"]:
            return None, None  # Jika bukan rumah, kembalikan None
        return label, confidence
    except Exception as e:
        st.error(f"❌ Error during prediction: {e}")
        return None, None

# Fungsi untuk menyimpan riwayat deteksi
def save_to_history(image, label, confidence):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.history.append({
        "timestamp": timestamp,
        "label": label,
        "confidence": confidence,
        "image": image
    })

# Navigasi dengan sidebar
with st.sidebar:
    selected = option_menu(
        "Navigasi",
        ["Beranda", "Deteksi", "Riwayat", "Statistik", "Tentang"],
        icons=["house", "camera", "clock-history", "bar-chart", "info-circle"],
        menu_icon="menu",
        default_index=0
    )

# Halaman Beranda
if selected == "Beranda":
    st.title("🏠 **Sistem Deteksi Kerusakan Bangunan Berbasis Website**")
    st.markdown("""
    Selamat datang di website yang dirancang untuk membantu mendeteksi tingkat kerusakan bangunan.
    """)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("🔍 **Deteksi Akurat**\nMenggunakan AI terkini untuk hasil yang presisi.")
    with col2:
        st.info("⚡ **Proses Cepat**\nHasil analisis dalam hitungan detik.")
    with col3:
        st.info("📊 **Laporan Lengkap**\nLihat tingkat kerusakan dan rekomendasi perbaikan.")

# Halaman Deteksi
elif selected == "Deteksi":
    st.title("🔍 **Deteksi Kerusakan Bangunan**")
    
    if model:
        uploaded_file = st.file_uploader("📤 **Upload Foto Bangunan Anda di Sini**", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="🖼️ **Foto yang diunggah**", use_container_width=True)

            # Spinner untuk proses prediksi
            with st.spinner("🪄 **Sedang Proses...✨**"):
                time.sleep(3)  # Simulasi proses
                label, confidence = predict_image(model, image)
                if label and confidence is not None:
                    st.success(f"🎉 **Hasil Deteksi:** {label} 🏠")
                    st.info(f"📊 **Tingkat Kepercayaan:** {confidence:.2f}%")
                    save_to_history(image, label, confidence)
                    st.balloons()
                else:
                    st.error("❌ **Maaf, website ini hanya mendukung gambar rumah. Silakan unggah gambar rumah.**")

# Halaman Riwayat
elif selected == "Riwayat":
    st.title("📜 **Riwayat Deteksi**")
    if st.session_state.history:
        for item in reversed(st.session_state.history):
            with st.expander(f"{item['timestamp']} - {item['label']}"):
                st.image(item['image'], caption="Gambar Bangunan", use_container_width=True)
                st.write(f"**Hasil Deteksi:** {item['label']}")
                st.write(f"**Tingkat Kepercayaan:** {item['confidence']:.2f}%")
    else:
        st.info("⚠️ Belum ada riwayat deteksi.")

# Halaman Statistik
elif selected == "Statistik":
    st.title("📊 **Statistik Deteksi**")
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        st.subheader("**Distribusi Deteksi**")
        fig = px.pie(df, names="label", title="Distribusi Kategori Kerusakan")
        st.plotly_chart(fig)
        st.subheader("**Rata-rata Tingkat Kepercayaan per Kategori**")
        avg_confidence = df.groupby('label')['confidence'].mean().reset_index()
        fig = px.bar(avg_confidence, x='label', y='confidence', 
                     title='Rata-rata Tingkat Kepercayaan per Kategori',
                     labels={'confidence': 'Tingkat Kepercayaan (%)', 'label': 'Kategori Kerusakan'})
        st.plotly_chart(fig)

# Halaman Tentang
elif selected == "Tentang":
    st.title("📖 **Tentang**")
    st.markdown("""
    Sistem ini dikembangkan oleh **Nabila Mumtaz** dan **Tasyfia Farhah Subrina Lubis** sebagai bagian dari tugas magang di **BPK RI** (*Badan Pemeriksa Keuangan Republik Indonesia*). 
    Tujuan utama dari website ini adalah untuk memanfaatkan teknologi **Artificial Intelligence (AI)** dalam mendeteksi tingkat kerusakan bangunan berdasarkan gambar yang diunggah.

    ### **Teknologi yang Digunakan**
    - **Deep Learning** dengan arsitektur **MobileNetV2**
    - **TensorFlow/Keras** untuk model AI
    - **Streamlit** untuk antarmuka web
    - **Plotly** untuk visualisasi data

    ### **Fitur Utama**
    - **Klasifikasi Kerusakan**:
        - **Rusak Berat**
        - **Rusak Menengah**
        - **Rusak Ringan**
    - **Tingkat Kepercayaan Model**: Menyediakan tingkat akurasi hasil analisis
    - **Visualisasi Data Interaktif**: Menampilkan statistik hasil analisis dalam bentuk grafik

    Website ini dirancang untuk memberikan solusi cepat dan akurat dalam menganalisis kerusakan bangunan, mendukung efisiensi proses penilaian di **BPK RI**.
    """)

st.markdown("---")
st.markdown("© 2025 Sistem Deteksi Kerusakan Bangunan berbasis website.")
