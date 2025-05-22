# app.py
import streamlit as st
from pymongo import MongoClient
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
import pandas as pd
import re
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from datetime import datetime, timedelta
import random

# Koneksi MongoDB
client = MongoClient("mongodb+srv://priaidaman:085778612820Iu%2A@test.knrjxyl.mongodb.net/?retryWrites=true&w=majority&appName=Test")
db = client["berita_keamanan"]
collection = db["berita"]
berita_list = list(collection.find())

st.title("📊 Visualisasi Data Berita Keamanan")

if not berita_list:
    st.warning("Belum ada data berita. Jalankan scraper terlebih dahulu.")
    st.stop()

# Tambahkan tanggal acak jika belum ada (untuk testing grafik)
for b in berita_list:
    if "tanggal" not in b:
        random_days = random.randint(0, 180)  # antara 0-180 hari ke belakang
        random_date = datetime.now() - timedelta(days=random_days)
        collection.update_one({"_id": b["_id"]}, {"$set": {"tanggal": random_date}})

# Reload berita setelah update
berita_list = list(collection.find())

# Konversi ke DataFrame
df_berita = pd.DataFrame(berita_list)
df_berita["tanggal"] = pd.to_datetime(df_berita["tanggal"], errors='coerce')
df_berita = df_berita.dropna(subset=["tanggal"])
df_berita["bulan"] = df_berita["tanggal"].dt.to_period("M").astype(str)

# Sidebar Filter Bulan
st.sidebar.header("🗓️ Filter Bulan")
opsi_bulan = sorted(df_berita["bulan"].unique())
bulan_terpilih = st.sidebar.selectbox("Pilih Bulan", ["Semua"] + opsi_bulan)

if bulan_terpilih != "Semua":
    df_berita = df_berita[df_berita["bulan"] == bulan_terpilih]

# 1. Tampilkan Judul Berita
st.subheader("📰 Daftar Judul Berita")
data = [{"Judul": b["judul"], "URL": b["url"], "Panjang (kata)": len(b["isi"].split())} for b in df_berita.to_dict("records")]
df_judul = pd.DataFrame(data)
st.dataframe(df_judul)

# 2. WordCloud
st.subheader("🔠 WordCloud dari Isi Berita")
all_text = " ".join(df_berita["isi"].tolist())
clean_text = re.sub(r'\W+', ' ', all_text.lower())
word_list = clean_text.split()

factory = StopWordRemoverFactory()
stopwords = set(factory.get_stop_words())
filtered_words = [w for w in word_list if w not in stopwords and len(w) > 3]
filtered_text = " ".join(filtered_words)

wordcloud = WordCloud(width=800, height=400, background_color='white').generate(filtered_text)
plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")
st.pyplot(plt)

# 3. Grafik Panjang Artikel
st.subheader("📏 Grafik Panjang Artikel")
df_judul_sorted = df_judul.sort_values("Panjang (kata)", ascending=False)
st.bar_chart(df_judul_sorted.set_index("Judul")["Panjang (kata)"])

# 4. Grafik Jumlah Berita per Bulan (semua data, tanpa filter)
st.subheader("🗓️ Jumlah Berita per Bulan")
df_all = pd.DataFrame(berita_list)
df_all["tanggal"] = pd.to_datetime(df_all["tanggal"], errors='coerce')
df_all = df_all.dropna(subset=["tanggal"])
df_all["bulan"] = df_all["tanggal"].dt.to_period("M").astype(str)
berita_per_bulan = df_all.groupby("bulan").size().reset_index(name="jumlah")
st.line_chart(data=berita_per_bulan.set_index("bulan"))

# 5. Kata Paling Sering Muncul
st.subheader("📊 15 Kata yang Paling Sering Muncul")
word_counts = Counter(filtered_words).most_common(15)
word_df = pd.DataFrame(word_counts, columns=["Kata", "Frekuensi"])
st.bar_chart(word_df.set_index("Kata"))
