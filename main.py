import os
import subprocess
import sqlite3

DB_PATH = "./database/song_monitoring.db"
SONG_DIR = "./samples"  # Folder containing .wav files

def create_tracks_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS known_tracks (title TEXT NOT NULL, artist TEXT NOT NULL, fingerprint TEXT NOT NULL)")
    conn.commit()
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
    create_tracks_table()
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
