# song_vocab_generator/tools/database_storage.py
import sqlite3
import os # Import os for file operations in test script
from typing import List, Dict, Optional

# Define the database file name
DB_FILE = 'vocabulary.db'

def initialize_database():
    """
    Initializes the SQLite database and creates the 'vocabulary' table if it doesn't exist.
    The table includes a unique constraint on (song_name, artist_name, word) to prevent duplicates.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Create the vocabulary table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vocabulary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                song_name TEXT NOT NULL,
                artist_name TEXT,
                word TEXT NOT NULL,
                definition TEXT NOT NULL,
                UNIQUE(song_name, artist_name, word) ON CONFLICT IGNORE
            )
        ''')
        conn.commit()
        print(f"Database '{DB_FILE}' initialized and 'vocabulary' table ensured.")
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
    finally:
        if conn:
            conn.close()

def store_vocabulary(
    song_name: str,
    artist_name: Optional[str],
    vocabulary_list: List[Dict[str, str]]
) -> bool:
    """
    Stores a list of vocabulary words and their definitions into the database.
    Handles duplicate entries by ignoring them (ON CONFLICT IGNORE).

    Args:
        song_name (str): The name of the song.
        artist_name (Optional[str]): The name of the artist.
        vocabulary_list (List[Dict[str, str]]): A list of dictionaries,
                                                 each with 'word' and 'definition'.

    Returns:
        bool: True if storage was successful, False otherwise.
    """
    if not vocabulary_list:
        print("No vocabulary to store.")
        return True # Considered successful if nothing to store

    conn = None
    stored_count = 0
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Insert data into the table one by one to ensure ON CONFLICT IGNORE works per row
        for item in vocabulary_list:
            word = item.get('word')
            definition = item.get('definition')
            if word and definition:
                try:
                    cursor.execute('''
                        INSERT INTO vocabulary (song_name, artist_name, word, definition)
                        VALUES (?, ?, ?, ?)
                    ''', (song_name, artist_name, word, definition))
                    # Check if a row was actually inserted (not ignored due to conflict)
                    if cursor.rowcount > 0:
                        stored_count += 1
                except sqlite3.IntegrityError:
                    # This specific error should ideally be caught by ON CONFLICT IGNORE
                    # but catching it explicitly here provides extra robustness and logging.
                    print(f"  Duplicate entry ignored for word '{word}' in '{song_name}' by '{artist_name}'.")
                except sqlite3.Error as e:
                    print(f"  Error inserting word '{word}': {e}")
            else:
                print(f"Skipping invalid vocabulary item: {item} (missing 'word' or 'definition')")
        
        conn.commit()
        print(f"Successfully stored {stored_count} unique vocabulary items for '{song_name}' by {artist_name}.")
        return True
    except sqlite3.Error as e:
        print(f"Error storing vocabulary batch: {e}") # This catches errors outside individual inserts
        return False
    finally:
        if conn:
            conn.close()

def get_vocabulary_for_song(
    song_name: str,
    artist_name: Optional[str] = None
) -> Optional[List[Dict[str, str]]]:
    """
    Retrieves all vocabulary words and definitions stored for a specific song and artist.

    Args:
        song_name (str): The name of the song.
        artist_name (Optional[str]): The name of the artist.

    Returns:
        Optional[List[Dict[str, str]]]: A list of dictionaries, each with 'word' and 'definition',
                                         or None if an error occurs.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        query = "SELECT word, definition FROM vocabulary WHERE song_name = ?"
        params = [song_name]

        if artist_name:
            query += " AND artist_name = ?"
            params.append(artist_name)
        else:
            query += " AND artist_name IS NULL" # Handle cases where artist_name was stored as NULL

        cursor.execute(query, params)
        results = cursor.fetchall()

        vocabulary_list = []
        for row in results:
            vocabulary_list.append({"word": row[0], "definition": row[1]})
        
        print(f"Retrieved {len(vocabulary_list)} vocabulary items for '{song_name}' by {artist_name}.")
        return vocabulary_list

    except sqlite3.Error as e:
        print(f"Error retrieving vocabulary: {e}")
        return None
    finally:
        if conn:
            conn.close()

# --- Test Script for Database Storage Tool ---
def test_database_storage():
    print("\n--- Testing Database Storage Tool ---")

    # 1. Initialize the database
    initialize_database()

    # 2. Prepare sample data
    test_song_name = "Test Song"
    test_artist_name = "Test Artist"
    sample_vocab_list_1 = [
        {"word": "test_word_1", "definition": "definition_1"},
        {"word": "test_word_2", "definition": "definition_2"}
    ]
    sample_vocab_list_2 = [
        {"word": "test_word_3", "definition": "definition_3"},
        {"word": "test_word_1", "definition": "definition_1_updated"} # Duplicate word, should be ignored
    ]
    sample_vocab_list_no_artist = [
        {"word": "no_artist_word", "definition": "no_artist_def"}
    ]

    # 3. Store first set of vocabulary
    print(f"\nStoring first set of vocabulary for '{test_song_name}' by '{test_artist_name}'...")
    success1 = store_vocabulary(test_song_name, test_artist_name, sample_vocab_list_1)
    print(f"Storage success: {success1}")

    # 4. Store second set of vocabulary (includes a duplicate)
    print(f"\nStoring second set of vocabulary for '{test_song_name}' by '{test_artist_name}' (with duplicate)...")
    success2 = store_vocabulary(test_song_name, test_artist_name, sample_vocab_list_2)
    print(f"Storage success: {success2}")

    # 5. Store vocabulary for a song with no artist
    print(f"\nStoring vocabulary for '{test_song_name}' with no artist...")
    success3 = store_vocabulary(test_song_name, None, sample_vocab_list_no_artist)
    print(f"Storage success: {success3}")

    # 6. Retrieve and verify
    print(f"\nRetrieving vocabulary for '{test_song_name}' by '{test_artist_name}'...")
    retrieved_vocab = get_vocabulary_for_song(test_song_name, test_artist_name)
    if retrieved_vocab is not None:
        print("Retrieved Vocabulary:")
        for item in retrieved_vocab:
            print(f"- Word: {item['word']}, Definition: {item['definition']}")
        
        # Verification: Should contain test_word_1, test_word_2, test_word_3 (test_word_1_updated ignored)
        expected_words = {"test_word_1", "test_word_2", "test_word_3"}
        actual_words = {item['word'] for item in retrieved_vocab}
        if actual_words == expected_words:
            print("Test passed: Retrieved vocabulary matches expected (duplicates handled).")
        else:
            print(f"Test failed: Retrieved words {actual_words} do not match expected {expected_words}.")
    else:
        print("Test failed: Could not retrieve vocabulary.")

    # 7. Retrieve vocabulary for song with no artist
    print(f"\nRetrieving vocabulary for '{test_song_name}' with no artist...")
    retrieved_no_artist_vocab = get_vocabulary_for_song(test_song_name, None)
    if retrieved_no_artist_vocab is not None:
        print("Retrieved No Artist Vocabulary:")
        for item in retrieved_no_artist_vocab:
            print(f"- Word: {item['word']}, Definition: {item['definition']}")
        
        if {"no_artist_word"} == {item['word'] for item in retrieved_no_artist_vocab}:
            print("Test passed: Retrieved no-artist vocabulary matches expected.")
        else:
            print("Test failed: Retrieved no-artist vocabulary does not match expected.")
    else:
        print("Test failed: Could not retrieve no-artist vocabulary.")

    # Clean up: remove the database file after testing
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"\nCleaned up: Removed database file '{DB_FILE}'.")

# To run the test, uncomment the line below:
#test_database_storage()
