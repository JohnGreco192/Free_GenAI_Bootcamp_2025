# song_vocab_generator/agent/agent.py
import os
import sys # Import sys
from typing import Optional, List, Dict

# Add the parent directory to sys.path to enable proper module imports
# This assumes your 'song_vocab_generator' directory is directly under /content/
# If your notebook is in /content/ and song_vocab_generator is also in /content/,
# then adding /content/ is correct.
project_root = os.path.abspath(os.path.join(os.getcwd(), 'song_vocab_generator'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    # Also add the directory *containing* song_vocab_generator, if it's not the current working directory
    # This handles cases where song_vocab_generator is a subfolder of the notebook's directory
    parent_dir_of_project_root = os.path.abspath(os.path.join(project_root, os.pardir))
    if parent_dir_of_project_root not in sys.path:
        sys.path.insert(0, parent_dir_of_project_root)


print(f"Current Working Directory: {os.getcwd()}")
print(f"sys.path: {sys.path}")


# Import the tools we've developed
# Ensure __init__.py files exist in song_vocab_generator/ and song_vocab_generator/tools/
from song_vocab_generator.tools.lyric_search import search_and_retrieve_lyrics
from song_vocab_generator.tools.vocabulary_extraction import extract_vocabulary
from song_vocab_generator.tools.database_storage import initialize_database, store_vocabulary, get_vocabulary_for_song

class SongToVocabAgent:
    """
    The Song-to-Vocab Agent orchestrates the process of finding song lyrics,
    extracting vocabulary from them using an LLM, and storing the vocabulary
    in a SQLite database.
    """
    def __init__(self):
        """
        Initializes the agent and ensures the database is set up.
        """
        print("Initializing SongToVocabAgent...")
        initialize_database() # Ensure the database table exists on agent initialization
        print("SongToVocabAgent initialized.")

    def process_song(self, song_name: str, artist_name: Optional[str] = None) -> bool:
        """
        Processes a given song to find its lyrics, extract vocabulary, and store it.

        Args:
            song_name (str): The name of the song.
            artist_name (Optional[str]): The name of the artist.

        Returns:
            bool: True if the entire process was successful, False otherwise.
        """
        print(f"\n--- Agent Processing Request for '{song_name}' by {artist_name or 'Unknown Artist'} ---")

        # Step 1: Lyric Search & Retrieval
        print("Step 1: Searching and retrieving lyrics...")
        lyrics = search_and_retrieve_lyrics(song_name, artist_name)
        if not lyrics:
            print("Agent failed: Could not retrieve lyrics.")
            return False
        print("Step 1: Lyrics retrieved successfully.")

        # Step 2: Vocabulary Extraction
        print("Step 2: Extracting vocabulary from lyrics using LLM...")
        vocabulary_list = extract_vocabulary(lyrics)
        if not vocabulary_list:
            print("Agent failed: Could not extract vocabulary.")
            return False
        print(f"Step 2: Extracted {len(vocabulary_list)} vocabulary items.")

        # Step 3: Database Storage
        print("Step 3: Storing extracted vocabulary in the database...")
        storage_success = store_vocabulary(song_name, artist_name, vocabulary_list)
        if not storage_success:
            print("Agent failed: Could not store vocabulary in the database.")
            return False
        print("Step 3: Vocabulary stored successfully.")

        print(f"--- Agent Process for '{song_name}' by {artist_name or 'Unknown Artist'} Completed Successfully ---")
        return True

# --- Test Script for Song-to-Vocab Agent ---
def test_song_to_vocab_agent():
    """
    Tests the Song-to-Vocab Agent end-to-end.
    Note: This test requires GOOGLE_API_KEY and GOOGLE_CSE_ID to be set as environment variables
    and for the tool modules to be correctly importable.
    """
    print("\n--- Testing Song-to-Vocab Agent (End-to-End) ---")

    # Ensure API keys are set for the tools.
    # In a Colab environment, these would typically be loaded from userdata.
    # For this test, we'll ensure they are set as environment variables.
    from google.colab import userdata
    import os
    try:
        os.environ['GOOGLE_API_KEY'] = userdata.get('GOOGLE_API_KEY')
        os.environ['GOOGLE_CSE_ID'] = userdata.get('GOOGLE_CSE_ID')
        print("Environment variables for API key and CSE ID set for testing.")
    except Exception as e:
        print(f"Could not set environment variables from secrets: {e}")
        print("Please ensure your GOOGLE_API_KEY and GOOGLE_CSE_ID are correctly set in Colab secrets.")
        return # Exit test if secrets can't be accessed

    # Instantiate the agent
    agent = SongToVocabAgent()

    # Test Case 1: Successful processing of "Bohemian Rhapsody" by Queen
    song_name_1 = "Bohemian Rhapsody"
    artist_name_1 = "Queen"
    print(f"\nAttempting to process: '{song_name_1}' by {artist_name_1}")
    process_success_1 = agent.process_song(song_name_1, artist_name_1)
    print(f"Agent processing result for '{song_name_1}': {process_success_1}")

    # Verify data in DB after successful processing
    if process_success_1:
        # Re-import get_vocabulary_for_song to ensure it's using the correct path if sys.path was just modified
        from song_vocab_generator.tools.database_storage import get_vocabulary_for_song
        retrieved_vocab_1 = get_vocabulary_for_song(song_name_1, artist_name_1)
        if retrieved_vocab_1:
            print(f"Successfully retrieved {len(retrieved_vocab_1)} vocabulary items for '{song_name_1}' from DB.")
            # You can add more specific checks here, e.g., check for specific words
            if len(retrieved_vocab_1) > 0:
                print("Test passed for successful song processing and DB storage.")
            else:
                print("Test failed: No vocabulary found in DB after successful processing.")
        else:
            print("Test failed: Could not retrieve vocabulary from DB.")
    else:
        print("Test failed: Agent processing was not successful.")

    # Test Case 2: Song not found (example of expected failure)
    song_name_2 = "NonExistentSong12345"
    artist_name_2 = "ImaginaryArtist"
    print(f"\nAttempting to process: '{song_name_2}' by {artist_name_2} (expecting failure)")
    process_success_2 = agent.process_song(song_name_2, artist_name_2)
    print(f"Agent processing result for '{song_name_2}': {process_success_2}")
    if not process_success_2:
        print("Test passed: Agent correctly handled song not found scenario.")
    else:
        print("Test failed: Agent unexpectedly succeeded for a non-existent song.")

    # Clean up the database file after all tests
    # Ensure DB_FILE is accessible from database_storage module
    from song_vocab_generator.tools.database_storage import DB_FILE
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"\nCleaned up: Removed database file '{DB_FILE}'.")

# To run the test, uncomment the line below:
test_song_to_vocab_agent()