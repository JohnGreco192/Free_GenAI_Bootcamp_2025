#!pip install Flask pyngrok

#import os
#os.environ["NGROK_AUTH_TOKEN"] = 'your token'

# -*- coding: utf-8 -*-
"""
Quebec French Language Learning Portal Backend API

This Flask application provides the backend API for a language learning portal.
It manages vocabulary, study sessions, and review statistics using an SQLite3 database.

Designed to be run in Google Colab.

Database Schema:
- words: Stores individual Quebec French vocabulary words.
    - id (Primary Key): Unique identifier for each word.
    - french_word (String, Required): The word in Quebec French.
    - pronunciation_guide (String, Required): A pronunciation guide (e.g., phonetic spelling).
    - english_translation (String, Required): English translation of the word.
    - parts (JSON, Required): Word components/details (e.g., gender, plural form, example sentence).
- groups: Manages collections of words.
    - id (Primary Key): Unique identifier for each group.
    - name (String, Required): Name of the group.
    - words_count (Integer, Default: 0): Counter cache for the number of words in the group.
- word_groups: Join-table for many-to-many relationship between words and groups.
    - word_id (Foreign Key): References words.id.
    - group_id (Foreign Key): References groups.id.
- study_activities: Defines different types of study activities available.
    - id (Primary Key): Unique identifier for each activity.
    - name (String, Required): Name of the activity (e.g., "Flashcards", "Quiz").
    - url (String, Required): The full URL of the study activity.
- study_sessions: Records individual study sessions.
    - id (Primary Key): Unique identifier for each session.
    - group_id (Foreign Key): References groups.id.
    - study_activity_id (Foreign Key): References study_activities.id.
    - created_at (Timestamp, Default: Current Time): When the session was created.
- word_review_items: Tracks individual word reviews within study sessions.
    - id (Primary Key): Unique identifier for each review.
    - word_id (Foreign Key): References words.id.
    - study_session_id (Foreign Key): References study_sessions.id.
    - correct (Boolean, Required): Whether the answer was correct.
    - created_at (Timestamp, Default: Current Time): When the review occurred.
"""

import sqlite3
import json
import os # Import os module to access environment variables
from flask import Flask, request, jsonify, g
from datetime import datetime
from pyngrok import ngrok # Import ngrok for Colab tunneling

# --- Configuration ---
DATABASE = 'lang_portal.db'
PER_PAGE = 10 # Default items per page for pagination

app = Flask(__name__)

# --- Database Helper Functions ---

