import os
import subprocess
import sqlite3

DB_PATH = "./database/song_monitoring.db"
SONG_DIR = "./samples"  # Folder containing .wav files

def create_database(db_path):
    """
    Creates an SQLite database and defines the schema for storing song metadata, samples, and fingerprints.

    Args:
        db_path (str): The path to the SQLite database file.
    """
    try:
        # Connect to the SQLite database (this will create the file if it doesn't exist)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute each CREATE TABLE statement
        cursor.execute('''
            CREATE TABLE songs (
                song_id INTEGER PRIMARY KEY AUTOINCREMENT,
                song_title VARCHAR(255) NOT NULL,
                artist_name VARCHAR(255) NOT NULL,
                album_title VARCHAR(255) NOT NULL,
                release_date DATE,
                duration INT,
                isrc VARCHAR(15) UNIQUE,
                mbid VARCHAR(36) UNIQUE
            )
        ''')

        cursor.execute('''
            CREATE TABLE samples (
                sample_id INTEGER PRIMARY KEY AUTOINCREMENT,
                song_id INT NOT NULL,
                sample_path VARCHAR(255) NOT NULL,
                FOREIGN KEY (song_id) REFERENCES songs(song_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE fingerprints (
                fingerprint_id INTEGER PRIMARY KEY AUTOINCREMENT,
                song_id INT NOT NULL,
                duration INT NOT NULL,
                FOREIGN KEY (song_id) REFERENCES songs(song_id)
            )
        ''')

        # Commit the changes and close the connection
        conn.commit()
        print(f"Database '{db_path}' created and schema defined successfully.")

    except sqlite3.Error as e:
        print(f"Error creating database or defining schema: {e}")
        if conn:
            conn.rollback()  # Rollback changes in case of an error
    finally:
        if conn:
            conn.close() 

def get_fingerprint(filepath):
    try:
        result = subprocess.run(["fpcalc", filepath], capture_output=True, text=True)
        for line in result.stdout.splitlines():
             if line.startswith("FINGERPRINT="):
                return line.split("=")[1].strip()
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return None

def store_fingerprint(title, artist, fingerprint):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO known_tracks (title, artist, fingerprint) VALUES (?, ?, ?)",
                   (title, artist, fingerprint))
    conn.commit()
    conn.close()

def process_folder():
    create_database("./database/tunetrack.db")
    for filename in os.listdir(SONG_DIR):
        if filename.endswith(".mp3"):
            title = os.path.splitext(filename)[0]
            artist = "Unknown"  # Or extract from metadata if available
            full_path = os.path.join(SONG_DIR, filename)
            print(f"Processing: {filename}")
            fp = get_fingerprint(full_path)
            if fp:
                store_fingerprint(title, artist, fp)
                print(f"[+] Stored fingerprint for {title}")
            else:
                print(f"[!] Failed to fingerprint {title}")

if __name__ == "__main__":
    process_folder()
