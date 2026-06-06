"""
Main application file for the Spaced Repetition Vocabulary Engine.
Handles API routing, database interactions, and frontend rendering.
"""

import sqlite3
from datetime import date, timedelta
from flask import Flask, render_template, request, jsonify

# Import the math engine you built last night
from sm2 import calculate_next_review

app = Flask(__name__)


def get_db_connection():
    """Establish and return a database connection with row factory."""
    conn = sqlite3.connect("vocab.db")
    conn.row_factory = sqlite3.Row  # Allows dictionary-like access to rows
    return conn


def row_to_dict(row):
    """Convert SQLite Row to dictionary and format data for frontend."""
    d = dict(row)
    # The frontend expects the ID as a string for strict equality checks
    d["id"] = str(d["id"])
    # The frontend expects tags as a JSON array, not a comma string
    d["tags"] = [t.strip() for t in d["tags"].split(",")] if d["tags"] else []
    return d


@app.route("/")
def index():
    """Render the main single-page application."""
    return render_template("index.html")


# --- API Routes ---


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Return dashboard statistics."""
    conn = get_db_connection()
    today = date.today().isoformat()

    total = conn.execute("SELECT COUNT(*) FROM Vocabulary").fetchone()[0]
    due = conn.execute(
        "SELECT COUNT(*) FROM Vocabulary WHERE next_review <= ?", (today,)
    ).fetchone()[0]

    # Mastered = interval >= 21 days
    mastered = conn.execute(
        "SELECT COUNT(*) FROM Vocabulary WHERE interval >= 21"
    ).fetchone()[0]
    learning = total - mastered
    conn.close()

    # Mock 7-day history to prevent the UI chart from crashing
    daily = []
    for i in range(6, -1, -1):
        d = (date.today() - timedelta(days=i)).isoformat()
        daily.append({"date": d, "count": 0})

    return jsonify(
        {
            "total": total,
            "due": due,
            "mastered": mastered,
            "learning": learning,
            "daily": daily,
        }
    )


@app.route("/api/decks", methods=["GET"])
def get_decks():
    """Return an aggregated list of decks and their card counts."""
    conn = get_db_connection()
    today = date.today().isoformat()

    rows = conn.execute(
        """
        SELECT deck_id, 
               COUNT(*) as total, 
               SUM(CASE WHEN next_review <= ? THEN 1 ELSE 0 END) as due 
        FROM Vocabulary 
        GROUP BY deck_id
        """,
        (today,),
    ).fetchall()
    conn.close()

    decks = []
    for r in rows:
        decks.append(
            {
                "id": r["deck_id"],
                "name": str(r["deck_id"]).replace("-", " ").title(),
                "total": r["total"],
                "due": r["due"] if r["due"] else 0,
            }
        )
    return jsonify(decks)


@app.route("/api/review", methods=["GET"])
def get_review_queue():
    """Return an array of cards due for review today."""
    deck_id = request.args.get("deck_id")
    today = date.today().isoformat()
    conn = get_db_connection()

    if deck_id:
        rows = conn.execute(
            "SELECT * FROM Vocabulary WHERE next_review <= ? AND deck_id = ?",
            (today, deck_id),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM Vocabulary WHERE next_review <= ?", (today,)
        ).fetchall()

    conn.close()
    return jsonify([row_to_dict(r) for r in rows])


@app.route("/api/review/<card_id>", methods=["POST"])
def submit_review(card_id):
    """Process a review score and calculate the next review date."""
    body = request.get_json()
    quality = int(body.get("quality", 0))

    conn = get_db_connection()
    card = conn.execute("SELECT * FROM Vocabulary WHERE id = ?", (card_id,)).fetchone()

    if not card:
        conn.close()
        return jsonify({"error": "Card not found"}), 404

    # Run the SM-2 Math logic from sm2.py
    n, ef, i = calculate_next_review(
        quality=quality,
        repetition=card["repetition"],
        ef=card["ef"],
        interval=card["interval"],
    )

    new_date = (date.today() + timedelta(days=i)).isoformat()

    conn.execute(
        """
        UPDATE Vocabulary 
        SET repetition = ?, ef = ?, interval = ?, next_review = ?
        WHERE id = ?
        """,
        (n, ef, i, new_date, card_id),
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "next_review": new_date})


@app.route("/api/cards", methods=["GET", "POST"])
def handle_cards():
    """Fetch all cards or create a new single card."""
    conn = get_db_connection()

    if request.method == "POST":
        body = request.get_json()
        front = body.get("front")
        back = body.get("back")
        deck_id = body.get("deck_id", "default")
        tags = ",".join(body.get("tags", []))
        today = date.today().isoformat()

        cursor = conn.execute(
            """
            INSERT INTO Vocabulary 
            (front, back, deck_id, tags, next_review) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (front, back, deck_id, tags, today),
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return jsonify({"id": str(new_id)}), 201

    # GET route
    rows = conn.execute("SELECT * FROM Vocabulary").fetchall()
    conn.close()
    return jsonify([row_to_dict(r) for r in rows])


@app.route("/api/cards/<card_id>", methods=["PUT", "DELETE"])
def update_delete_card(card_id):
    """Edit or delete a specific card."""
    conn = get_db_connection()

    if request.method == "DELETE":
        conn.execute("DELETE FROM Vocabulary WHERE id = ?", (card_id,))
        conn.commit()
        conn.close()
        return jsonify({"ok": True})

    # PUT route
    body = request.get_json()
    front = body.get("front")
    back = body.get("back")
    tags = ",".join(body.get("tags", []))

    conn.execute(
        "UPDATE Vocabulary SET front = ?, back = ?, tags = ? WHERE id = ?",
        (front, back, tags, card_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/bulk", methods=["POST"])
def bulk_import():
    """Import multiple cards at once."""
    body = request.get_json()
    deck_id = body.get("deck_id", "imported")
    pairs = body.get("pairs", [])
    today = date.today().isoformat()

    conn = get_db_connection()
    inserted = 0
    for p in pairs:
        conn.execute(
            """
            INSERT INTO Vocabulary 
            (front, back, deck_id, next_review) 
            VALUES (?, ?, ?, ?)
            """,
            (p.get("front"), p.get("back"), deck_id, today),
        )
        inserted += 1

    conn.commit()
    conn.close()
    return jsonify({"added": inserted}), 201


if __name__ == "__main__":
    app.run(debug=True)