def get_db():
    """Establishes a database connection or returns the existing one."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row # Return rows as dictionary-like objects
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initializes the database schema and populates with sample data."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                french_word TEXT NOT NULL,
                pronunciation_guide TEXT NOT NULL,
                english_translation TEXT NOT NULL,
                parts TEXT NOT NULL -- Stored as JSON string
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                words_count INTEGER DEFAULT 0
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS word_groups (
                word_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                PRIMARY KEY (word_id, group_id),
                FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE,
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                study_activity_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
                FOREIGN KEY (study_activity_id) REFERENCES study_activities(id) ON DELETE CASCADE
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS word_review_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER NOT NULL,
                study_session_id INTEGER NOT NULL,
                correct BOOLEAN NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE,
                FOREIGN KEY (study_session_id) REFERENCES study_sessions(id) ON DELETE CASCADE
            );
        """)
        db.commit()

        # --- Sample Data Population ---
        # Check if data already exists to prevent duplicates on re-init
        cursor.execute("SELECT COUNT(*) FROM words;")
        if cursor.fetchone()[0] == 0:
            print("Populating sample data...")
            # Sample Quebec French words
            words_data = [
                ("Bonjour", "bon-jour", "Hello", {"gender": "N/A", "notes": "Common greeting"}),
                ("Bienvenue", "byen-vuh-noo", "Welcome", {"gender": "N/A", "notes": "Used for welcoming"}),
                ("Comment ça va?", "koh-mahn sah vah", "How are you?", {"gender": "N/A", "notes": "Informal greeting"}),
                ("Je suis", "zhuh swee", "I am", {"gender": "N/A", "notes": "To introduce oneself"}),
                ("Merci", "mer-see", "Thank you", {"gender": "N/A", "notes": "Common expression of gratitude"}),
                ("Au revoir", "oh ruh-vwahr", "Goodbye", {"gender": "N/A", "notes": "Common farewell"}),
                ("Oui", "wee", "Yes", {"gender": "N/A", "notes": "Affirmative answer"}),
                ("Non", "noh", "No", {"gender": "N/A", "notes": "Negative answer"}),
                ("S'il vous plaît", "seel voo pleh", "Please (formal)", {"gender": "N/A", "notes": "Polite request"}),
                ("De rien", "duh ree-ahn", "You're welcome", {"gender": "N/A", "notes": "Response to thank you"}),
                ("Tabarnak", "ta-bar-nak", "Damn it (Quebecois swear word)", {"gender": "N/A", "notes": "Very common Quebecois expletive, often used as an interjection. Use with caution!"}),
                ("C'est plate", "say plat", "It's boring/lame (Quebecois slang)", {"gender": "N/A", "notes": "Informal way to say something is dull or disappointing."}),
                ("Chum", "chum", "Boyfriend/Buddy (Quebecois slang)", {"gender": "N/A", "notes": "Can mean a close friend or a romantic partner."}),
                ("Blé d'Inde", "blay daind", "Corn (Quebecois specific)", {"gender": "N/A", "notes": "Standard French uses 'maïs'."}),
                ("Poutine", "poo-teen", "Poutine (Quebecois dish)", {"gender": "N/A", "notes": "Iconic Quebecois dish of fries, cheese curds, and gravy."}),
            ]
            for fr_word, pron_guide, en_trans, parts_json in words_data:
                cursor.execute(
                    "INSERT INTO words (french_word, pronunciation_guide, english_translation, parts) VALUES (?, ?, ?, ?)",
                    (fr_word, pron_guide, en_trans, json.dumps(parts_json))
                )

            # Sample groups
            groups_data = [
                ("Basic Greetings",),
                ("Common Phrases",),
                ("Quebecois Slang",),
                ("Quebecois Culture",)
            ]
            for name in groups_data:
                cursor.execute("INSERT INTO groups (name) VALUES (?)", name)

            # Sample study activities
            activities_data = [
                ("Flashcards", "https://example.com/flashcards"),
                ("Quiz", "https://example.com/quiz"),
                ("Listening Practice", "https://example.com/listen")
            ]
            for name, url in activities_data:
                cursor.execute("INSERT INTO study_activities (name, url) VALUES (?, ?)", (name, url))

            db.commit()

            # Link words to groups and update words_count
            # Fetch word and group IDs
            words_map = {row['french_word']: row['id'] for row in cursor.execute("SELECT id, french_word FROM words").fetchall()}
            groups_map = {row['name']: row['id'] for row in cursor.execute("SELECT id, name FROM groups").fetchall()}

            word_group_links = [
                ("Bonjour", "Basic Greetings"),
                ("Bienvenue", "Basic Greetings"),
                ("Comment ça va?", "Basic Greetings"),
                ("Je suis", "Common Phrases"),
                ("Merci", "Common Phrases"),
                ("Au revoir", "Basic Greetings"),
                ("Oui", "Common Phrases"),
                ("Non", "Common Phrases"),
                ("S'il vous plaît", "Common Phrases"),
                ("De rien", "Common Phrases"),
                ("Tabarnak", "Quebecois Slang"),
                ("C'est plate", "Quebecois Slang"),
                ("Chum", "Quebecois Slang"),
                ("Blé d'Inde", "Quebecois Culture"),
                ("Poutine", "Quebecois Culture"),
            ]

            for word_name, group_name in word_group_links:
                word_id = words_map.get(word_name)
                group_id = groups_map.get(group_name)
                if word_id and group_id:
                    try:
                        cursor.execute(
                            "INSERT INTO word_groups (word_id, group_id) VALUES (?, ?)",
                            (word_id, group_id)
                        )
                        cursor.execute(
                            "UPDATE groups SET words_count = words_count + 1 WHERE id = ?",
                            (group_id,)
                        )
                    except sqlite3.IntegrityError:
                        # Handle cases where a word might already be in a group (e.g., if re-running init_db)
                        pass
            db.commit()
            print("Sample data populated successfully.")
        else:
            print("Database already contains data. Skipping sample data population.")


# --- API Routes ---

@app.route('/')
def index():
    """Root endpoint for basic API information."""
    return jsonify({"message": "Welcome to the Quebec French Language Portal API!"})

