import streamlit as st
import requests
import json
import random
import base64
import os
from dotenv import load_dotenv
from streamlit_drawable_canvas import st_canvas # Import the drawing component

# Load environment variables from env.txt
load_dotenv("env.txt")

# --- Constants and Configuration ---
API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# --- Helper Functions for LLM Calls ---

def call_gemini_api(prompt, response_schema=None):
    """
    Makes a call to the Gemini API with the given prompt and optional response schema.
    Returns the JSON response from the API.
    """
    if not API_KEY:
        st.error("GOOGLE_API_KEY is not set. Please configure it in your env.txt file.")
        return None

    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}]
    }
    if response_schema:
        payload["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }

    try:
        response = requests.post(f"{GEMINI_API_URL}?key={API_KEY}", headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        if result.get("candidates") and result["candidates"][0].get("content") and \
           result["candidates"][0]["content"].get("parts"):
            return result["candidates"][0]["content"]["parts"][0].get("text")
        else:
            st.error("Failed to get a valid response from the LLM.")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        return None
    except json.JSONDecodeError:
        st.error("Failed to decode JSON response from LLM.")
        return None

# --- Application State Management ---

def initialize_state():
    """Initializes session state variables."""
    if 'app_state' not in st.session_state:
        st.session_state.app_state = 'SETUP'
    if 'word_collection' not in st.session_state:
        st.session_state.word_collection = []
    if 'current_english_sentence' not in st.session_state:
        st.session_state.current_english_sentence = ''
    if 'current_japanese_word' not in st.session_state: # Add state for Japanese word
        st.session_state.current_japanese_word = ''
    if 'grading_results' not in st.session_state:
        st.session_state.grading_results = None
    if 'is_loading' not in st.session_state:
        st.session_state.is_loading = False
    if 'error' not in st.session_state:
        st.session_state.error = ''
    if 'drawing_data' not in st.session_state: # Add state for drawing data
        st.session_state.drawing_data = None

def set_loading(status, error_msg=""):
    """Helper to set loading state and clear/set errors."""
    st.session_state.is_loading = status
    st.session_state.error = error_msg
    if status:
        st.session_state.grading_results = None

def fetch_word_collection():
    """
    Simulates fetching word collection from a backend.
    In a real app, this would be a GET request to localhost:5000/db/groupId/id/raw.
    """
    set_loading(True)
    try:
        import time
        time.sleep(1)
        st.session_state.word_collection = [
            {'japanese': '本', 'english': 'book'},
            {'japanese': '車', 'english': 'car'},
            {'japanese': 'ラーメン', 'english': 'ramen'},
            {'japanese': '寿司', 'english': 'sushi'},
            {'japanese': '飲む', 'english': 'to drink'},
            {'japanese': '食べる', 'english': 'to eat'},
            {'japanese': '会う', 'english': 'to meet'},
            {'japanese': '明日', 'english': 'tomorrow'},
            {'japanese': '今日', 'english': 'today'},
            {'japanese': '昨日', 'english': 'yesterday'},
            {'japanese': '学校', 'english': 'school'},
            {'japanese': '行く', 'english': 'to go'},
            {'japanese': '読む', 'english': 'to read'},
            {'japanese': '友達', 'english': 'friend'},
            {'japanese': '公園', 'english': 'park'},
            {'japanese': '遊ぶ', 'english': 'to play'},
            {'japanese': '見る', 'english': 'to see'},
            {'japanese': '話す', 'english': 'to speak'},
            {'japanese': '聞く', 'english': 'to listen'},
            {'japanese': '買う', 'english': 'to buy'},
        ]
    except Exception as e:
        set_loading(False, f"Failed to fetch word collection: {e}")
    finally:
        set_loading(False)

def generate_sentence():
    """Generates an English sentence using an LLM."""
    if not st.session_state.word_collection:
        set_loading(False, 'Word collection is empty. Cannot generate sentence.')
        return

    set_loading(True)
    try:
        random_word = random.choice(st.session_state.word_collection)
        st.session_state.current_japanese_word = random_word['japanese'] # Store the Japanese word
        # Ensure Japanese word is correctly embedded in the prompt
        prompt = (
            f"Generate a simple English sentence using the Japanese word \"{random_word['japanese']}\" "
            f"(meaning \"{random_word['english']}\"). The grammar should be scoped to eJLPTN5 grammar. "
            "You can use the following vocabulary to construct a simple sentence: - simple objects eg. book, car, ramen, sushi "
            "- simple verbs, to drink, to eat, to meet - simple times eg. tomorrow, today, yesterday. "
            "The sentence should be in English."
        )
        print(f"DEBUG: Prompt sent to LLM: {prompt}") # Debug print for the prompt

        response_text = call_gemini_api(prompt)
        if response_text:
            st.session_state.current_english_sentence = response_text
            st.session_state.app_state = 'PRACTICE'
            st.session_state.drawing_data = None # Clear drawing data for new sentence
        else:
            st.session_state.error = 'Failed to generate sentence. Please try again.'
    except Exception as e:
        st.session_state.error = f'Error generating sentence: {e}'
    finally:
        set_loading(False)

def submit_for_review(input_data):
    """Simulates the Grading System, handling either image data or drawing data."""
    set_loading(True)
    try:
        # --- Simulate MangaOCR Transcription ---
        # This part is still simulated. In a real app, you'd send input_data
        # (either image bytes or drawing data) to a backend service.
        # For now, we'll use a hardcoded Japanese transcription for demonstration.
        # Simulate a wrong transcription for drawing input
        simulated_transcription = "これはまちがいです。" # "This is wrong."

        # --- LLM for Literal Translation ---
        translation_prompt = f"Translate the following Japanese text literally into English: \"{simulated_transcription}\""
        translated_transcription = call_gemini_api(translation_prompt)
        if not translated_transcription:
            translated_transcription = 'Translation failed.'

        # --- LLM for Grading ---
        grading_prompt = (
            f"Given the original English sentence \"{st.session_state.current_english_sentence}\", "
            f"the user's simulated Japanese transcription \"{simulated_transcription}\", "
            f"and its literal English translation \"{translated_transcription}\", "
            f"and the target Japanese word \"{st.session_state.current_japanese_word}\", " # Include target word
            "provide a letter grade (A, B, C, D, F) and a brief description (1-2 sentences) "
            "explaining whether the attempt was accurate to the English sentence and offering suggestions for improvement. "
            "Also, provide the correct Japanese sentence based on the original English sentence and target Japanese word."
        )
        grading_schema = {
            "type": "OBJECT",
            "properties": {
                "grade": {"type": "STRING"},
                "description": {"type": "STRING"},
                "correct_japanese_sentence": {"type": "STRING"} # Add correct sentence to schema
            },
            "propertyOrdering": ["grade", "description", "correct_japanese_sentence"]
        }
        grading_response_json = call_gemini_api(grading_prompt, response_schema=grading_schema)

        if grading_response_json:
            parsed_json = json.loads(grading_response_json)
            st.session_state.grading_results = {
                'transcription': simulated_transcription,
                'translation': translated_transcription,
                'grade': parsed_json.get('grade', 'N/A'),
                'description': parsed_json.get('description', 'No description provided.'),
                'correct_japanese_sentence': parsed_json.get('correct_japanese_sentence', 'Correct sentence not provided.') # Store correct sentence
            }
            st.session_state.app_state = 'REVIEW'
        else:
            st.session_state.error = 'Failed to grade. Unexpected LLM response.'
    except json.JSONDecodeError:
        st.session_state.error = 'Failed to parse grading results from LLM.'
    except Exception as e:
        st.session_state.error = f'Error submitting for review: {e}'
    finally:
        set_loading(False)

# --- UI Components ---

def setup_state_ui():
    """Renders the UI for the Setup State."""
    st.markdown(
        """
        <div style="text-align: center;">
            <p style="font-size: 1.125rem; color: #4b5563; margin-bottom: 1.5rem;">
                Welcome! Press the button below to generate your first Japanese sentence practice question.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button(
        "Generate Sentence",
        key="generate_sentence_button",
        help="Click to generate a new English sentence for practice."
    ):
        generate_sentence()

def practice_state_ui():
    """Renders the UI for the Practice State."""
    st.markdown(
        """
        <div style="text-align: center;">
            <h2 style="font-size: 1.5rem; font-weight: 600; color: #1f2937; margin-bottom: 1rem;">
                Practice Time!
            </h2>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Display the Japanese word for practice
    st.markdown(
        """
        <p style="font-size: 1.25rem; color: #374151; margin-bottom: 1.5rem; padding: 1rem; background-color: #f9fafb; border-radius: 0.5rem; border: 1px solid #e5e7eb; text-align: center;">
            <span style="font-weight: bold;">Japanese Word:</span>
        </p>
        """,
        unsafe_allow_html=True
    )
    st.write(st.session_state.current_japanese_word) # Display the Japanese word

    # Display the English sentence
    st.markdown(
        """
        <p style="font-size: 1.25rem; color: #374151; margin-bottom: 1.5rem; padding: 1rem; background-color: #f9fafb; border-radius: 0.5rem; border: 1px solid #e5e7eb; text-align: center;">
            <span style="font-weight: bold;">English Sentence:</span>
        </p>
        """,
        unsafe_allow_html=True
    )
    st.write(st.session_state.current_english_sentence)

    st.markdown(
        """
        <label style="display: block; color: #374151; font-size: 0.875rem; font-weight: bold; margin-bottom: 0.5rem;">
            Draw your handwritten Japanese attempt:
        </label>
        """,
        unsafe_allow_html=True
    )

    # Create a canvas component
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
        stroke_width=3,
        stroke_color="#000000", # Black stroke color
        background_color="#eee", # Light gray background
        height=200,
        width=400,
        drawing_mode="freedraw",
        key="canvas",
    )

    # Get the image data from the canvas
    if canvas_result.image_data is not None:
        # Convert the image data (numpy array) to bytes and then base64
        from PIL import Image
        import io
        img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        st.session_state.drawing_data = base64.b64encode(buffered.getvalue()).decode('utf-8')


    submit_disabled = st.session_state.drawing_data is None
    if st.button(
        "Submit for Review",
        key="submit_review_button",
        disabled=submit_disabled,
        help="Submit your drawing for grading."
    ):
        if st.session_state.drawing_data:
            submit_for_review(st.session_state.drawing_data)
        else:
            st.warning("Please draw something on the canvas before submitting.")


def review_state_ui():
    """Renders the UI for the Review State."""
    grading_results = st.session_state.grading_results
    if not grading_results:
        st.markdown("<div style='text-align: center; color: #6b7280;'>No review results available.</div>", unsafe_allow_html=True)
        return

    def get_grade_color(grade):
        grade_map = {
            'A': '#10b981',
            'B': '#3b82f6',
            'C': '#f59e0b',
            'D': '#f97316',
            'F': '#ef4444',
        }
        return grade_map.get(grade.upper(), '#1f2937')

    st.markdown(
        f"""
        <div style="text-align: center;">
            <h2 style="font-size: 1.5rem; font-weight: 600; color: #1f2937; margin-bottom: 1rem;">
                Review Your Attempt!
            </h2>
            <p style="font-size: 1.25rem; color: #374151; margin-bottom: 1.5rem; padding: 1rem; background-color: #f9fafb; border-radius: 0.5rem; border: 1px solid #e5e7eb;">
                <span style="font-weight: bold;">Original English Sentence:</span> {st.session_state.current_english_sentence}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div style="background-color: #ffffff; padding: 1.5rem; border-radius: 0.5rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); border: 1px solid #e2e8f0; margin-bottom: 1.5rem; text-align: left;">
            <div style="margin-bottom: 1rem;">
                <p style="font-size: 1.125rem; font-weight: 600; color: #1f2937;">Transcription of Image:</p>
                <p style="color: #374151; font-style: italic; background-color: #f3f4f6; padding: 0.75rem; border-radius: 0.375rem;">{grading_results['transcription']}</p>
            </div>
            <div style="margin-bottom: 1rem;">
                <p style="font-size: 1.125rem; font-weight: 600; color: #1f2937;">Translation of Transcription:</p>
                <p style="color: #374151; font-style: italic; background-color: #f3f4f6; padding: 0.75rem; border-radius: 0.375rem;">{grading_results['translation']}</p>
            </div>
            <div style="margin-bottom: 1rem;">
                <p style="font-size: 1.125rem; font-weight: 600; color: #1f2937;">Grade:</p>
                <p style="font-size: 3rem; font-weight: 800; color: {get_grade_color(grading_results['grade'])};">{grading_results['grade']}</p>
            </div>
            <div>
                <p style="font-size: 1.125rem; font-weight: 600; color: #1f2937;">Description & Suggestions:</p>
                <p style="color: #374151; background-color: #f3f4f6; padding: 0.75rem; border-radius: 0.375rem;">{grading_results['description']}</p>
            </div>
             <div style="margin-top: 1.5rem;">
                <p style="font-size: 1.125rem; font-weight: 600; color: #1f2937;">Correct Japanese Sentence:</p>
                <p style="color: #10b981; font-weight: bold; background-color: #f0fdf4; padding: 0.75rem; border-radius: 0.375rem;">{grading_results['correct_japanese_sentence']}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "Next Question",
        key="next_question_button",
        help="Generate a new practice question."
    ):
        generate_sentence()


# --- Main Application Layout ---

def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(
        page_title="Japanese Sentence Practice",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
        html, body, [class*="st-emotion"] {
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        .stApp {
            background: linear-gradient(to bottom right, #e0f2fe, #e9d5ff);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1rem;
        }
        .st-emotion-cache-1c7y2kl {
            background-color: #ffffff;
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            width: 100%;
            max-width: 48rem;
            border: 1px solid #e2e8f0;
        }
        h1 {
            font-size: 2.25rem;
            font-weight: 800;
            text-align: center;
            color: #1f2937;
            margin-bottom: 2rem;
        }
        button {
            width: 100%;
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            font-weight: bold;
            color: #ffffff;
            transition: all 0.3s ease-in-out;
            transform: scale(1);
        }
        button:hover {
            transform: scale(1.05);
        }
        button:focus {
            outline: none;
            box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.5);
        }
        .stButton>button {
            background-color: #2563eb;
        }
        .stButton>button:hover {
            background-color: #1d4ed8;
        }
        .stButton>button:disabled {
            background-color: #9ca3af;
            cursor: not-allowed;
            transform: none;
        }
        .stFileUploader label {
            font-weight: bold;
            color: #374151;
            margin-bottom: 0.5rem;
        }
        .stFileUploader div[data-testid="stFileUploaderDropzone"] {
            border: 1px dashed #d1d5db;
            border-radius: 0.5rem;
            padding: 1rem;
            text-align: center;
            background-color: #f9fafb;
        }
        .stFileUploader div[data-testid="stFileUploaderDropzone"] svg {
            color: #6b7280;
        }
        .stFileUploader div[data-testid="stFileUploaderDropzone"] p {
            color: #6b7280;
        }
        .stFileUploader div[data-testid="stFileUploaderFileName"] {
            background-color: #e0f2fe;
            border-radius: 0.5rem;
            padding: 0.5rem;
            margin-top: 0.5rem;
            color: #2563eb;
            font-weight: 600;
        }
        .stAlert {
            border-radius: 0.5rem;
            padding: 0.75rem 1rem;
            margin-bottom: 1rem;
        }
        .stAlert.error {
            background-color: #fee2e2;
            border-color: #f87171;
            color: #b91c1c;
        }
        .stAlert.warning {
            background-color: #fffbeb;
            border-color: #fcd34d;
            color: #b45309;
        }
        .spinner {
            border: 4px solid rgba(0, 0, 0, 0.1);
            border-left-color: #2563eb;
            border-radius: 50%;
            width: 32px;
            height: 32px;
            animation: spin 1s linear infinite;
            margin: 0 auto 0.5rem auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    initialize_state()

    st.title("Japanese Sentence Practice")

    if not st.session_state.word_collection:
        fetch_word_collection()

    if st.session_state.is_loading:
        st.markdown(
            """
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 1rem;">
                <div class="spinner"></div>
                <p style="margin-top: 0.5rem; color: #4b5563;">Loading...</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    elif st.session_state.error:
        st.error(st.session_state.error)
    else:
        if st.session_state.app_state == 'SETUP':
            setup_state_ui()
        elif st.session_state.app_state == 'PRACTICE':
            practice_state_ui()
        elif st.session_state.app_state == 'REVIEW':
            review_state_ui()

if __name__ == '__main__':
    main()