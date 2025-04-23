import os
import subprocess
import sys
import sqlite3
from pydub import AudioSegment  # Import pydub

def calculate_fingerprint(file_path):
    """
    Calculates the audio fingerprint of a given audio file using fpcalc.

    Args:
        file_path (str): The path to the audio file.

    Returns:
        str: The audio fingerprint string, or None if an error occurs.
    """
    command = [
        "fpcalc",
        file_path,
        "-raw",  # Get the raw fingerprint
    ]
    try:
        # Execute the fpcalc command and capture the output
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        # The fingerprint is on the last line of the output, after "FINGERPRINT="
        for line in result.stdout.splitlines():
            if "FINGERPRINT=" in line:
                return line.split("=")[1].strip()
        return None  # Return None if no fingerprint found
    except subprocess.CalledProcessError as e:
        print(f"Error calculating fingerprint for {file_path}: {e}")
        print(f"fpcalc output (stderr): {e.stderr}")
        return None
    except FileNotFoundError:
        print("Error: fpcalc command not found.  Please ensure fpcalc is installed and in your system's PATH.")
        sys.exit(1)


def calculate_percentage_match(hash1, hash2):
    """
    Calculates the percentage of matching characters between two hexadecimal hashes.

    Args:
        hash1 (str): The first hexadecimal hash string.
        hash2 (str): The second hexadecimal hash string.

    Returns:
        float: The percentage of matching characters, or 0 if either hash is empty.
    """
    if not hash1 or not hash2:
        return 0.0  # Avoid division by zero and handle empty cases

    min_length = min(len(hash1), len(hash2))
    matches = sum(1 for i in range(min_length) if hash1[i] == hash2[i])
    return (matches / min_length) * 100.0

def create_database(db_path):
    """
    Creates an SQLite database and defines the schema for storing song metadata,
    samples, and fingerprints.

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
                sample_duration INT NOT NULL,
                FOREIGN KEY (song_id) REFERENCES songs(song_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE fingerprints (
                fingerprint_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sample_id INT NOT NULL,
                fingerprint VARCHAR(255) NOT NULL,
                FOREIGN KEY (sample_id) REFERENCES samples(sample_id)
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


def insert_song_data(db_path, song_title, artist_name, album_title, release_date, duration, isrc, mbid):
    """
    Inserts song data into the songs table.

    Args:
        db_path (str): Path to the SQLite database.
        song_title (str): Title of the song.
        artist_name (str): Name of the artist.
        album_title (str): Title of the album.
        release_date (str): Release date of the song.
        duration (int): Duration of the song in seconds.
        isrc (str): ISRC code of the song.
        mbid (str): MusicBrainz ID of the song.

    Returns:
        int: The song_id of the inserted song, or -1 on error.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO songs (song_title, artist_name, album_title, release_date, duration, isrc, mbid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (song_title, artist_name, album_title, release_date, duration, isrc, mbid))

        conn.commit()
        return cursor.lastrowid  # Return the newly inserted song_id

    except sqlite3.Error as e:
        print(f"Error inserting song data: {e}")
        if conn:
            conn.rollback()
        return -1
    finally:
        if conn:
            conn.close()


