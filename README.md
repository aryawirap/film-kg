# Film Knowledge Graph

Sistem Knowledge Graph berbasis **Neo4j** untuk data film, dilengkapi pipeline pemrosesan data dan aplikasi web **Flask** untuk eksplorasi serta rekomendasi film berbasis kemiripan graph.

---

## Gambaran Umum

Project ini membangun knowledge graph dari dataset film TMDB/MovieLens, mengekstrak entitas (film, aktor, sutradara, genre, keyword) beserta relasinya, lalu menyimpannya ke Neo4j. Hasilnya dapat dieksplorasi melalui aplikasi web interaktif.

```
Dataset TMDB/MovieLens
        │
        ▼
┌─────────────────────┐
│  1. Baca & Parsing  │  baca_data/
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│ 2. Entity Construction │  entity_construction/
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  3. Import Neo4j    │  graph_construction/
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  4. Query & Reasoning│  query_reasoning/
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  5. Rekomendasi     │  rekomendasi/
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  6. Flask Web App   │  flask_app/
└─────────────────────┘
```

---

## Statistik Knowledge Graph

| Entitas | Jumlah |
|---|---|
| Movie | 45.460 |
| Actor | 73.155 |
| Director | 19.740 |
| Genre | 20 |
| Keyword | 19.956 |

| Relasi | Jumlah |
|---|---|
| Movie → actedBy → Actor | 207.535 |
| Movie → directedBy → Director | 50.295 |
| Movie → hasGenre → Genre | 93.342 |
| Movie → hasKeyword → Keyword | 159.437 |

---

## Struktur Proyek

```
film-kg/
├── baca_data/
│   ├── baca_data.ipynb           # Load dataset ke DataFrame
│   ├── potong_kolom.ipynb        # Seleksi dan cleaning kolom
│   └── step1_parsing.ipynb       # Parsing kolom JSON-like (genres, cast, crew)
│
├── dataset/                      # Data hasil cleaning (siap diproses)
│   ├── movies_clean.csv
│   ├── credits_clean.csv
│   ├── keywords_clean.csv
│   ├── keywords.csv
│   └── movies.csv
│
├── database/                     # Raw dataset (credits.csv & ratings.csv tidak di-push, terlalu besar)
│   ├── movies_metadata.csv
│   ├── keywords.csv
│   ├── links.csv
│   ├── links_small.csv
│   └── ratings_small.csv
│
├── entity_construction/
│   ├── step2_entity_construction.ipynb  # Bangun node & relationship Neo4j-ready
│   ├── nodes/
│   │   ├── nodes_movie.csv
│   │   ├── nodes_actor.csv
│   │   ├── nodes_director.csv
│   │   ├── nodes_genre.csv
│   │   └── nodes_keyword.csv
│   └── relationships/
│       ├── rels_movie_actor.csv
│       ├── rels_movie_director.csv
│       ├── rels_movie_genre.csv
│       └── rels_movie_keyword.csv
│
├── graph_construction/
│   └── step3_import_neo4j.ipynb  # Import CSV ke Neo4j via py2neo / neo4j driver
│
├── query_reasoning/
│   └── step4_query_reasoning.ipynb  # Query Cypher untuk eksplorasi graph
│
├── rekomendasi/
│   └── step5_rekomendasi.ipynb   # Algoritma rekomendasi berbasis graph similarity
│
└── flask_app/
    ├── app.py                    # Backend Flask & Cypher queries
    └── templates/                # Halaman web (Jinja2)
```

---

## Algoritma Rekomendasi

Kemiripan antar film dihitung berdasarkan kesamaan entitas yang terhubung dalam graph:

```
skor = (aktor_bersama × 3) + (sutradara_bersama × 4) + (genre_bersama × 2) + (keyword_bersama × 1)
```

Film dengan skor tertinggi ditampilkan sebagai rekomendasi.

---

## Prasyarat

- Python 3.8+
- Jupyter Notebook / JupyterLab
- Neo4j Desktop atau Neo4j AuraDB
- Dataset TMDB/MovieLens (lihat bagian Dataset di bawah)

---

## Dataset

Dataset berasal dari [TMDB Movie Metadata](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata) dan [MovieLens](https://grouplens.org/datasets/movielens/) di Kaggle.

Unduh dan letakkan file berikut ke folder `database/`:

| File | Ukuran | Keterangan |
|---|---|---|
| `movies_metadata.csv` | ~33 MB | Metadata film (judul, genre, revenue, dll.) |
| `credits.csv` | ~181 MB | Data aktor & sutradara (JSON nested) |
| `keywords.csv` | ~6 MB | Keyword tiap film |
| `ratings.csv` | ~677 MB | Rating pengguna (26 juta baris) |
| `links.csv` | ~1 MB | Mapping movieId ↔ tmdbId ↔ imdbId |

> `credits.csv` dan `ratings.csv` tidak disertakan di repositori ini karena ukurannya melebihi batas GitHub (100 MB).

---

## Cara Menjalankan

### 1. Clone repositori

```bash
git clone https://github.com/aryawirap/film-kg.git
cd film-kg
```

### 2. Install dependensi

```bash
pip install pandas flask neo4j jupyter
```

### 3. Siapkan dataset

Unduh file CSV dari Kaggle (lihat bagian Dataset) dan letakkan di folder `database/`.

### 4. Jalankan notebook secara berurutan

```
baca_data/baca_data.ipynb          → load data
baca_data/potong_kolom.ipynb       → cleaning
baca_data/step1_parsing.ipynb      → parsing
entity_construction/step2_entity_construction.ipynb  → bangun node & relasi
graph_construction/step3_import_neo4j.ipynb          → import ke Neo4j
query_reasoning/step4_query_reasoning.ipynb          → eksplorasi query
rekomendasi/step5_rekomendasi.ipynb                  → sistem rekomendasi
```

### 5. Konfigurasi koneksi Neo4j

Edit bagian berikut di `flask_app/app.py`:

```python
URI      = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "password123"   # ganti dengan password Neo4j Anda
DATABASE = "flimkg"
```

### 6. Jalankan aplikasi web

```bash
cd flask_app
python app.py
```

Buka browser: `http://localhost:5000`

---

## Fitur Aplikasi Web

| Halaman | Deskripsi |
|---|---|
| Beranda | Statistik jumlah entitas dalam knowledge graph |
| Browser Film | Jelajahi film dengan filter genre, pencarian judul, dan sorting |
| Browser Aktor | Daftar aktor beserta filmografi |
| Browser Sutradara | Daftar sutradara dengan statistik karya |
| Browser Genre | Daftar genre beserta jumlah film |
| Detail Film | Info lengkap + 6 rekomendasi film serupa |
| Detail Aktor | Filmografi + daftar co-aktor |
| Detail Sutradara | Filmografi + genre favorit |
| Rekomendasi | Input judul → 10 rekomendasi berdasarkan graph similarity |
| Graph Explorer | Visualisasi interaktif knowledge graph (vis.js) |

---

## Tech Stack

- **Data Processing:** Python, Pandas
- **Graph Database:** Neo4j (Cypher Query Language)
- **Backend:** Flask
- **Frontend:** Jinja2, HTML/CSS/JavaScript, vis.js Network
- **Notebook:** Jupyter

---

## Author

**I Gede Ngurah Arya Wira Putra**
GitHub: [@aryawirap](https://github.com/aryawirap)