@app.route('/words', methods=['GET'])
def get_words():
    """
    GET /words - Get paginated list of words with review statistics.
    Query Parameters:
        page (int): Page number (default: 1)
        sort_by (str): Sort field ('french_word', 'pronunciation_guide', 'english_translation', 'correct_count', 'wrong_count') (default: 'french_word')
        order (str): Sort order ('asc' or 'desc') (default: 'asc')
    """
    db = get_db()
    cursor = db.cursor()

    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'french_word')
    order = request.args.get('order', 'asc').upper()

    # Validate sort_by and order
    valid_sort_fields = ['french_word', 'pronunciation_guide', 'english_translation', 'correct_count', 'wrong_count']
    if sort_by not in valid_sort_fields:
        return jsonify({"error": f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"}), 400
    if order not in ['ASC', 'DESC']:
        return jsonify({"error": "Invalid order. Must be 'asc' or 'desc'"}), 400

    offset = (page - 1) * PER_PAGE

    # Base query for words with review counts
    query = f"""
        SELECT
            w.id,
            w.french_word,
            w.pronunciation_guide,
            w.english_translation,
            w.parts,
            SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END) AS correct_count,
            SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END) AS wrong_count
        FROM
            words w
        LEFT JOIN
            word_review_items wri ON w.id = wri.word_id
        GROUP BY
            w.id, w.french_word, w.pronunciation_guide, w.english_translation, w.parts
        ORDER BY
            {sort_by} {order}
        LIMIT ? OFFSET ?;
    """
    words = cursor.execute(query, (PER_PAGE, offset)).fetchall()

    # Get total count for pagination metadata
    total_words = cursor.execute("SELECT COUNT(*) FROM words;").fetchone()[0]
    total_pages = (total_words + PER_PAGE - 1) // PER_PAGE

    result = []
    for word in words:
        word_dict = dict(word)
        # Convert 'parts' from JSON string back to Python object
        word_dict['parts'] = json.loads(word_dict['parts'])
        # Ensure correct_count and wrong_count are integers, default to 0 if NULL
        word_dict['correct_count'] = int(word_dict['correct_count'] or 0)
        word_dict['wrong_count'] = int(word_dict['wrong_count'] or 0)
        result.append(word_dict)

    return jsonify({
        "words": result,
        "pagination": {
            "total_items": total_words,
            "total_pages": total_pages,
            "current_page": page,
            "per_page": PER_PAGE
        }
    })

@app.route('/groups', methods=['GET'])
def get_groups():
    """
    GET /groups - Get paginated list of word groups with word counts.
    Query Parameters:
        page (int): Page number (default: 1)
        sort_by (str): Sort field ('name', 'words_count') (default: 'name')
        order (str): Sort order ('asc' or 'desc') (default: 'asc')
    """
    db = get_db()
    cursor = db.cursor()

    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'name')
    order = request.args.get('order', 'asc').upper()

    # Validate sort_by and order
    valid_sort_fields = ['name', 'words_count']
    if sort_by not in valid_sort_fields:
        return jsonify({"error": f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"}), 400
    if order not in ['ASC', 'DESC']:
        return jsonify({"error": "Invalid order. Must be 'asc' or 'desc'"}), 400

    offset = (page - 1) * PER_PAGE

    query = f"""
        SELECT
            id,
            name,
            words_count
        FROM
            groups
        ORDER BY
            {sort_by} {order}
        LIMIT ? OFFSET ?;
    """
    groups = cursor.execute(query, (PER_PAGE, offset)).fetchall()

    # Get total count for pagination metadata
    total_groups = cursor.execute("SELECT COUNT(*) FROM groups;").fetchone()[0]
    total_pages = (total_groups + PER_PAGE - 1) // PER_PAGE

    result = [dict(group) for group in groups]

    return jsonify({
        "groups": result,
        "pagination": {
            "total_items": total_groups,
            "total_pages": total_pages,
            "current_page": page,
            "per_page": PER_PAGE
        }
    })

@app.route('/groups/<int:group_id>', methods=['GET'])
def get_group_words(group_id):
    """
    GET /groups/:id - Get words from a specific group.
    Path Parameters:
        group_id (int): ID of the group.
    Query Parameters:
        page (int): Page number (default: 1)
        sort_by (str): Sort field ('french_word', 'pronunciation_guide', 'english_translation') (default: 'french_word')
        order (str): Sort order ('asc' or 'desc') (default: 'asc')
    """
    db = get_db()
    cursor = db.cursor()

    # Check if group exists
    group = cursor.execute("SELECT id, name FROM groups WHERE id = ?", (group_id,)).fetchone()
    if not group:
        return jsonify({"error": "Group not found"}), 404

    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'french_word')
    order = request.args.get('order', 'asc').upper()

    # Validate sort_by and order
    valid_sort_fields = ['french_word', 'pronunciation_guide', 'english_translation']
    if sort_by not in valid_sort_fields:
        return jsonify({"error": f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"}), 400
    if order not in ['ASC', 'DESC']:
        return jsonify({"error": "Invalid order. Must be 'asc' or 'desc'"}), 400

    offset = (page - 1) * PER_PAGE

    query = f"""
        SELECT
            w.id,
            w.french_word,
            w.pronunciation_guide,
            w.english_translation,
            w.parts
        FROM
            words w
        JOIN
            word_groups wg ON w.id = wg.word_id
        WHERE
            wg.group_id = ?
        ORDER BY
            w.{sort_by} {order}
        LIMIT ? OFFSET ?;
    """
    words = cursor.execute(query, (group_id, PER_PAGE, offset)).fetchall()

    # Get total count of words in this group for pagination metadata
    total_words_in_group = cursor.execute("SELECT COUNT(*) FROM word_groups WHERE group_id = ?;", (group_id,)).fetchone()[0]
    total_pages = (total_words_in_group + PER_PAGE - 1) // PER_PAGE

    result = []
    for word in words:
        word_dict = dict(word)
        word_dict['parts'] = json.loads(word_dict['parts'])
        result.append(word_dict)

    return jsonify({
        "group_id": group_id,
        "group_name": group['name'],
        "words": result,
        "pagination": {
            "total_items": total_words_in_group,
            "total_pages": total_pages,
            "current_page": page,
            "per_page": PER_PAGE
        }
    })

@app.route('/study_sessions', methods=['POST'])
def create_study_session():
    """
    POST /study_sessions - Create a new study session for a group.
    Request Body (JSON):
        group_id (int): ID of the group to study (required).
        study_activity_id (int): ID of the study activity (required).
    """
    db = get_db()
    cursor = db.cursor()
    data = request.get_json()

    group_id = data.get('group_id')
    study_activity_id = data.get('study_activity_id')

    if not group_id or not study_activity_id:
        return jsonify({"error": "group_id and study_activity_id are required"}), 400

    # Validate group_id
    group_exists = cursor.execute("SELECT 1 FROM groups WHERE id = ?", (group_id,)).fetchone()
    if not group_exists:
        return jsonify({"error": "Group not found"}), 404

    # Validate study_activity_id
    activity_exists = cursor.execute("SELECT 1 FROM study_activities WHERE id = ?", (study_activity_id,)).fetchone()
    if not activity_exists:
        return jsonify({"error": "Study activity not found"}), 404

    try:
        cursor.execute(
            "INSERT INTO study_sessions (group_id, study_activity_id) VALUES (?, ?)",
            (group_id, study_activity_id)
        )
        db.commit()
        session_id = cursor.lastrowid
        return jsonify({"message": "Study session created successfully", "session_id": session_id}), 201
    except sqlite3.Error as e:
        db.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@app.route('/study_sessions/<int:session_id>/review', methods=['POST'])
def log_review_attempt(session_id):
    """
    POST /study_sessions/:id/review - Log a review attempt for a word during a study session.
    Path Parameters:
        session_id (int): ID of the study session.
    Request Body (JSON):
        word_id (int): ID of the word reviewed (required).
        correct (bool): Whether the answer was correct (required).
    """
    db = get_db()
    cursor = db.cursor()
    data = request.get_json()

    word_id = data.get('word_id')
    correct = data.get('correct')

    if word_id is None or correct is None:
        return jsonify({"error": "word_id and correct status are required"}), 400

    if not isinstance(correct, bool):
        return jsonify({"error": "Correct status must be a boolean (true/false)"}), 400

    # Validate session_id
    session_exists = cursor.execute("SELECT 1 FROM study_sessions WHERE id = ?", (session_id,)).fetchone()
    if not session_exists:
        return jsonify({"error": "Study session not found"}), 404

    # Validate word_id
    word_exists = cursor.execute("SELECT 1 FROM words WHERE id = ?", (word_id,)).fetchone()
    if not word_exists:
        return jsonify({"error": "Word not found"}), 404

    try:
        cursor.execute(
            "INSERT INTO word_review_items (word_id, study_session_id, correct) VALUES (?, ?, ?)",
            (word_id, session_id, 1 if correct else 0) # SQLite stores booleans as 0 or 1
        )
        db.commit()
        review_id = cursor.lastrowid
        return jsonify({"message": "Review attempt logged successfully", "review_id": review_id}), 201
    except sqlite3.Error as e:
        db.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

# --- Run the application ---
if __name__ == '__main__':
    # Initialize the database when the script is run
    init_db()
    # Terminate any existing ngrok tunnels to prevent conflicts
    ngrok.kill()

    # Retrieve the ngrok authtoken from environment variables
    ngrok_authtoken = os.environ.get("NGROK_AUTH_TOKEN")

    if not ngrok_authtoken:
        print("Error: NGROK_AUTH_TOKEN environment variable not set.")
        print("Please set it in a separate Colab cell using: os.environ['NGROK_AUTH_TOKEN'] = 'your_actual_token_value_here'")
        exit() # Exit if authtoken is not set, as tunneling won't work

    try:
        ngrok.set_auth_token(ngrok_authtoken)
    except Exception as e:
        print(f"Error setting ngrok authtoken: {e}")
        print("Please ensure your NGROK_AUTH_TOKEN is valid.")
        exit() # Exit if authtoken is invalid

    # Establish a new ngrok tunnel
    public_url = ngrok.connect(5000)
    print(f" * Tunnel URL: {public_url}")
    # Run the Flask app. Set debug=False to potentially reduce verbose debugger messages.
    app.run(debug=False, port=5000, use_reloader=False)