def insert_sample_data(db_path, song_id, sample_path, sample_duration):
    """
    Inserts sample data into the samples table.

    Args:
        db_path (str): Path to the SQLite database.
        song_id (int): ID of the song to which the sample belongs.
        sample_path (str): Path to the sample file.
        sample_duration (int): Duration of the sample.

    Returns:
        int: The sample_id of the inserted sample, or -1 on error.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO samples (song_id, sample_path, sample_duration)
            VALUES (?, ?, ?)
        ''', (song_id, sample_path, sample_duration))

        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error inserting sample data: {e}")
        if conn:
            conn.rollback()
        return -1
    finally:
        if conn:
            conn.close()


def insert_fingerprint_data(db_path, sample_id, fingerprint):
    """
    Inserts fingerprint data into the fingerprints table.

    Args:
        db_path (str): Path to the SQLite database.
        sample_id (int): ID of the sample to which the fingerprint belongs.
        fingerprint (str): The audio fingerprint string.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO fingerprints (sample_id, fingerprint)
            VALUES (?, ?)
        ''', (sample_id, fingerprint))

        conn.commit()
    except sqlite3.Error as e:
        print(f"Error inserting fingerprint data: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def create_sample_pydub(input_file, output_folder, sample_duration=10):
    """Creates an audio sample using pydub."""
    try:
        audio = AudioSegment.from_file(input_file)
        duration_ms = sample_duration * 1000
        sample = audio[0:duration_ms]  # Get the first 'sample_duration' seconds
        sample_name = os.path.splitext(os.path.basename(input_file))[0] + f"_sample_{sample_duration}s.wav"
        output_path = os.path.join(output_folder, sample_name)
        sample.export(output_path, format="wav")
        print(f"Created sample: {output_path} from {input_file} using pydub")
        return output_path
    except Exception as e:
        print(f"Error creating sample with pydub from {input_file}: {e}")
        return None

def process_audio_file(db_path, input_file, output_folder, sample_duration=10):
    """
    Processes a single audio file: converts it to WAV, creates a sample using pydub,
    calculates fingerprints for both the full song and the sample,
    and stores the data in the database.

    Args:
        db_path (str): Path to the SQLite database.
        input_file (str): Path to the input audio file.
        output_folder (str): Path to the folder to save the sample.
        sample_duration (int): Duration of the sample in seconds.
    """
    # 1. Convert to WAV (if necessary)
    if not input_file.lower().endswith(".wav"):
        wav_file = os.path.join(output_folder, os.path.splitext(os.path.basename(input_file))[0] + ".wav")
        command = [
            "ffmpeg",
            "-i",
            input_file,
            wav_file,
        ]
        result = subprocess.run(command, capture_output=True)
        if result.returncode == 0:
            print(f"Attempted conversion: {input_file} to {wav_file}")
            input_file = wav_file  # Use the .wav file for subsequent processing
        else:
            print(f"Error during conversion of {input_file}:")
            print(f"FFmpeg output (stderr): {result.stderr.decode()}")
            return  # Stop processing if conversion failed

    # 2. Create the audio sample using pydub
    sample_file = create_sample_pydub(input_file, output_folder, sample_duration)

    if sample_file:
        # 3. Calculate fingerprints
        full_song_fingerprint = calculate_fingerprint(input_file)
        sample_fingerprint = calculate_fingerprint(sample_file)

        if not full_song_fingerprint or not sample_fingerprint:
            print(f"Failed to calculate fingerprints for {input_file} or {sample_file}. Skipping database insertion.")
            return

        # 4. Store data in the database
        song_title = os.path.splitext(os.path.basename(input_file))[0]  # Basic title from filename
        artist_name = "Unknown Artist"  # Replace with actual extraction if available
        album_title = "Unknown Album"    # Replace with actual extraction
        release_date = None              # Replace with actual extraction
        duration = sample_duration
        isrc = None
        mbid = None

        song_id = insert_song_data(db_path, song_title, artist_name, album_title, release_date, duration, isrc, mbid)
        if song_id == -1:
            print(f"Failed to insert song data for {input_file}. Skipping sample and fingerprint insertion.")
            return

        sample_id = insert_sample_data(db_path, song_id, sample_file, sample_duration)
        if sample_id == -1:
            print(f"Failed to insert sample data for {sample_file}. Skipping fingerprint insertion.")
            return

        insert_fingerprint_data(db_path, sample_id, sample_fingerprint)
        print(f"Inserted fingerprint for sample {sample_file} into the database.")

        # 5. Calculate and print match percentage
        truncated_full_song_fingerprint = full_song_fingerprint[:len(sample_fingerprint)]
        percentage_match = calculate_percentage_match(truncated_full_song_fingerprint, sample_fingerprint)
        print(f"Fingerprint match: {percentage_match:.2f}%")

    else:
        print(f"Skipping fingerprinting and database insertion for {input_file} due to sample creation failure.")


def main(db_path, input_folder, output_folder):
    """
    Main function to process audio files in a folder, create samples,
    calculate fingerprints, and store data in a database.

    Args:
        db_path (str): Path to the SQLite database.
        input_folder (str): Path to the folder containing audio files.
        output_folder (str): Path to the folder to save the samples.
    """
    # Create the database if it doesn't exist
    create_database(db_path)

    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Process each audio file in the input folder
    for filename in os.listdir(input_folder):
        input_file = os.path.join(input_folder, filename)
        if os.path.isfile(input_file) and filename.lower().endswith(('.mp3', '.wav', '.flac', '.ogg', '.aac')):
            process_audio_file(db_path, input_file, output_folder)
        else:
            print(f"Skipping: {input_file} (not a supported audio file or not a file)")


if __name__ == "__main__":
    # Specify the database and folder paths
    db_file = "./tunetrack.db"  # Use the same path as in create_database
    input_folder = "./samples"  # Replace with the path to your folder containing audio files
    output_folder = "./samples/wav"  # Replace with the path to your desired output folder

    # Create dummy input folder and files if they don't exist
    if not os.path.exists(input_folder):
        os.makedirs(input_folder)
        # Create a dummy wav file for testing if it doesn't exist
        dummy_wav = os.path.join(input_folder, "dummy.wav")
        if not os.path.exists(dummy_wav):
            try:
                # Create a silent 1-second wav file using sox (if available)
                subprocess.run(["sox", "-n", "-r", "44100", "-c", "1", "-b", "16", dummy_wav, "trim", "0", "1"], check=True, capture_output=True)
                print(f"Created dummy WAV file: {dummy_wav}")
            except FileNotFoundError:
                print("Warning: sox not found, cannot create dummy WAV file.")
            except subprocess.CalledProcessError as e:
                print(f"Error creating dummy WAV file: {e}")

    # Run the main function
    main(db_file, input_folder, output_folder)
