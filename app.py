from flask import Flask, render_template, request, jsonify, session
import json
import os
import uuid
from datetime import datetime, timedelta
import math

app = Flask(__name__)
app.secret_key = "srs-vocab-engine-secret-2024"

DATA_FILE = "data/cards.json"

# --- SM-2 Algorithm ---
def sm2(quality, repetitions, easiness, interval):
    """
    SM-2 spaced repetition algorithm.
    quality: 0-5 (0=complete blackout, 5=perfect)
    Returns: (new_repetitions, new_easiness, new_interval)
    """
    if quality < 3:
        repetitions = 0
        interval = 1
    else:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * easiness)
        repetitions += 1

    easiness = max(1.3, easiness + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    return repetitions, easiness, interval


def load_data():
    if not os.path.exists(DATA_FILE):
        os.makedirs("data", exist_ok=True)
        return {"cards": [], "decks": []}
    with open(DATA_FILE) as f:
        return json.load(f)


def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_due_cards(cards, deck_id=None):
    now = datetime.utcnow().isoformat()
    due = []
    for c in cards:
        if deck_id and c.get("deck_id") != deck_id:
            continue
        if c.get("next_review", now) <= now:
            due.append(c)
    return due


# --- Routes ---
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/cards", methods=["GET"])
def get_cards():
    data = load_data()
    deck_id = request.args.get("deck_id")
    cards = data["cards"]
    if deck_id:
        cards = [c for c in cards if c.get("deck_id") == deck_id]
    return jsonify(cards)


@app.route("/api/cards", methods=["POST"])
def add_card():
    data = load_data()
    body = request.json
    card = {
        "id": str(uuid.uuid4()),
        "front": body["front"],
        "back": body["back"],
        "deck_id": body.get("deck_id", "default"),
        "tags": body.get("tags", []),
        "created_at": datetime.utcnow().isoformat(),
        "next_review": datetime.utcnow().isoformat(),
        "repetitions": 0,
        "easiness": 2.5,
        "interval": 1,
        "history": [],
    }
    data["cards"].append(card)
    save_data(data)
    return jsonify(card), 201


@app.route("/api/cards/<card_id>", methods=["PUT"])
def update_card(card_id):
    data = load_data()
    body = request.json
    for c in data["cards"]:
        if c["id"] == card_id:
            c["front"] = body.get("front", c["front"])
            c["back"] = body.get("back", c["back"])
            c["tags"] = body.get("tags", c["tags"])
            save_data(data)
            return jsonify(c)
    return jsonify({"error": "Not found"}), 404


@app.route("/api/cards/<card_id>", methods=["DELETE"])
def delete_card(card_id):
    data = load_data()
    data["cards"] = [c for c in data["cards"] if c["id"] != card_id]
    save_data(data)
    return jsonify({"ok": True})


@app.route("/api/review", methods=["GET"])
def get_review_queue():
    data = load_data()
    deck_id = request.args.get("deck_id")
    due = get_due_cards(data["cards"], deck_id)
    # Shuffle-like sort: due first, then by next_review
    due.sort(key=lambda c: c.get("next_review", ""))
    return jsonify(due)


@app.route("/api/review/<card_id>", methods=["POST"])
def submit_review(card_id):
    data = load_data()
    body = request.json
    quality = int(body["quality"])  # 0-5

    for c in data["cards"]:
        if c["id"] == card_id:
            reps, ease, interval = sm2(
                quality,
                c.get("repetitions", 0),
                c.get("easiness", 2.5),
                c.get("interval", 1),
            )
            c["repetitions"] = reps
            c["easiness"] = ease
            c["interval"] = interval
            next_review = (datetime.utcnow() + timedelta(days=interval)).isoformat()
            c["next_review"] = next_review
            c.setdefault("history", []).append({
                "date": datetime.utcnow().isoformat(),
                "quality": quality,
                "interval": interval,
            })
            save_data(data)
            return jsonify(c)
    return jsonify({"error": "Not found"}), 404


@app.route("/api/decks", methods=["GET"])
def get_decks():
    data = load_data()
    # Auto-generate deck list from cards
    deck_ids = list(set(c.get("deck_id", "default") for c in data["cards"]))
    decks = []
    now = datetime.utcnow().isoformat()
    for did in deck_ids:
        cards = [c for c in data["cards"] if c.get("deck_id") == did]
        due = [c for c in cards if c.get("next_review", now) <= now]
        decks.append({
            "id": did,
            "name": did.replace("-", " ").title(),
            "total": len(cards),
            "due": len(due),
        })
    return jsonify(decks)


@app.route("/api/stats", methods=["GET"])
def get_stats():
    data = load_data()
    cards = data["cards"]
    now = datetime.utcnow().isoformat()
    total = len(cards)
    due = len([c for c in cards if c.get("next_review", now) <= now])
    mastered = len([c for c in cards if c.get("interval", 1) >= 21])
    learning = total - mastered

    # Reviews per day (last 7 days)
    daily = {}
    for c in cards:
        for h in c.get("history", []):
            day = h["date"][:10]
            daily[day] = daily.get(day, 0) + 1

    last7 = []
    for i in range(6, -1, -1):
        d = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        last7.append({"date": d, "count": daily.get(d, 0)})

    return jsonify({
        "total": total,
        "due": due,
        "mastered": mastered,
        "learning": learning,
        "daily": last7,
    })


@app.route("/api/bulk", methods=["POST"])
def bulk_import():
    data = load_data()
    body = request.json
    deck_id = body.get("deck_id", "imported")
    pairs = body.get("pairs", [])
    added = []
    now = datetime.utcnow().isoformat()
    for p in pairs:
        card = {
            "id": str(uuid.uuid4()),
            "front": p["front"],
            "back": p["back"],
            "deck_id": deck_id,
            "tags": p.get("tags", []),
            "created_at": now,
            "next_review": now,
            "repetitions": 0,
            "easiness": 2.5,
            "interval": 1,
            "history": [],
        }
        data["cards"].append(card)
        added.append(card)
    save_data(data)
    return jsonify({"added": len(added), "cards": added}), 201


if __name__ == "__main__":
    app.run(debug=True)