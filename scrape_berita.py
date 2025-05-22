import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import time
import schedule
from datetime import datetime

# 🔧 Konfigurasi
keywords = ["pencurian", "perampokan", "kamera cctv", "rumah dibobol"]
jumlah_halaman = 5

# Koneksi MongoDB
client = MongoClient("mongodb+srv://priaidaman:085778612820Iu%2A@test.knrjxyl.mongodb.net/?retryWrites=true&w=majority&appName=Test")
db = client["berita_keamanan"]
collection = db["berita"]

def get_detik_links(keyword, jumlah_halaman):
    links = []
    for page in range(1, jumlah_halaman + 1):
        url = f"https://www.detik.com/search/searchall?query={keyword}&siteid=2&sortby=time&page={page}"
        print(f"🔍 Mengakses: {url}")
        try:
            res = requests.get(url, timeout=10)
            soup = BeautifulSoup(res.content, "html.parser")
            for a in soup.select("article a"):
                href = a.get("href")
                if href and "https://news.detik.com/" in href:
                    links.append(href)
        except Exception as e:
            print(f"❌ Error akses halaman: {e}")
        time.sleep(1)
    return list(set(links))

def scrape_detik(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.content, 'html.parser')
        judul = soup.find('h1').text.strip()
        isi_elem = soup.find_all('p')
        isi = ' '.join(p.text for p in isi_elem)

        # Tambahkan tanggal sekarang sebagai metadata
        tanggal = datetime.now()

        return {
            "judul": judul,
            "isi": isi,
            "url": url,
            "tanggal": tanggal  # simpan datetime object
        }
    except Exception as e:
        print(f"❌ Gagal scrape {url} - {e}")
        return None


def scrape_and_store():
    total_disimpan = 0
    for keyword in keywords:
        print(f"\n📌 Scraping untuk: '{keyword}'")
        links = get_detik_links(keyword, jumlah_halaman)
        print(f"🔗 Ditemukan {len(links)} link")

        for link in links:
            data = scrape_detik(link)
            if data:
                if collection.count_documents({"url": data["url"]}) == 0:
                    collection.insert_one(data)
                    total_disimpan += 1
                    print(f"✅ Disimpan: {data['judul'][:60]}...")
                else:
                    print(f"⚠️ Sudah ada: {data['url']}")
            time.sleep(1)

    print(f"\n🎉 Total artikel baru yang disimpan: {total_disimpan}")

# =============================
# 🚀 Mode: Terjadwal atau Manual
# =============================

if __name__ == "__main__":
    mode = input("Jalankan sekali atau otomatis setiap 10 detik? (sekali / auto): ").strip().lower()
    
    if mode == "auto":
        schedule.every(10).seconds.do(scrape_and_store)
        print("🕒 Menjalankan scraper otomatis setiap 10 detik...\n")
        while True:
            schedule.run_pending()
            time.sleep(1)
    else:
        print("▶️ Menjalankan scraper satu kali...\n")
        scrape_and_store()
