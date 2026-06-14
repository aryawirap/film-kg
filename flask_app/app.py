from flask import Flask, render_template, request, jsonify
from neo4j import GraphDatabase
import math

app = Flask(__name__)

URI      = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "password123"
DATABASE = "flimkg"

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

PER_PAGE = 24

def q(cypher, **params):
    with driver.session(database=DATABASE) as s:
        return s.run(cypher, **params).data()


# ── Landing Page ─────────────────────────────────────────────
@app.route("/")
def index():
    stats = {label: q(f"MATCH (n:{label}) RETURN count(n) AS t")[0]["t"]
             for label in ["Movie", "Actor", "Director", "Genre", "Keyword"]}
    return render_template("index.html", stats=stats)


# ── Tentang / Pipeline ───────────────────────────────────────
@app.route("/tentang")
def tentang():
    return render_template("tentang.html")


# ── Database: Film Browser ───────────────────────────────────
@app.route("/database/film")
def db_film():
    search = request.args.get("search", "").strip()
    genre  = request.args.get("genre", "").strip()
    sort   = request.args.get("sort", "judul")
    page   = max(1, int(request.args.get("page", 1)))
    skip   = (page - 1) * PER_PAGE

    where_clauses = []
    params = {"skip": skip, "limit": PER_PAGE}

    if search:
        where_clauses.append("toLower(m.title) CONTAINS toLower($search)")
        params["search"] = search
    if genre:
        where_clauses.append("EXISTS { MATCH (m)-[:hasGenre]->(g:Genre {name: $genre}) }")
        params["genre"] = genre

    where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    order = {
        "revenue": "coalesce(m.revenue, 0) DESC",
        "terbaru": "m.release_date DESC",
        "terlama": "m.release_date ASC",
    }.get(sort, "m.title")

    films = q(f"""
        MATCH (m:Movie)
        {where}
        OPTIONAL MATCH (m)-[:hasGenre]->(g:Genre)
        OPTIONAL MATCH (m)-[:directedBy]->(d:Director)
        WITH m, collect(DISTINCT g.name) AS genres, collect(DISTINCT d.name) AS directors
        RETURN m.title AS judul, m.release_date AS tahun,
               m.revenue AS revenue, genres, directors
        ORDER BY {order}
        SKIP $skip LIMIT $limit
    """, **params)

    count_params = {k: v for k, v in params.items() if k not in ("skip", "limit")}
    total = q(f"MATCH (m:Movie) {where} RETURN count(m) AS t", **count_params)[0]["t"]
    total_pages = math.ceil(total / PER_PAGE)

    genres_list = q("MATCH (g:Genre) RETURN g.name AS name ORDER BY g.name")

    return render_template("db_film.html",
                           films=films, genres=genres_list,
                           search=search, genre=genre, sort=sort,
                           page=page, total_pages=total_pages, total=total)


# ── Database: Aktor Browser ──────────────────────────────────
@app.route("/database/aktor")
def db_aktor():
    search = request.args.get("search", "").strip()
    sort   = request.args.get("sort", "film")
    page   = max(1, int(request.args.get("page", 1)))
    skip   = (page - 1) * PER_PAGE

    where  = "WHERE toLower(a.name) CONTAINS toLower($search)" if search else ""
    params = {"skip": skip, "limit": PER_PAGE, "search": search}

    order = "a.name" if sort == "nama" else "total_film DESC"

    actors = q(f"""
        MATCH (a:Actor)<-[:actedBy]-(m:Movie)
        {where}
        WITH a, count(m) AS total_film
        RETURN a.name AS nama, total_film
        ORDER BY {order}
        SKIP $skip LIMIT $limit
    """, **params)

    count_params = {"search": search}
    total = q(f"MATCH (a:Actor) {where} RETURN count(a) AS t", **count_params)[0]["t"]
    total_pages = math.ceil(total / PER_PAGE)

    return render_template("db_aktor.html",
                           actors=actors, search=search, sort=sort,
                           page=page, total_pages=total_pages, total=total)


# ── Database: Genre Browser ──────────────────────────────────
@app.route("/database/genre")
def db_genre():
    sort  = request.args.get("sort", "film")
    order = "g.name" if sort == "nama" else "total_film DESC"
    genres = q(f"""
        MATCH (g:Genre)<-[:hasGenre]-(m:Movie)
        WITH g, count(m) AS total_film
        RETURN g.name AS nama, total_film
        ORDER BY {order}
    """)
    return render_template("db_genre.html", genres=genres, sort=sort)


