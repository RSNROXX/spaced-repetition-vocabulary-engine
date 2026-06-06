"""
Database initialization module.
Sets up SQLite database and seeds it with initial UI-compatible 
data
"""

import sqlite3
from datetime import date

def init_database():
    """Connects to the Vocabulary database file and inserts default 
    testing data"""
    conn = sqlite3.connect('vocab.db')
    cursor = conn.cursor()

    # Create the Vocabulary table based on our exact schema
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            front TEXT NOT NULL,
            back TEXT NOT NULL,
            deck_id TEXT DEFAULT 'default',
            tags TEXT,
            next_review DATE NOT NULL,
            repetition INTEGER DEFAULT 0,
            ef REAL DEFAULT 2.5,
            interval INTEGER DEFAULT 0
        )
        """
    )

    # Clear existing data in case running this script multiple times while testing
    cursor.execute('DELETE FROM Vocabulary')

    # Seed the database with two dummy words. 
    # Notice the date is set to TODAY so the GET route will 
    #  immediately find them.
    today = date.today().isoformat()
    dummy_data = [
        (
            "der Bahnhof", "train station", 
            "german-101", "", 
            today, 0, 
            2.5, 0
        ),
        (
            "die Anmeldung", "registration", 
            "german-101", "", 
            today, 0, 
            2.5, 0
        )
    ]

    # Force complete wipe of the old table
    cursor.execute("DROP TABLE IS EXISTS Vocabulary")

    # Create the Vocabulary table
    cursor.execute('''
        INSERT INTO Vocabulary (front, back, deck_id, tags, next_review, repetition, ef, interval)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', dummy_data
    )

    conn.commit()
    conn.close()
    
    print("Database 'vocab.db' successfully initialized and seeded.")

if __name__ == "__main__":
    init_database()