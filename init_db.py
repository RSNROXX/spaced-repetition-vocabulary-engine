import sqlite3
from datetime import date

def init_database():
    # Connects to the database file (creates it if it doesn't exist)
    conn = sqlite3.connect('vocab.db')
    cursor = conn.cursor()

    # Create the Vocabulary table based on our exact schema
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Vocabulary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL,
        translation TEXT NOT NULL,
        next_review DATE NOT NULL,
        repetition INTEGER DEFAULT 0,
        ef REAL DEFAULT 2.5,
        interval INTEGER DEFAULT 0
    )
    ''')

    # Clear existing data in case you run this script multiple times while testing
    cursor.execute('DELETE FROM Vocabulary')

    # Seed the database with two dummy words. 
    # Notice the date is set to TODAY so your GET route will immediately find them.
    today = date.today().isoformat()
    dummy_data = [
        ("der Bahnhof", "train station", today, 0, 2.5, 0),
        ("die Anmeldung", "registration", today, 0, 2.5, 0)
    ]

    cursor.executemany('''
    INSERT INTO Vocabulary (word, translation, next_review, repetition, ef, interval)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', dummy_data)

    conn.commit()
    conn.close()
    
    print("Database 'vocab.db' successfully initialized and seeded.")

if __name__ == "__main__":
    init_database()