# ── Detail Film ──────────────────────────────────────────────
@app.route("/film")
def detail_film():
    judul = request.args.get("judul", "").strip()
    if not judul:
        return render_template("detail_film.html", film=None, judul="")

    info = q("""
        MATCH (m:Movie {title: $judul})
        OPTIONAL MATCH (m)-[:directedBy]->(d:Director)
        OPTIONAL MATCH (m)-[:hasGenre]->(g:Genre)
        OPTIONAL MATCH (m)-[:actedBy]->(a:Actor)
        OPTIONAL MATCH (m)-[:hasKeyword]->(k:Keyword)
        RETURN m.title AS judul, m.release_date AS tahun, m.revenue AS revenue,
               collect(DISTINCT d.name) AS sutradara,
               collect(DISTINCT g.name) AS genre,
               collect(DISTINCT a.name) AS aktor,
               collect(DISTINCT k.name) AS keyword
    """, judul=judul)

    rekomendasi = q("""
        MATCH (target:Movie {title: $title})
        OPTIONAL MATCH (target)-[:actedBy]->(a:Actor)<-[:actedBy]-(k:Movie)
        WHERE k <> target
        WITH target, k, count(DISTINCT a) AS sa
        OPTIONAL MATCH (target)-[:directedBy]->(d:Director)<-[:directedBy]-(k)
        WITH target, k, sa, count(DISTINCT d) AS sd
        OPTIONAL MATCH (target)-[:hasGenre]->(g:Genre)<-[:hasGenre]-(k)
        WITH target, k, sa, sd, count(DISTINCT g) AS sg
        OPTIONAL MATCH (target)-[:hasKeyword]->(kw:Keyword)<-[:hasKeyword]-(k)
        WITH k, sa, sd, sg, count(DISTINCT kw) AS sk
        WITH k, sa, sd, sg, sk, (sa*3)+(sd*4)+(sg*2)+(sk*1) AS skor
        WHERE skor > 0
        RETURN k.title AS judul, skor AS skor_total,
               sa AS aktor, sd AS sutradara, sg AS genre, sk AS keyword
        ORDER BY skor DESC LIMIT 6
    """, title=judul)

    return render_template("detail_film.html",
                           film=info[0] if info else None,
                           rekomendasi=rekomendasi, judul=judul)


# ── Detail Aktor ─────────────────────────────────────────────
@app.route("/aktor")
def detail_aktor():
    nama = request.args.get("nama", "").strip()
    if not nama:
        return render_template("detail_aktor.html", nama="", film_list=[], co_aktor=[])

    film_list = q("""
        MATCH (a:Actor {name: $nama})<-[:actedBy]-(m:Movie)
        OPTIONAL MATCH (m)-[:hasGenre]->(g:Genre)
        OPTIONAL MATCH (m)-[:directedBy]->(d:Director)
        WITH m, collect(DISTINCT g.name) AS genre, collect(DISTINCT d.name) AS sutradara
        RETURN m.title AS judul, m.release_date AS tahun, genre, sutradara
        ORDER BY m.release_date DESC LIMIT 20
    """, nama=nama)

    co_aktor = q("""
        MATCH (a:Actor {name: $nama})<-[:actedBy]-(m:Movie)-[:actedBy]->(b:Actor)
        WHERE a <> b
        WITH b, count(m) AS bareng
        RETURN b.name AS nama, bareng
        ORDER BY bareng DESC LIMIT 10
    """, nama=nama)

    return render_template("detail_aktor.html",
                           nama=nama, film_list=film_list, co_aktor=co_aktor)


# ── Rekomendasi ──────────────────────────────────────────────
_REK_QUERY = """
    MATCH (target:Movie {title: $title})
    OPTIONAL MATCH (target)-[:actedBy]->(a:Actor)<-[:actedBy]-(k:Movie)
    WHERE k <> target
    WITH target, k, count(DISTINCT a) AS sa
    OPTIONAL MATCH (target)-[:directedBy]->(d:Director)<-[:directedBy]-(k)
    WITH target, k, sa, count(DISTINCT d) AS sd
    OPTIONAL MATCH (target)-[:hasGenre]->(g:Genre)<-[:hasGenre]-(k)
    WITH target, k, sa, sd, count(DISTINCT g) AS sg
    OPTIONAL MATCH (target)-[:hasKeyword]->(kw:Keyword)<-[:hasKeyword]-(k)
    WITH k, sa, sd, sg, count(DISTINCT kw) AS sk
    WITH k, sa, sd, sg, sk, (sa*3)+(sd*4)+(sg*2)+(sk*1) AS skor
    WHERE skor > 0
    RETURN k.title AS judul, skor AS skor_total,
           sa AS aktor, sd AS sutradara, sg AS genre, sk AS keyword
    ORDER BY skor DESC LIMIT 10
"""

@app.route("/rekomendasi", methods=["GET", "POST"])
def rekomendasi():
    hasil, film, matched_film, candidates = [], "", "", []

    if request.method == "POST":
        film = request.form.get("judul", "").strip()
        if film:
            # Cari kandidat: exact dulu, lalu starts-with, lalu contains
            matches = q("""
                MATCH (m:Movie)
                WHERE toLower(m.title) CONTAINS toLower($t)
                RETURN m.title AS title
                ORDER BY
                  CASE
                    WHEN m.title = $t                              THEN 0
                    WHEN toLower(m.title) = toLower($t)            THEN 1
                    WHEN toLower(m.title) STARTS WITH toLower($t)  THEN 2
                    ELSE 3
                  END,
                  size(m.title)
                LIMIT 8
            """, t=film)

            if matches:
                top = matches[0]["title"]
                # Auto-pick jika exact (case-insensitive) atau hanya satu hasil
                if top.lower() == film.lower() or len(matches) == 1:
                    matched_film = top
                    hasil = q(_REK_QUERY, title=matched_film)
                else:
                    candidates = [r["title"] for r in matches]

    return render_template("rekomendasi.html",
                           hasil=hasil, film=film,
                           matched_film=matched_film, candidates=candidates)


