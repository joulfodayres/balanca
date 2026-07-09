import os
import sqlite3
from datetime import date
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_PATH = os.environ.get("DB_PATH", "data/balanca.db")


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS registos (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                data DATE    NOT NULL UNIQUE,
                peso REAL    NOT NULL
            )
        """)
        conn.commit()


init_db()


# ─── Frontend ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ─── API: Registos ────────────────────────────────────────────────────────────

@app.route("/api/registos", methods=["GET"])
def list_registos():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, data, peso FROM registos ORDER BY data ASC"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/registos", methods=["POST"])
def create_registo():
    body = request.get_json()
    data = body.get("data")
    peso = body.get("peso")
    if not data or peso is None:
        return jsonify({"erro": "data e peso são obrigatórios"}), 400
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO registos (data, peso) VALUES (?, ?)", (data, peso)
            )
            conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"erro": f"Já existe registo para {data}"}), 409
    return jsonify({"ok": True}), 201


@app.route("/api/registos/<int:rid>", methods=["PUT"])
def update_registo(rid):
    body = request.get_json()
    data = body.get("data")
    peso = body.get("peso")
    if not data or peso is None:
        return jsonify({"erro": "data e peso são obrigatórios"}), 400
    with get_db() as conn:
        cur = conn.execute(
            "UPDATE registos SET data=?, peso=? WHERE id=?", (data, peso, rid)
        )
        conn.commit()
    if cur.rowcount == 0:
        return jsonify({"erro": "Registo não encontrado"}), 404
    return jsonify({"ok": True})


@app.route("/api/registos/<int:rid>", methods=["DELETE"])
def delete_registo(rid):
    with get_db() as conn:
        cur = conn.execute("DELETE FROM registos WHERE id=?", (rid,))
        conn.commit()
    if cur.rowcount == 0:
        return jsonify({"erro": "Registo não encontrado"}), 404
    return jsonify({"ok": True})


# ─── API: Import bulk ─────────────────────────────────────────────────────────

@app.route("/api/import", methods=["POST"])
def import_registos():
    items = request.get_json()
    if not isinstance(items, list):
        return jsonify({"erro": "Esperado array de {data, peso}"}), 400
    inserted = 0
    skipped = 0
    with get_db() as conn:
        for item in items:
            try:
                conn.execute(
                    "INSERT INTO registos (data, peso) VALUES (?, ?)",
                    (item["data"], item["peso"]),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                skipped += 1
        conn.commit()
    return jsonify({"inseridos": inserted, "ignorados": skipped})


# ─── API: Pesquisa histórica ──────────────────────────────────────────────────

@app.route("/api/pesquisa", methods=["GET"])
def pesquisa():
    data = request.args.get("data")
    if not data:
        return jsonify({"erro": "Parâmetro 'data' obrigatório"}), 400
    with get_db() as conn:
        # peso registado na data indicada
        row = conn.execute(
            "SELECT peso FROM registos WHERE data = ?", (data,)
        ).fetchone()
        if not row:
            return jsonify({"erro": f"Sem registo para {data}"}), 404
        peso_ref = row["peso"]
        # últimas 10 datas com peso <= peso_ref (excluindo a própria data)
        rows = conn.execute(
            """
            SELECT data, peso FROM registos
            WHERE peso <= ? AND data <= ?
            ORDER BY data DESC
            LIMIT 10
            """,
            (peso_ref, data),
        ).fetchall()
    return jsonify({
        "data": data,
        "peso_ref": peso_ref,
        "resultados": [dict(r) for r in rows],
    })


if __name__ == "__main__":
    app.run(debug=True)
