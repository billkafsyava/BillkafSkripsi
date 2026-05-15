import streamlit as st
import pandas as pd
import joblib
import base64
import sqlite3
from fpdf import FPDF

# ============================
# Load model dan preprocessing
# ============================
rf_model = joblib.load('rf_banjir_model.joblib')
scaler = joblib.load('scaler.joblib')
encoder = joblib.load('label_encoder.joblib')
month_map = joblib.load('month_mapping.joblib')

# ============================
# Setup Database SQLite
# ============================
conn = sqlite3.connect('riwayat_banjir.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS riwayat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bulan TEXT,
    curah_hujan REAL,
    hari_hujan INTEGER,
    hasil TEXT,
    wilayah TEXT,
    penyebab TEXT,
    barat TEXT,
    timur TEXT
)
''')
conn.commit()

# ============================
# Save PDF
# ============================
def generate_pdf(row):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    def add_line(text):
        pdf.multi_cell(0, 8, text)
        pdf.ln(1)

    add_line("LAPORAN HASIL PREDIKSI BANJIR KABUPATEN KEDIRI")
    add_line("====================================")

    add_line(f"Bulan: {row[1]}")
    add_line(f"Curah Hujan: {row[2]} mm")
    add_line(f"Jumlah Hari Hujan: {row[3]} hari")

    hasil = "BERPOTENSI BANJIR" if row[4] == "YES" else "TIDAK BERPOTENSI BANJIR"
    add_line(f"Hasil Prediksi: {hasil}")

    add_line("\nWilayah Terdampak:")
    add_line(row[5])

    add_line("\nPenyebab Utama:")
    add_line(row[6])

    add_line("\nWilayah Barat Sungai:")
    add_line(row[7])

    add_line("\nWilayah Timur Sungai:")
    add_line(row[8])

    return pdf.output(dest='S').encode('latin-1')

# ============================
# Session State
# ============================
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# ============================
# Mapping Wilayah Rawan per Bulan
# ============================
wilayah_banjir = {
    "JAN 2025": ["TAROKAN", "GROGOL", "KAYEN KIDUL", "KEPUNG", "KANDANGAN",
            "PURWOASRI", "PAPAR", "GAMPENGREJO", "BANYAKAN", "PARE", "KRAS"],
    
    "FEB 2025": ["KEPUNG", "KANDANGAN", "BADAS", "PARE", "NGASEM", "TAROKAN",
            "PURWOASRI", "KUNJANG", "MOJO", "PLEMAHAN", "BANYAKAN",
            "SEMEN", "GROGOL"],
    
    "MAR 2025": ["BANYAKAN", "KANDANGAN", "SEMEN", "GAMPENGREJO", "GROGOL",
            "TAROKAN", "NGASEM", "PAPAR", "PURWOASRI"],
    
    "APR 2025": ["BADAS", "KAYEN KIDUL", "NGANCAR", "KANDANGAN", "PAPAR",
            "KEPUNG", "GROGOL", "GAMPENGREJO", "SEMEN", "BANYAKAN"],
    
    "MAY 2025": ["PURWOASRI"],
    
    "JUN 2025": ["PLOSO KLATEN", "WATES", "PAPAR", "KAYEN KIDUL"],
    
    "JUL 2025": ["KEPUNG"],
    
    "AUG 2025": [],
    
    "SEP 2025": ["NGANCAR"],
    
    "OCT 2025": ["PUNCU"],
    
    "NOV 2025": ["BANYAKAN", "TAROKAN", "GROGOL"],
    
    "DEC 2025": ["TAROKAN", "GROGOL", "BANYAKAN", "WATES",
            "SEMEN", "GAMPENGREJO", "NGANCAR"]
}


# ============================
# Penyebab
# ============================
penyebab_banjir = """
Rata-rata terjadinya curah hujan yang lebat dengan intensitas tinggi dan durasi panjang
"""
# yang menyebabkan peningkatan debit air hingga melampaui kapasitas sungai.
# Kondisi ini diperparah oleh kerusakan infrastruktur pengendali air seperti tanggul,
# serta faktor topografi wilayah yang mempercepat aliran air dari hulu ke hilir.

barat_sungai = """
Terjadinya curah hujan yang lebat dari hulu gunung wilis menuju sehingga 
menyebabkan tanggul yang menahan sungai hardisingat, kolokoso, mlinjo 
dan bendo mongol jebol
"""

timur_sungai = """
Terjadinya curah hujan yang lebat dari hulu gunung kelud menyebabkan 
peningkatan debit air menuju hilir, diperparah oleh alih fungsi lahan
yang tidak terkendali serta penyempitan saluran sungai dan gorong-gorong
"""

# ============================
# Konfigurasi Halaman
# ============================
st.set_page_config(
    page_title="Sistem Prediksi",
    page_icon="🌧️",
    layout="centered"
)

def get_base64(file):
    with open(file, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return data

def set_bg_local(image_file):
    bg_img = get_base64(image_file)
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{bg_img}");
            background-size: cover;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_bg_local("banjir1.jpg")

# ============================
# UI Header
# ============================
st.title("🌧️ Sistem Prediksi Banjir Bulanan Kabupaten Kediri")
st.write(
    "Aplikasi ini digunakan untuk memprediksi potensi banjir bulanan "
    "berdasarkan **bulan**, **curah hujan**, dan **jumlah hari hujan**."
)

# st.divider()

# ============================
# Tabs
# ============================
tab1, tab2 = st.tabs(["📊 Prediksi", "📁 Riwayat"])

# ============================
# Input Data
# ============================
with tab1:
    st.subheader("Input Data")

    month_input = st.selectbox(
        "Bulan",
        placeholder="Pilih Bulan",
        options=["Pilih Bulan", "JAN 2025", "FEB 2025", "MAR 2025", 
                "APR 2025", "MAY 2025", "JUN 2025", "JUL 2025", "AUG 2025", 
                "SEP 2025", "OCT 2025", "NOV 2025", "DEC 2025"],
        help="Pilih bulan pengamatan"
    )

    rainfall_input = st.text_input(
        "Curah Hujan (mm)",
        placeholder="Masukkan total curah hujan bulanan",
        help="Masukkan total curah hujan bulanan"
    )

    rainday_input = st.text_input(
        "Jumlah Hari Hujan (hari)",
        placeholder="Masukkan jumlah hari hujan dalam satu bulan",
        help="Masukkan jumlah hari hujan dalam satu bulan"
    )

    # ============================
    # Tombol Prediksi
    # ============================
    if st.button("Prediksi Banjir"):
        
        # Validasi input
        if month_input == "" or rainfall_input == "" or rainday_input == "":
            st.error(
                "⚠️ Semua input wajib diisi. "
                "Pastikan bulan dipilih dan nilai curah hujan serta hari hujan."
            )
        else:
            # Preprocessing
            input_df = pd.DataFrame({
                'MONTH': [month_input],
                'RAINFALL': [rainfall_input],
                'RAINDAY': [rainday_input]
            })

            input_df['MONTH'] = input_df['MONTH'].map(month_map)
            input_scaled = scaler.transform(input_df)

            # Prediksi
            prediction = rf_model.predict(input_scaled)
            prediction_label = encoder.inverse_transform(prediction)[0]

            prediction_proba = rf_model.predict_proba(input_scaled)
            prob_yes = prediction_proba[0][list(encoder.classes_).index('YES')]

            # ============================
            # Output
            # ============================
            st.subheader("Hasil Prediksi")

            if prediction_label == "YES":
                st.error(
                    "🚨 **BERPOTENSI BANJIR**\n\n"
                    "Harap meningkatkan kewaspadaan dan mengikuti arahan pihak berwenang."
                )

                # ============================
                # Tampilkan Wilayah
                # ============================
                wilayah = wilayah_banjir.get(month_input, [])

                if wilayah:
                    st.write("### 📍 Perkiraan Wilayah Terdampak:")
                    st.write(", ".join(wilayah))
                else:
                    st.write("### 📍 Perkiraan Wilayah Terdampak:")
                    st.write("Tidak ada data wilayah untuk bulan ini.")

                # ============================
                # Tampilkan Penyebab
                # ============================
                st.write("### ⚠️ Faktor Penyebab:")
                st.write("#### Penyebab Utama")
                st.write(penyebab_banjir)
                st.write("#### Untuk wilayah barat sungai")
                st.write(barat_sungai)
                st.write("#### Untuk wilayah timur sungai")
                st.write(timur_sungai)

            else:
                st.success(
                    "✅ **TIDAK BERPOTENSI BANJIR**\n\n"
                    "Kondisi relatif aman, namun tetap disarankan untuk memantau cuaca."
                )
                
            # simpan ke session
            st.session_state.last_result = {
                "bulan": month_input,
                "curah": rainfall_input,
                "hari": rainday_input,
                "hasil": prediction_label,
                "wilayah": ", ".join(wilayah) if wilayah else "Tidak ada data",
                "penyebab": penyebab_banjir,
                "barat": barat_sungai,
                "timur": timur_sungai
            }
            
    # tombol simpan
    if st.session_state.last_result:
        if st.button("💾 Simpan ke Riwayat"):
            d = st.session_state.last_result

            cursor.execute("""
            INSERT INTO riwayat
            (bulan, curah_hujan, hari_hujan, hasil, wilayah, penyebab, barat, timur)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                d["bulan"], d["curah"], d["hari"], d["hasil"],
                d["wilayah"], d["penyebab"], d["barat"], d["timur"]
            ))

            conn.commit()
            st.success("Data berhasil disimpan!")
                
# ============================
# TAB 2 - RIWAYAT
# ============================
with tab2:
    st.subheader("📁 Riwayat Prediksi")

    cursor.execute("SELECT * FROM riwayat ORDER BY id DESC")
    data = cursor.fetchall()

    if not data:
        st.info("Belum ada data")
    else:
        for row in data:
            st.markdown("---")

            col1, col2, col3 = st.columns([4, 1, 1])

            with col1:
                st.markdown(f"""
**Bulan :** {row[1]}  
**Curah Hujan :** {row[2]} mm  
**Jumlah Hari Hujan :** {row[3]} hari  
**Hasil Prediksi :** {"BERPOTENSI BANJIR" if row[4]=="YES" else "TIDAK BERPOTENSI BANJIR"}  

**Perkiraan Wilayah Berdampak :**  
{row[5]}  

**Penyebab Utama :**  
{row[6]}  

**Wilayah Barat Sungai :**  
{row[7]}  

**Wilayah Timur Sungai :**  
{row[8]}  
""")

            with col2:
                if st.button("🗑️ Hapus", key=f"hapus_{row[0]}"):
                    cursor.execute("DELETE FROM riwayat WHERE id = ?", (row[0],))
                    conn.commit()
                    st.success("Data berhasil dihapus!")

                    # refresh tampilan
                    st.rerun()
            
            with col3:
                pdf_data = generate_pdf(row)
                
                bulan_clean = row[1].replace(" ", "_")  # JAN 2025 → JAN_2025

                st.download_button(
                    label="📄 PDF",
                    data=pdf_data,
                    file_name=f"laporan_banjir_{bulan_clean}_Kabupaten_Kediri.pdf",
                    mime="application/pdf",
                    key=f"pdf_{row[0]}"
                )