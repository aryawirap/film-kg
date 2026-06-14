# Film Knowledge Graph — Flask App

Aplikasi web berbasis **Flask** untuk mengeksplorasi Knowledge Graph film yang tersimpan di **Neo4j**. Menyediakan fitur pencarian, browsing, visualisasi graf, hingga rekomendasi film berbasis graph similarity.

---

## Fitur

| Halaman | Deskripsi |
|---|---|
| **Beranda** | Statistik jumlah Film, Aktor, Sutradara, Genre, dan Keyword dalam knowledge graph |
| **Browser Film** | Jelajahi film dengan filter genre, pencarian judul, dan sorting (judul / revenue / terbaru / terlama) |
| **Browser Aktor** | Daftar aktor beserta jumlah film, dilengkapi pencarian dan sorting |
| **Browser Sutradara** | Daftar sutradara dengan statistik film yang pernah disutradarai |
| **Browser Genre** | Daftar genre beserta jumlah film di tiap genre |
| **Detail Film** | Info lengkap film: sutradara, aktor, genre, keyword, dan 6 rekomendasi film serupa |
| **Detail Aktor** | Filmografi aktor dan daftar co-aktor yang sering bermain bersama |
| **Detail Sutradara** | Filmografi sutradara dan genre favorit berdasarkan histori karyanya |
| **Rekomendasi** | Input judul film, dapatkan 10 rekomendasi berdasarkan skor kemiripan graph |
| **Graph Explorer** | Visualisasi interaktif knowledge graph — eksplorasi relasi Film, Aktor, Sutradara, dan Genre |

---

## Algoritma Rekomendasi

Skor kemiripan antar film dihitung berdasarkan kesamaan entitas dalam graph:

```
skor = (aktor × 3) + (sutradara × 4) + (genre × 2) + (keyword × 1)
```

Film dengan skor tertinggi ditampilkan sebagai rekomendasi.

---

## Struktur Proyek

```
flask_app/
├── app.py              # Backend Flask & query Cypher ke Neo4j
├── templates/
│   ├── base.html       # Layout utama
│   ├── index.html      # Beranda
│   ├── db_film.html    # Browser film
│   ├── db_aktor.html   # Browser aktor
│   ├── db_sutradara.html
│   ├── db_genre.html
│   ├── detail_film.html
│   ├── detail_aktor.html
│   ├── detail_sutradara.html
│   ├── rekomendasi.html
│   ├── graph.html      # Graph explorer interaktif
│   ├── eksplorasi.html
│   └── tentang.html
└── static/
```

---

## Prasyarat

- Python 3.8+
- Neo4j Database (lokal atau cloud)
- Knowledge graph film sudah di-import ke Neo4j (database: `flimkg`)

**Node yang dibutuhkan:** `Movie`, `Actor`, `Director`, `Genre`, `Keyword`

**Relasi yang dibutuhkan:** `actedBy`, `directedBy`, `hasGenre`, `hasKeyword`

---

## Instalasi & Menjalankan

### 1. Clone repository

```bash
git clone https://github.com/aryawirap/film-kg.git
cd film-kg
```

### 2. Install dependensi

```bash
pip install flask neo4j
```

### 3. Konfigurasi koneksi Neo4j

Edit bagian berikut di `app.py`:

```python
URI      = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "password123"   # ganti dengan password Neo4j Anda
DATABASE = "flimkg"
```

### 4. Jalankan aplikasi

```bash
python app.py
```

Buka browser dan akses: `http://localhost:5000`

---

## API Endpoints

| Method | Endpoint | Deskripsi |
|---|---|---|
| GET | `/` | Beranda |
| GET | `/database/film` | Browser film (support `?search=`, `?genre=`, `?sort=`, `?page=`) |
| GET | `/database/aktor` | Browser aktor |
| GET | `/database/sutradara` | Browser sutradara |
| GET | `/database/genre` | Browser genre |
| GET | `/film?judul=` | Detail film |
| GET | `/aktor?nama=` | Detail aktor |
| GET | `/sutradara?nama=` | Detail sutradara |
| GET/POST | `/rekomendasi` | Rekomendasi film |
| GET | `/graph` | Graph explorer |
| GET | `/api/graph?q=&type=` | Data graph (JSON) |
| GET | `/cari?q=` | Autocomplete judul film |
| GET | `/cari-aktor?q=` | Autocomplete nama aktor |
| GET | `/cari-sutradara?q=` | Autocomplete nama sutradara |

---

## Tech Stack

- **Backend:** Python, Flask
- **Database:** Neo4j (Cypher Query Language)
- **Frontend:** Jinja2 Templates, HTML/CSS/JavaScript
- **Graph Visualization:** vis.js Network