# ── Database: Sutradara Browser ──────────────────────────────
@app.route("/database/sutradara")
def db_sutradara():
    search = request.args.get("search", "").strip()
    sort   = request.args.get("sort", "film")
    page   = max(1, int(request.args.get("page", 1)))
    skip   = (page - 1) * PER_PAGE

    where  = "WHERE toLower(d.name) CONTAINS toLower($search)" if search else ""
    params = {"skip": skip, "limit": PER_PAGE, "search": search}

    order = "d.name" if sort == "nama" else "total_film DESC"

    directors = q(f"""
        MATCH (d:Director)<-[:directedBy]-(m:Movie)
        {where}
        WITH d, count(m) AS total_film
        RETURN d.name AS nama, total_film
        ORDER BY {order}
        SKIP $skip LIMIT $limit
    """, **params)

    total = q(f"MATCH (d:Director) {where} RETURN count(d) AS t", search=search)[0]["t"]
    total_pages = math.ceil(total / PER_PAGE)

    return render_template("db_sutradara.html",
                           directors=directors, search=search, sort=sort,
                           page=page, total_pages=total_pages, total=total)


# ── Detail Sutradara ─────────────────────────────────────────
@app.route("/sutradara")
def detail_sutradara():
    nama = request.args.get("nama", "").strip()
    if not nama:
        return render_template("detail_sutradara.html", nama="", film_list=[], co_director=[])

    film_list = q("""
        MATCH (d:Director {name: $nama})<-[:directedBy]-(m:Movie)
        OPTIONAL MATCH (m)-[:hasGenre]->(g:Genre)
        OPTIONAL MATCH (m)-[:actedBy]->(a:Actor)
        WITH m, collect(DISTINCT g.name) AS genre, collect(DISTINCT a.name) AS aktor
        RETURN m.title AS judul, m.release_date AS tahun,
               m.revenue AS revenue, genre, aktor
        ORDER BY m.release_date DESC
    """, nama=nama)

    # Genre favorit sutradara ini
    genre_stats = q("""
        MATCH (d:Director {name: $nama})<-[:directedBy]-(m:Movie)-[:hasGenre]->(g:Genre)
        WITH g, count(m) AS total
        RETURN g.name AS nama, total
        ORDER BY total DESC LIMIT 5
    """, nama=nama)

    return render_template("detail_sutradara.html",
                           nama=nama, film_list=film_list, genre_stats=genre_stats)


# ── Cypher Query Runner ──────────────────────────────────────
@app.route("/cypher")
def cypher_page():
    return render_template("cypher.html")

@app.route("/api/cypher", methods=["POST"])
def api_cypher():
    import time
    payload = request.get_json(silent=True) or {}
    cypher  = (payload.get("query") or "").strip()
    if not cypher:
        return jsonify({"error": "Query kosong."}), 400
    try:
        t0      = time.perf_counter()
        results = q(cypher)
        elapsed = round((time.perf_counter() - t0) * 1000)
        return jsonify({"rows": results, "count": len(results), "elapsed_ms": elapsed})
    except Exception as exc:
        msg = str(exc)
        # trim verbose Neo4j stacktrace — keep only the first meaningful line
        first = next((l.strip() for l in msg.splitlines() if l.strip()), msg)
        return jsonify({"error": first}), 400



# ── Autocomplete ─────────────────────────────────────────────
@app.route("/cari")
def cari():
    qstr = request.args.get("q", "")
    if len(qstr) < 2: return jsonify([])
    data = q("MATCH (m:Movie) WHERE toLower(m.title) CONTAINS toLower($q) RETURN m.title AS t ORDER BY m.title LIMIT 8", q=qstr)
    return jsonify([d["t"] for d in data])

@app.route("/cari-aktor")
def cari_aktor():
    qstr = request.args.get("q", "")
    if len(qstr) < 2: return jsonify([])
    data = q("MATCH (a:Actor) WHERE toLower(a.name) CONTAINS toLower($q) RETURN a.name AS n ORDER BY a.name LIMIT 8", q=qstr)
    return jsonify([d["n"] for d in data])

@app.route("/cari-sutradara")
def cari_sutradara():
    qstr = request.args.get("q", "")
    if len(qstr) < 2: return jsonify([])
    data = q("MATCH (d:Director) WHERE toLower(d.name) CONTAINS toLower($q) RETURN d.name AS n ORDER BY d.name LIMIT 8", q=qstr)
    return jsonify([d["n"] for d in data])


if __name__ == "__main__":
    app.run(debug=True, port=5000)
