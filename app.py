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

# Konfigurasi halaman
st.set_page_config(
    page_title="Sistem Deteksi Kerusakan Bangunan Berbasis Website",
    page_icon="🏠",
    layout="wide"
)

# Path ke model
MODEL_PATH = "C:/Users/Nabila Mumtaz/OneDrive/Documents/Streamlit.app/model/model_klasifikasirumah.h5"

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
        st.error(f"Error loading model: {str(e)}")
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
        return ["Rusak Berat", "Rusak Menengah", "Rusak Ringan"][predicted_index], confidence
    except Exception as e:
        st.error(f"Error during prediction: {str(e)}")
        return None, None


# Custom CSS untuk tema
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');

body {
    background: linear-gradient(135deg, #e8faff, #d0ebff);
    font-family: 'Poppins', sans-serif;
    color: #2d3436;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(135deg, #ffffff, #dfe6e9);
    border-right: 1px solid #dfe6e9;
    padding: 1rem;
}

div[data-testid="stSidebar"] .nav-link {
    font-size: 16px;
    font-weight: 500;
    margin: 10px 0;
    padding: 10px 15px;
    border-radius: 8px;
    color: #2ecc71 !important;
    transition: all 0.3s ease;
}

div[data-testid="stSidebar"] .nav-link:hover {
    background: #f1c40f !important;
    color: #ffffff !important;
}

div[data-testid="stSidebar"] .nav-link.active {
    background: linear-gradient(135deg, #2ecc71, #f1c40f) !important;
    color: #ffffff !important;
    font-weight: bold;
    border-radius: 10px;
}

.stButton > button {
    background: linear-gradient(135deg, #2ecc71, #f1c40f);
    color: white;
    font-size: 16px;
    font-weight: bold;
    padding: 10px 20px;
    border: none;
    border-radius: 8px;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #f1c40f, #2ecc71);
    box-shadow: 0px 6px 12px rgba(0, 0, 0, 0.2);
    transform: translateY(-2px);
}

footer {
    text-align: center;
    font-size: 12px;
    color: #2ecc71;
    margin-top: 20px;
}
</style>
""", unsafe_allow_html=True)

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

            # Spinner dengan emoji lucu
            with st.spinner("🪄 **Sedang Proses...✨**"):
                time.sleep(3)  # Simulasi proses
                label, confidence = predict_image(model, image)
                
                if label and confidence is not None:
                    st.success(f"🎉 **Hasil Deteksi:** {label} 🏠")
                    st.info(f"📊 **Tingkat Kepercayaan:** {confidence:.2f}%")
                    save_to_history(image, label, confidence)
                    st.balloons()  # Efek balon
                else:
                    st.error("😿 **Yah, ada yang salah nih. Coba lagi ya!**")


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
        st.info("Belum ada riwayat deteksi.")

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
    st.title("ℹ **Tentang**")
    st.markdown("""
    Sistem ini dikembangkan oleh **Nabila Mumtaz** dan **Tasyfia Farhah Subrina Lubis** sebagai bagian dari tugas magang di **BPK RI** (*Badan Pemeriksa Keuangan Republik Indonesia*). 
    Tujuan utama dari website ini adalah untuk memanfaatkan teknologi **Artificial Intelligence (AI)** dalam mendeteksi tingkat kerusakan bangunan berdasarkan gambar yang diunggah.

    ### **Teknologi yang Digunakan**
    - **Deep Learning** dengan arsitektur **MobileNetV2** untuk klasifikasi gambar
    - **TensorFlow/Keras** untuk membangun model AI
    - **Streamlit** sebagai framework untuk antarmuka pengguna berbasis web
    - **Plotly** untuk visualisasi data analisis

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
st.markdown("© 2025 **Sistem Deteksi Kerusakan Bangunan berbasis website**.")
