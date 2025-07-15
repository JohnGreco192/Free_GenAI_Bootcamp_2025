# song_vocab_generator/tools/vocabulary_extraction.py
import json
import os
from typing import List, Dict, Optional

# Get API key from userdata for Colab environment
try:
    from google.colab import userdata
    API_KEY = userdata.get('GOOGLE_API_KEY')
    if not API_KEY:
        print("Warning: GOOGLE_API_KEY not found in Colab secrets. Vocabulary extraction may fail.")
except ImportError:
    # If not in Colab, try environment variable
    API_KEY = os.environ.get('GOOGLE_API_KEY', "")
    if not API_KEY:
        print("Warning: GOOGLE_API_KEY not found in environment variables. Vocabulary extraction may fail.")

import requests # Add the import here, right before the function definition

def extract_vocabulary(lyrics_text: str) -> Optional[List[Dict[str, str]]]:
    """
    Analyzes a given block of song lyrics and identifies a list of vocabulary words
    along with their definitions using an LLM.

    Args:
        lyrics_text (str): The raw lyrics content obtained from the Lyric Search & Retrieval Tool.

    Returns:
        Optional[List[Dict[str, str]]]: A list of dictionaries, where each dictionary
        represents a vocabulary word and its definition. Returns None if extraction fails.
    """
    if not lyrics_text:
        print("Error: No lyrics text provided for vocabulary extraction.")
        return None

    if not API_KEY:
        print("Error: API key is not set. Cannot perform vocabulary extraction.")
        return None

    # Define the prompt for the LLM
    prompt = f"""
From the following song lyrics, identify a list of vocabulary words that might be
unfamiliar to a language learner. For each identified word, provide a concise definition.
Focus on contextually relevant terms.

Return the output as a JSON array of objects, where each object has two keys:
"word" and "definition".

Example format:
[
    {{
        "word": "melancholy",
        "definition": "a feeling of pensive sadness, typically with no obvious cause."
    }},
    {{
        "word": "serenade",
        "definition": "a piece of music sung or played in the open air, typically by a man to his beloved one."
    }}
]

Lyrics:
---
{lyrics_text}
---
"""

    # Prepare the payload for the Gemini API call
    chatHistory = []
    chatHistory.append({ "role": "user", "parts": [{ "text": prompt }] })

    payload = {
        "contents": chatHistory,
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "word": { "type": "STRING" },
                        "definition": { "type": "STRING" }
                    },
                    "propertyOrdering": ["word", "definition"]
                }
            }
        }
    }

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

    print("Calling LLM for vocabulary extraction...")
    try:
        response = requests.post(api_url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        result = response.json()

        if result.get('candidates') and result['candidates'][0].get('content') and \
           result['candidates'][0]['content'].get('parts') and \
           result['candidates'][0]['content']['parts'][0].get('text'):

            json_string = result['candidates'][0]['content']['parts'][0]['text']
            vocabulary_list = json.loads(json_string)

            # Basic validation of the structure
            if isinstance(vocabulary_list, list) and \
               all(isinstance(item, dict) and 'word' in item and 'definition' in item for item in vocabulary_list):
                print("Vocabulary extracted successfully.")
                return vocabulary_list
            else:
                print("LLM response did not conform to the expected JSON schema.")
                print(f"Raw LLM response text: {json_string}")
                return None
        else:
            print("LLM response did not contain expected content.")
            print(f"Full LLM response: {json.dumps(result, indent=2)}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API for vocabulary extraction: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from LLM response: {e}")
        print(f"Raw LLM response text (if available): {response.text if 'response' in locals() else 'N/A'}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during vocabulary extraction: {e}")
        return None

# --- Test Script for Vocabulary Extraction Tool ---
# This test requires a GOOGLE_API_KEY to be available (e.g., via Colab secrets or directly set)
# and an internet connection to call the Gemini API.

def test_extract_vocabulary():
    print("\n--- Testing Vocabulary Extraction Tool ---")

    # This part would ideally be handled during agent initialization or setup
    # For direct execution in Colab, ensure GOOGLE_API_KEY is set in userdata.
    # The API_KEY is now handled globally at the top of the file.
    if not API_KEY:
        print("Warning: API_KEY is not set for the test. Please ensure it's loaded.")
        return

    sample_lyrics = """
    Is this the real life?
    Is this just fantasy?
    Caught in a landslide,
    No escape from reality.
    Open your eyes,
    Look up to the skies and see,
    I'm just a poor boy, I need no sympathy,
    Because I'm easy come, easy go,
    Little high, little low,
    Any way the wind blows doesn't really matter to me, to me.

    Mama, just killed a man,
    Put a gun against his head, pulled my trigger, now he's dead.
    Mama, life had just begun,
    But now I've gone and thrown it all away.
    Mama, ooh,
    Didn't mean to make you cry,
    If I'm not back again this time tomorrow,
    Carry on, carry on, as if nothing really matters.
    """

    print("Calling vocabulary extraction with sample lyrics...")
    vocabulary = extract_vocabulary(sample_lyrics)

    if vocabulary:
        print("\nExtracted Vocabulary:")
        for item in vocabulary:
            print(f"- Word: {item.get('word')}, Definition: {item.get('definition')}")
        
        # Add a simple validation check
        if len(vocabulary) > 0 and all('word' in v and 'definition' in v for v in vocabulary):
            print("\nTest passed: Vocabulary list is not empty and has correct structure.")
        else:
            print("\nTest failed: Vocabulary list is empty or has incorrect structure.")
    else:
        print("\nTest failed: No vocabulary extracted.")

# To run the test, uncomment the line below:
# test_extract_vocabulary()
