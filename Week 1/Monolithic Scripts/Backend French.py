# -*- coding: utf-8 -*-
"""
Quebec French Language Learning Portal Backend API (Full Revised)

This Flask application provides the comprehensive backend API for a language learning portal,
meeting all detailed requirements. It manages vocabulary, study sessions, and review statistics
using an SQLite3 database.

Designed to be run in Google Colab, utilizing Colab Secrets for ngrok authentication.

Database Schema:
- words: Stores individual Quebec French vocabulary words.
    - id (Primary Key): Unique identifier for each word
    - french_word (String, Required): The word in Quebec French
    - quebec_pronunciation (String, Required): Pronunciation guide specific to Quebec French
    - english (String, Required): English translation of the word
    - parts (JSON, Required): Word components/details (e.g., gender, plural form, example sentence)
- words_groups: Join-table for many-to-many relationship between words and groups.
    - id (Primary Key): Unique identifier for each join record
    - word_id (Foreign Key): References words.id
    - group_id (Foreign Key): References groups.id
- groups: Manages collections of words.
    - id (Primary Key): Unique identifier for each group
    - name (String, Required): Name of the group
    - word_count (Integer, Default: 0): Counter cache for the number of words in the group
- study_activities: Defines different types of study activities available.
    - id (Primary Key): Unique identifier for each activity
    - name (String, Required): Name of the activity (e.g., "Flashcards", "Quiz")
    - thumbnail_url (String): URL for activity thumbnail
    - description (String): Description of the activity
    - launch_url (String, Required): The base URL to launch the study activity
- study_sessions: Records individual study sessions.
    - id (Primary Key): Unique identifier for each session
    - group_id (Foreign Key): References groups.id
    - study_activity_id (Foreign Key): References study_activities.id
    - created_at (Timestamp, Default: Current Time): When the session was created (start time)
    - end_time (Timestamp, Nullable): When the session ended (can be inferred from last review)
- word_review_items: Tracks individual word reviews within study sessions.
    - id (Primary Key): Unique identifier for each review
    - word_id (Foreign Key): References words.id
    - study_session_id (Foreign Key): References study_sessions.id
    - correct (Boolean, Required): Whether the answer was correct (0 for false, 1 for true)
    - created_at (Timestamp, Default: Current Time): When the review occurred
"""

import sqlite3
import json
import os
from flask import Flask, request, jsonify, g, url_for
from datetime import datetime, timedelta, timezone
from pyngrok import ngrok
from google.colab import userdata # For accessing Colab Secrets

# --- Configuration ---
DATABASE = 'lang_portal.db'
PER_PAGE = 100 # Default items per page for pagination as per new spec

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

def init_db(app_instance):
    """
    Initializes the database schema and populates with sample data.
    Takes Flask app instance to ensure application context for get_db().
    """
    with app_instance.app_context():
        db = get_db()
        cursor = db.cursor()

        # Drop tables if they exist for a clean full reset
        cursor.execute("DROP TABLE IF EXISTS word_review_items;")
        cursor.execute("DROP TABLE IF EXISTS study_sessions;")
        cursor.execute("DROP TABLE IF EXISTS study_activities;")
        cursor.execute("DROP TABLE IF EXISTS words_groups;")
        cursor.execute("DROP TABLE IF EXISTS groups;")
        cursor.execute("DROP TABLE IF EXISTS words;")
        db.commit()

        # Create tables with updated schema
        cursor.execute("""
            CREATE TABLE words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                french_word TEXT NOT NULL,
                quebec_pronunciation TEXT NOT NULL,
                english TEXT NOT NULL,
                parts TEXT NOT NULL -- Stored as JSON string
            );
        """)
        cursor.execute("""
            CREATE TABLE groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                word_count INTEGER DEFAULT 0
            );
        """)
        cursor.execute("""
            CREATE TABLE words_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE,
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
            );
        """)
        cursor.execute("""
            CREATE TABLE study_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                thumbnail_url TEXT,
                description TEXT,
                launch_url TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                study_activity_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP, -- Nullable, will be updated or inferred
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
                FOREIGN KEY (study_activity_id) REFERENCES study_activities(id) ON DELETE CASCADE
            );
        """)
        cursor.execute("""
            CREATE TABLE word_review_items (
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
        print("Populating sample data...")
        # Sample Quebec French words
        words_data = [
            ("Bonjour", "bon-zhoor", "Hello", {"gender": "N/A", "notes": "Common greeting"}),
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
            ("Dépanneur", "day-pan-ner", "Convenience store (Quebecois)", {"gender": "masculine", "notes": "Common term for a corner store in Quebec."}),
            ("Magasiner", "ma-ga-zee-nay", "To shop (Quebecois)", {"gender": "N/A", "notes": "Standard French uses 'faire du shopping'."}),
            ("Frette", "fret", "Cold (Quebecois slang)", {"gender": "N/A", "notes": "Informal way to say it's cold."}),
            ("Char", "shar", "Car (Quebecois slang)", {"gender": "masculine", "notes": "Informal term for a car."}),
            ("Tiguidou", "tee-gee-doo", "Alright/Okay (Quebecois slang)", {"gender": "N/A", "notes": "Used to express agreement or that something is fine."}),
        ]
        for fr_word, pron_guide, en_trans, parts_json in words_data:
            cursor.execute(
                "INSERT INTO words (french_word, quebec_pronunciation, english, parts) VALUES (?, ?, ?, ?)",
                (fr_word, pron_guide, en_trans, json.dumps(parts_json))
            )

        # Sample groups
        groups_data = [
            ("Basic Greetings",),
            ("Common Phrases",),
            ("Quebecois Slang",),
            ("Quebecois Culture",),
            ("Everyday Objects",)
        ]
        for name in groups_data:
            cursor.execute("INSERT INTO groups (name) VALUES (?)", name)

        # Sample study activities
        activities_data = [
            ("Flashcards", "/thumbnails/flashcards.png", "Practice words with interactive flashcards.", "/app/flashcards"),
            ("Quiz", "/thumbnails/quiz.png", "Test your knowledge with a multiple-choice quiz.", "/app/quiz"),
            ("Listening Practice", "/thumbnails/listen.png", "Improve your listening comprehension.", "/app/listen")
        ]
        for name, thumbnail, desc, launch in activities_data:
            cursor.execute("INSERT INTO study_activities (name, thumbnail_url, description, launch_url) VALUES (?, ?, ?, ?)",
                           (name, thumbnail, desc, launch))

        db.commit()

        # Link words to groups and update word_count
        words_map = {row['french_word']: row['id'] for row in cursor.execute("SELECT id, french_word FROM words").fetchall()}
        groups_map = {row['name']: row['id'] for row in cursor.execute("SELECT id, name FROM groups").fetchall()}
        # Define activities_map after activities have been inserted
        activities_map = {row['name']: row['id'] for row in cursor.execute("SELECT id, name FROM study_activities").fetchall()}


        word_group_links = [
            ("Bonjour", "Basic Greetings"), ("Bienvenue", "Basic Greetings"), ("Comment ça va?", "Basic Greetings"),
            ("Au revoir", "Basic Greetings"),
            ("Je suis", "Common Phrases"), ("Merci", "Common Phrases"), ("Oui", "Common Phrases"),
            ("Non", "Common Phrases"), ("S'il vous plaît", "Common Phrases"), ("De rien", "Common Phrases"),
            ("Tabarnak", "Quebecois Slang"), ("C'est plate", "Quebecois Slang"), ("Chum", "Quebecois Slang"),
            ("Dépanneur", "Quebecois Slang"), ("Frette", "Quebecois Slang"), ("Char", "Quebecois Slang"),
            ("Tiguidou", "Quebecois Slang"),
            ("Blé d'Inde", "Quebecois Culture"), ("Poutine", "Quebecois Culture"),
            ("Dépanneur", "Everyday Objects"), ("Char", "Everyday Objects")
        ]

        for word_name, group_name in word_group_links:
            word_id = words_map.get(word_name)
            group_id = groups_map.get(group_name)
            if word_id and group_id:
                try:
                    cursor.execute(
                        "INSERT INTO words_groups (word_id, group_id) VALUES (?, ?)",
                        (word_id, group_id)
                    )
                    cursor.execute(
                        "UPDATE groups SET word_count = word_count + 1 WHERE id = ?",
                        (group_id,)
                    )
                except sqlite3.IntegrityError:
                    pass # Already linked

        db.commit()

        # Simulate some study sessions and reviews
        # Session 1: Basic Greetings, Flashcards
        cursor.execute("INSERT INTO study_sessions (group_id, study_activity_id, created_at) VALUES (?, ?, ?)",
                       (groups_map['Basic Greetings'], activities_map['Flashcards'], "2024-05-20 10:00:00"))
        session1_id = cursor.lastrowid
        reviews1 = [
            (words_map['Bonjour'], session1_id, True, "2024-05-20 10:01:00"),
            (words_map['Bienvenue'], session1_id, True, "2024-05-20 10:02:00"),
            (words_map['Comment ça va?'], session1_id, False, "2024-05-20 10:03:00"),
            (words_map['Au revoir'], session1_id, True, "2024-05-20 10:04:00"),
        ]
        for word_id, sess_id, correct, created_at in reviews1:
            cursor.execute("INSERT INTO word_review_items (word_id, study_session_id, correct, created_at) VALUES (?, ?, ?, ?)",
                           (word_id, sess_id, 1 if correct else 0, created_at))
        cursor.execute("UPDATE study_sessions SET end_time = ? WHERE id = ?", ("2024-05-20 10:05:00", session1_id))
        db.commit()

        # Session 2: Common Phrases, Quiz (Next day)
        cursor.execute("INSERT INTO study_sessions (group_id, study_activity_id, created_at) VALUES (?, ?, ?)",
                       (groups_map['Common Phrases'], activities_map['Quiz'], "2024-05-21 11:00:00"))
        session2_id = cursor.lastrowid
        reviews2 = [
            (words_map['Merci'], session2_id, True, "2024-05-21 11:01:00"),
            (words_map['Oui'], session2_id, True, "2024-05-21 11:02:00"),
            (words_map['Non'], session2_id, False, "2024-05-21 11:03:00"),
            (words_map['S\'il vous plaît'], session2_id, True, "2024-05-21 11:04:00"),
            (words_map['De rien'], session2_id, True, "2024-05-21 11:05:00"),
        ]
        for word_id, sess_id, correct, created_at in reviews2:
            cursor.execute("INSERT INTO word_review_items (word_id, study_session_id, correct, created_at) VALUES (?, ?, ?, ?)",
                           (word_id, sess_id, 1 if correct else 0, created_at))
        cursor.execute("UPDATE study_sessions SET end_time = ? WHERE id = ?", ("2024-05-21 11:06:00", session2_id))
        db.commit()

        # Session 3: Quebecois Slang, Flashcards (Same day as session 2, later)
        cursor.execute("INSERT INTO study_sessions (group_id, study_activity_id, created_at) VALUES (?, ?, ?)",
                       (groups_map['Quebecois Slang'], activities_map['Flashcards'], "2024-05-21 15:00:00"))
        session3_id = cursor.lastrowid
        reviews3 = [
            (words_map['Tabarnak'], session3_id, True, "2024-05-21 15:01:00"),
            (words_map['C\'est plate'], session3_id, True, "2024-05-21 15:02:00"),
            (words_map['Chum'], session3_id, False, "2024-05-21 15:03:00"),
        ]
        for word_id, sess_id, correct, created_at in reviews3:
            cursor.execute("INSERT INTO word_review_items (word_id, study_session_id, correct, created_at) VALUES (?, ?, ?, ?)",
                           (word_id, sess_id, 1 if correct else 0, created_at))
        cursor.execute("UPDATE study_sessions SET end_time = ? WHERE id = ?", ("2024-05-21 15:04:00", session3_id))
        db.commit()

        # Session 4: Basic Greetings, Quiz (Next day)
        cursor.execute("INSERT INTO study_sessions (group_id, study_activity_id, created_at) VALUES (?, ?, ?)",
                       (groups_map['Basic Greetings'], activities_map['Quiz'], "2024-05-22 09:00:00"))
        session4_id = cursor.lastrowid
        reviews4 = [
            (words_map['Bonjour'], session4_id, True, "2024-05-22 09:01:00"),
            (words_map['Comment ça va?'], session4_id, True, "2024-05-22 09:02:00"),
        ]
        for word_id, sess_id, correct, created_at in reviews4:
            cursor.execute("INSERT INTO word_review_items (word_id, study_session_id, correct, created_at) VALUES (?, ?, ?, ?)",
                           (word_id, sess_id, 1 if correct else 0, created_at))
        cursor.execute("UPDATE study_sessions SET end_time = ? WHERE id = ?", ("2024-05-22 09:03:00", session4_id))
        db.commit()

        print("Sample data populated successfully.")


def _get_pagination_metadata(base_url, total_items, current_page, per_page):
    """Helper to generate pagination metadata."""
    total_pages = (total_items + per_page - 1) // per_page
    next_page = None
    prev_page = None

    if current_page < total_pages:
        next_page = f"{base_url}?page={current_page + 1}&limit={per_page}"
    if current_page > 1:
        prev_page = f"{base_url}?page={current_page - 1}&limit={per_page}"

    return {
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": current_page,
        "items_per_page": per_page,
        "next_page": next_page,
        "prev_page": prev_page
    }

def _format_datetime(dt_str):
    """Formats a datetime string to ISO 8601 with 'Z' for UTC."""
    if not dt_str:
        return None
    # Assuming SQLite stores timestamps in 'YYYY-MM-DD HH:MM:SS' format
    dt_obj = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    # Add timezone info (assuming UTC for simplicity, adjust if needed)
    return dt_obj.replace(tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z')


# --- API Routes ---

@app.route('/api')
def api_root():
    """Root endpoint for basic API information."""
    return jsonify({"message": "Welcome to the Quebec French Language Portal API!"})

# --- Dashboard Endpoints ---

@app.route('/api/dashboard/last_study_session', methods=['GET'])
def get_last_study_session():
    """
    GET /api/dashboard/last_study_session - Get details of the most recent study session.
    """
    db = get_db()
    cursor = db.cursor()

    query = """
        SELECT
            ss.id,
            g.name AS group_name,
            ss.created_at,
            ss.end_time,
            SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END) AS correct_count,
            SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END) AS incorrect_count,
            COUNT(wri.id) AS total_words_reviewed
        FROM
            study_sessions ss
        JOIN
            groups g ON ss.group_id = g.id
        LEFT JOIN
            word_review_items wri ON ss.id = wri.study_session_id
        GROUP BY
            ss.id, g.name, ss.created_at, ss.end_time
        ORDER BY
            ss.created_at DESC
        LIMIT 1;
    """
    last_session = cursor.execute(query).fetchone()

    if not last_session:
        return jsonify({"message": "No study sessions found."}), 404

    result = dict(last_session)
    result['correct_count'] = int(result['correct_count'] or 0)
    result['incorrect_count'] = int(result['incorrect_count'] or 0)
    result['total_words_reviewed'] = int(result['total_words_reviewed'] or 0)
    result['created_at'] = _format_datetime(result['created_at'])
    result['end_time'] = _format_datetime(result['end_time']) # Format end_time if present

    return jsonify(result)

@app.route('/api/dashboard/study_progress', methods=['GET'])
def get_study_progress():
    """
    GET /api/dashboard/study_progress - Get overall study progress statistics.
    """
    db = get_db()
    cursor = db.cursor()

    # Total unique words studied (reviewed at least once)
    total_words_studied_query = """
        SELECT COUNT(DISTINCT word_id) FROM word_review_items;
    """
    total_words_studied = cursor.execute(total_words_studied_query).fetchone()[0]

    # Total vocabulary in database
    total_vocabulary_in_db_query = """
        SELECT COUNT(*) FROM words;
    """
    total_vocabulary_in_db = cursor.execute(total_vocabulary_in_db_query).fetchone()[0]

    mastery_percentage = 0.0
    if total_vocabulary_in_db > 0:
        mastery_percentage = (total_words_studied / total_vocabulary_in_db) * 100

    return jsonify({
        "total_words_studied": total_words_studied,
        "total_vocabulary_in_db": total_vocabulary_in_db,
        "mastery_percentage": round(mastery_percentage, 2)
    })

@app.route('/api/dashboard/quick-stats', methods=['GET'])
def get_quick_stats():
    """
    GET /api/dashboard/quick-stats - Get quick overall study statistics.
    """
    db = get_db()
    cursor = db.cursor()

    # Success rate percentage
    total_correct_reviews_query = "SELECT COUNT(*) FROM word_review_items WHERE correct = 1;"
    total_correct_reviews = cursor.execute(total_correct_reviews_query).fetchone()[0]

    total_reviews_query = "SELECT COUNT(*) FROM word_review_items;"
    total_reviews = cursor.execute(total_reviews_query).fetchone()[0]

    success_rate_percentage = 0.0
    if total_reviews > 0:
        success_rate_percentage = (total_correct_reviews / total_reviews) * 100

    # Total study sessions
    total_study_sessions_query = "SELECT COUNT(*) FROM study_sessions;"
    total_study_sessions = cursor.execute(total_study_sessions_query).fetchone()[0]

    # Total active groups (groups that have had at least one study session)
    total_active_groups_query = "SELECT COUNT(DISTINCT group_id) FROM study_sessions;"
    total_active_groups = cursor.execute(total_active_groups_query).fetchone()[0]

    # Study streak days (consecutive days with at least one study session)
    # This is a more complex calculation, fetching all session dates and processing in Python
    study_streak_days = 0
    session_dates_query = "SELECT DISTINCT DATE(created_at) FROM study_sessions ORDER BY created_at DESC;"
    session_dates_raw = cursor.execute(session_dates_query).fetchall()
    session_dates = sorted([datetime.strptime(d[0], '%Y-%m-%d').date() for d in session_dates_raw], reverse=True)

    if session_dates:
        today = datetime.now(timezone.utc).date()
        # If the most recent session was yesterday or today, start counting streak
        if session_dates[0] == today or session_dates[0] == today - timedelta(days=1):
            current_day = today
            if session_dates[0] == today - timedelta(days=1): # If last session was yesterday, streak starts at 1
                current_day = today - timedelta(days=1)
            
            for date in session_dates:
                if date == current_day:
                    study_streak_days += 1
                    current_day -= timedelta(days=1)
                elif date < current_day: # Gap in streak
                    break
    
    return jsonify({
        "success_rate_percentage": round(success_rate_percentage, 2),
        "total_study_sessions": total_study_sessions,
        "total_active_groups": total_active_groups,
        "study_streak_days": study_streak_days
    })


# --- Study Activities Endpoints ---

@app.route('/api/study_activities', methods=['GET'])
def get_study_activities():
    """
    GET /api/study_activities - Get paginated list of study activities.
    """
    db = get_db()
    cursor = db.cursor()

    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE

    query = """
        SELECT id, name, thumbnail_url, description, launch_url
        FROM study_activities
        LIMIT ? OFFSET ?;
    """
    activities = cursor.execute(query, (PER_PAGE, offset)).fetchall()

    total_activities = cursor.execute("SELECT COUNT(*) FROM study_activities;").fetchone()[0]
    pagination = _get_pagination_metadata(url_for('get_study_activities', _external=True), total_activities, page, PER_PAGE)

    result = [dict(activity) for activity in activities]
    return jsonify({"study_activities": result, "pagination": pagination})

@app.route('/api/study_activities/<int:activity_id>', methods=['GET'])
def get_study_activity_by_id(activity_id):
    """
    GET /api/study_activities/:id - Get details of a specific study activity.
    """
    db = get_db()
    cursor = db.cursor()

    activity = cursor.execute(
        "SELECT id, name, thumbnail_url, description, launch_url FROM study_activities WHERE id = ?",
        (activity_id,)
    ).fetchone()

    if not activity:
        return jsonify({"error": "Study activity not found"}), 404

    return jsonify(dict(activity))

@app.route('/api/study_activities/<int:activity_id>/study_sessions', methods=['GET'])
def get_study_sessions_for_activity(activity_id):
    """
    GET /api/study_activities/:id/study_sessions - Get paginated list of study sessions for a specific activity.
    """
    db = get_db()
    cursor = db.cursor()

    activity = cursor.execute("SELECT id, name FROM study_activities WHERE id = ?", (activity_id,)).fetchone()
    if not activity:
        return jsonify({"error": "Study activity not found"}), 404

    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE

    query = """
        SELECT
            ss.id,
            g.name AS group_name,
            ss.created_at AS start_time,
            ss.end_time,
            COUNT(wri.id) AS number_of_review_items
        FROM
            study_sessions ss
        JOIN
            groups g ON ss.group_id = g.id
        LEFT JOIN
            word_review_items wri ON ss.id = wri.study_session_id
        WHERE
            ss.study_activity_id = ?
        GROUP BY
            ss.id, g.name, ss.created_at, ss.end_time
        ORDER BY
            ss.created_at DESC
        LIMIT ? OFFSET ?;
    """
    study_sessions = cursor.execute(query, (activity_id, PER_PAGE, offset)).fetchall()

    total_sessions_query = "SELECT COUNT(*) FROM study_sessions WHERE study_activity_id = ?;"
    total_sessions = cursor.execute(total_sessions_query, (activity_id,)).fetchone()[0]

    pagination = _get_pagination_metadata(url_for('get_study_sessions_for_activity', activity_id=activity_id, _external=True),
                                          total_sessions, page, PER_PAGE)

    result = []
    for session in study_sessions:
        session_dict = dict(session)
        session_dict['start_time'] = _format_datetime(session_dict['start_time'])
        session_dict['end_time'] = _format_datetime(session_dict['end_time'])
        session_dict['number_of_review_items'] = int(session_dict['number_of_review_items'] or 0)
        result.append(session_dict)

    return jsonify({
        "study_activity_id": activity_id,
        "study_activity_name": activity['name'],
        "study_sessions": result,
        "pagination": pagination
    })

@app.route('/api/study_activities', methods=['POST'])
def create_study_activity_session():
    """
    POST /api/study_activities - Create a new study session (acting as "launch" for an activity).
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

    group = cursor.execute("SELECT 1 FROM groups WHERE id = ?", (group_id,)).fetchone()
    if not group:
        return jsonify({"error": "Group not found"}), 404

    activity = cursor.execute("SELECT launch_url FROM study_activities WHERE id = ?", (study_activity_id,)).fetchone()
    if not activity:
        return jsonify({"error": "Study activity not found"}), 404

    try:
        cursor.execute(
            "INSERT INTO study_sessions (group_id, study_activity_id) VALUES (?, ?)",
            (group_id, study_activity_id)
        )
        db.commit()
        session_id = cursor.lastrowid
        launch_url = f"{activity['launch_url']}?session_id={session_id}"
        return jsonify({
            "message": "Study activity session launched successfully.",
            "study_session_id": session_id,
            "launch_url": launch_url
        }), 201
    except sqlite3.Error as e:
        db.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500


# --- Words Endpoints ---

@app.route('/api/words', methods=['GET'])
def get_words():
    """
    GET /api/words - Get paginated list of words with review statistics.
    Query Parameters:
        page (int): Page number (default: 1)
        sort_by (str): Sort field ('french_word', 'quebec_pronunciation', 'english', 'correct_count', 'wrong_count') (default: 'french_word')
        order (str): Sort order ('asc' or 'desc') (default: 'asc')
    """
    db = get_db()
    cursor = db.cursor()

    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'french_word')
    order = request.args.get('order', 'asc').upper()

    # Validate sort_by and order
    valid_sort_fields = ['french_word', 'quebec_pronunciation', 'english', 'correct_count', 'wrong_count']
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
            w.quebec_pronunciation,
            w.english,
            SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END) AS correct_count,
            SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END) AS wrong_count
        FROM
            words w
        LEFT JOIN
            word_review_items wri ON w.id = wri.word_id
        GROUP BY
            w.id, w.french_word, w.quebec_pronunciation, w.english
        ORDER BY
            {sort_by} {order}
        LIMIT ? OFFSET ?;
    """
    words = cursor.execute(query, (PER_PAGE, offset)).fetchall()

    # Get total count for pagination metadata
    total_words = cursor.execute("SELECT COUNT(*) FROM words;").fetchone()[0]
    pagination = _get_pagination_metadata(url_for('get_words', _external=True), total_words, page, PER_PAGE)

    result = []
    for word in words:
        word_dict = dict(word)
        word_dict['correct_count'] = int(word_dict['correct_count'] or 0)
        word_dict['wrong_count'] = int(word_dict['wrong_count'] or 0)
        result.append(word_dict)

    return jsonify({
        "words": result,
        "pagination": pagination
    })

@app.route('/api/words/<int:word_id>', methods=['GET'])
def get_word_by_id(word_id):
    """
    GET /api/words/:id - Get details of a specific word.
    """
    db = get_db()
    cursor = db.cursor()

    word_query = """
        SELECT
            w.id,
            w.french_word,
            w.quebec_pronunciation,
            w.english,
            w.parts,
            SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END) AS correct_count,
            SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END) AS wrong_count
        FROM
            words w
        LEFT JOIN
            word_review_items wri ON w.id = wri.word_id
        WHERE
            w.id = ?
        GROUP BY
            w.id, w.french_word, w.quebec_pronunciation, w.english, w.parts;
    """
    word = cursor.execute(word_query, (word_id,)).fetchone()

    if not word:
        return jsonify({"error": "Word not found"}), 404

    word_dict = dict(word)
    word_dict['parts'] = json.loads(word_dict['parts'])
    word_dict['study_statistics'] = {
        "correct_count": int(word_dict['correct_count'] or 0),
        "wrong_count": int(word_dict['wrong_count'] or 0)
    }
    del word_dict['correct_count'] # Remove raw counts
    del word_dict['wrong_count']

    # Get groups for this word
    groups_query = """
        SELECT g.id, g.name
        FROM groups g
        JOIN words_groups wg ON g.id = wg.group_id
        WHERE wg.word_id = ?;
    """
    word_groups = cursor.execute(groups_query, (word_id,)).fetchall()
    word_dict['word_groups'] = [dict(g) for g in word_groups]

    return jsonify(word_dict)


# --- Groups Endpoints ---

@app.route('/api/groups', methods=['GET'])
def get_groups():
    """
    GET /api/groups - Get paginated list of word groups with word counts.
    """
    db = get_db()
    cursor = db.cursor()

    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'name')
    order = request.args.get('order', 'asc').upper()

    # Validate sort_by and order
    valid_sort_fields = ['name', 'word_count']
    if sort_by not in valid_sort_fields:
        return jsonify({"error": f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"}), 400
    if order not in ['ASC', 'DESC']:
        return jsonify({"error": "Invalid order. Must be 'asc' or 'desc'"}), 400

    offset = (page - 1) * PER_PAGE

    query = f"""
        SELECT
            id,
            name,
            word_count
        FROM
            groups
        ORDER BY
            {sort_by} {order}
        LIMIT ? OFFSET ?;
    """
    groups = cursor.execute(query, (PER_PAGE, offset)).fetchall()

    total_groups = cursor.execute("SELECT COUNT(*) FROM groups;").fetchone()[0]
    pagination = _get_pagination_metadata(url_for('get_groups', _external=True), total_groups, page, PER_PAGE)

    result = [dict(group) for group in groups]

    return jsonify({
        "groups": result,
        "pagination": pagination
    })

@app.route('/api/groups/<int:group_id>', methods=['GET'])
def get_group_by_id(group_id):
    """
    GET /api/groups/:id - Get details of a specific group.
    """
    db = get_db()
    cursor = db.cursor()

    group = cursor.execute(
        "SELECT id, name, word_count AS total_word_count FROM groups WHERE id = ?",
        (group_id,)
    ).fetchone()

    if not group:
        return jsonify({"error": "Group not found"}), 404

    return jsonify(dict(group))

@app.route('/api/groups/<int:group_id>/words', methods=['GET'])
def get_words_from_group(group_id):
    """
    GET /api/groups/:id/words - Get paginated list of words from a specific group.
    """
    db = get_db()
    cursor = db.cursor()

    group = cursor.execute("SELECT id, name FROM groups WHERE id = ?", (group_id,)).fetchone()
    if not group:
        return jsonify({"error": "Group not found"}), 404

    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'french_word')
    order = request.args.get('order', 'asc').upper()

    valid_sort_fields = ['french_word', 'quebec_pronunciation', 'english', 'correct_count', 'wrong_count']
    if sort_by not in valid_sort_fields:
        return jsonify({"error": f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"}), 400
    if order not in ['ASC', 'DESC']:
        return jsonify({"error": "Invalid order. Must be 'asc' or 'desc'"}), 400

    offset = (page - 1) * PER_PAGE

    query = f"""
        SELECT
            w.id,
            w.french_word,
            w.quebec_pronunciation,
            w.english,
            SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END) AS correct_count,
            SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END) AS wrong_count
        FROM
            words w
        JOIN
            words_groups wg ON w.id = wg.word_id
        LEFT JOIN
            word_review_items wri ON w.id = wri.word_id
        WHERE
            wg.group_id = ?
        GROUP BY
            w.id, w.french_word, w.quebec_pronunciation, w.english
        ORDER BY
            {sort_by} {order}
        LIMIT ? OFFSET ?;
    """
    words = cursor.execute(query, (group_id, PER_PAGE, offset)).fetchall()

    total_words_in_group = cursor.execute("SELECT word_count FROM groups WHERE id = ?;", (group_id,)).fetchone()[0]
    pagination = _get_pagination_metadata(url_for('get_words_from_group', group_id=group_id, _external=True),
                                          total_words_in_group, page, PER_PAGE)

    result = []
    for word in words:
        word_dict = dict(word)
        word_dict['correct_count'] = int(word_dict['correct_count'] or 0)
        word_dict['wrong_count'] = int(word_dict['wrong_count'] or 0)
        result.append(word_dict)

    return jsonify({
        "group_id": group_id,
        "group_name": group['name'],
        "words": result,
        "pagination": pagination
    })

@app.route('/api/groups/<int:group_id>/study_sessions', methods=['GET'])
def get_study_sessions_for_group(group_id):
    """
    GET /api/groups/:id/study_sessions - Get paginated list of study sessions for a specific group.
    """
    db = get_db()
    cursor = db.cursor()

    group = cursor.execute("SELECT id, name FROM groups WHERE id = ?", (group_id,)).fetchone()
    if not group:
        return jsonify({"error": "Group not found"}), 404

    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE

    query = """
        SELECT
            ss.id,
            sa.name AS activity_name,
            g.name AS group_name,
            ss.created_at AS start_time,
            ss.end_time,
            COUNT(wri.id) AS number_of_review_items
        FROM
            study_sessions ss
        JOIN
            study_activities sa ON ss.study_activity_id = sa.id
        JOIN
            groups g ON ss.group_id = g.id
        LEFT JOIN
            word_review_items wri ON ss.id = wri.study_session_id
        WHERE
            ss.group_id = ?
        GROUP BY
            ss.id, sa.name, g.name, ss.created_at, ss.end_time
        ORDER BY
            ss.created_at DESC
        LIMIT ? OFFSET ?;
    """
    study_sessions = cursor.execute(query, (group_id, PER_PAGE, offset)).fetchall()

    total_sessions_query = "SELECT COUNT(*) FROM study_sessions WHERE group_id = ?;"
    total_sessions = cursor.execute(total_sessions_query, (group_id,)).fetchone()[0]

    pagination = _get_pagination_metadata(url_for('get_study_sessions_for_group', group_id=group_id, _external=True),
                                          total_sessions, page, PER_PAGE)

    result = []
    for session in study_sessions:
        session_dict = dict(session)
        session_dict['start_time'] = _format_datetime(session_dict['start_time'])
        session_dict['end_time'] = _format_datetime(session_dict['end_time'])
        session_dict['number_of_review_items'] = int(session_dict['number_of_review_items'] or 0)
        result.append(session_dict)

    return jsonify({
        "group_id": group_id,
        "group_name": group['name'],
        "study_sessions": result,
        "pagination": pagination
    })


# --- Study Sessions Endpoints ---

@app.route('/api/study_sessions', methods=['GET'])
def get_all_study_sessions():
    """
    GET /api/study_sessions - Get paginated list of all study sessions.
    """
    db = get_db()
    cursor = db.cursor()

    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE

    query = """
        SELECT
            ss.id,
            sa.name AS activity_name,
            g.name AS group_name,
            ss.created_at AS start_time,
            ss.end_time,
            COUNT(wri.id) AS number_of_review_items
        FROM
            study_sessions ss
        JOIN
            study_activities sa ON ss.study_activity_id = sa.id
        JOIN
            groups g ON ss.group_id = g.id
        LEFT JOIN
            word_review_items wri ON ss.id = wri.study_session_id
        GROUP BY
            ss.id, sa.name, g.name, ss.created_at, ss.end_time
        ORDER BY
            ss.created_at DESC
        LIMIT ? OFFSET ?;
    """
    study_sessions = cursor.execute(query, (PER_PAGE, offset)).fetchall()

    total_sessions = cursor.execute("SELECT COUNT(*) FROM study_sessions;").fetchone()[0]
    pagination = _get_pagination_metadata(url_for('get_all_study_sessions', _external=True), total_sessions, page, PER_PAGE)

    result = []
    for session in study_sessions:
        session_dict = dict(session)
        session_dict['start_time'] = _format_datetime(session_dict['start_time'])
        session_dict['end_time'] = _format_datetime(session_dict['end_time'])
        session_dict['number_of_review_items'] = int(session_dict['number_of_review_items'] or 0)
        result.append(session_dict)

    return jsonify({
        "study_sessions": result,
        "pagination": pagination
    })

@app.route('/api/study_sessions/<int:session_id>', methods=['GET'])
def get_study_session_by_id(session_id):
    """
    GET /api/study_sessions/:id - Get details of a specific study session.
    """
    db = get_db()
    cursor = db.cursor()

    query = """
        SELECT
            ss.id,
            sa.name AS activity_name,
            g.name AS group_name,
            ss.created_at AS start_time,
            ss.end_time,
            COUNT(wri.id) AS number_of_review_items
        FROM
            study_sessions ss
        JOIN
            study_activities sa ON ss.study_activity_id = sa.id
        JOIN
            groups g ON ss.group_id = g.id
        LEFT JOIN
            word_review_items wri ON ss.id = wri.study_session_id
        WHERE
            ss.id = ?
        GROUP BY
            ss.id, sa.name, g.name, ss.created_at, ss.end_time;
    """
    session = cursor.execute(query, (session_id,)).fetchone()

    if not session:
        return jsonify({"error": "Study session not found"}), 404

    session_dict = dict(session)
    session_dict['start_time'] = _format_datetime(session_dict['start_time'])
    session_dict['end_time'] = _format_datetime(session_dict['end_time'])
    session_dict['number_of_review_items'] = int(session_dict['number_of_review_items'] or 0)

    return jsonify(session_dict)

@app.route('/api/study_sessions/<int:session_id>/words', methods=['GET'])
def get_words_from_study_session(session_id):
    """
    GET /api/study_sessions/:id/words - Get list of word review items for a specific study session.
    """
    db = get_db()
    cursor = db.cursor()

    session_info = cursor.execute(
        "SELECT ss.id, g.name AS group_name FROM study_sessions ss JOIN groups g ON ss.group_id = g.id WHERE ss.id = ?",
        (session_id,)
    ).fetchone()

    if not session_info:
        return jsonify({"error": "Study session not found"}), 404

    query = """
        SELECT
            w.id AS word_id,
            w.french_word,
            w.quebec_pronunciation,
            w.english,
            wri.correct,
            wri.created_at
        FROM
            word_review_items wri
        JOIN
            words w ON wri.word_id = w.id
        WHERE
            wri.study_session_id = ?
        ORDER BY
            wri.created_at ASC;
    """
    review_items = cursor.execute(query, (session_id,)).fetchall()

    result = []
    for item in review_items:
        item_dict = dict(item)
        item_dict['correct'] = bool(item_dict['correct']) # Convert 0/1 to boolean
        item_dict['created_at'] = _format_datetime(item_dict['created_at'])
        result.append(item_dict)

    return jsonify({
        "study_session_id": session_id,
        "study_session_group_name": session_info['group_name'],
        "word_review_items": result
    })

@app.route('/api/study_sessions/<int:session_id>/words/<int:word_id>/review', methods=['POST'])
def log_word_review_attempt(session_id, word_id):
    """
    POST /api/study_sessions/:id/words/:word_id/review - Log a review attempt for a word during a study session.
    Path Parameters:
        session_id (int): ID of the study session.
        word_id (int): ID of the word reviewed.
    Request Body (JSON):
        correct (bool): Whether the answer was correct (required).
    """
    db = get_db()
    cursor = db.cursor()
    data = request.get_json()

    correct = data.get('correct')

    if correct is None:
        return jsonify({"error": "Correct status is required"}), 400

    if not isinstance(correct, bool):
        return jsonify({"error": "Correct status must be a boolean (true/false)"}), 400

    session_exists = cursor.execute("SELECT 1 FROM study_sessions WHERE id = ?", (session_id,)).fetchone()
    if not session_exists:
        return jsonify({"error": "Study session not found"}), 404

    word_exists = cursor.execute("SELECT 1 FROM words WHERE id = ?", (word_id,)).fetchone()
    if not word_exists:
        return jsonify({"error": "Word not found"}), 404

    try:
        current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "INSERT INTO word_review_items (word_id, study_session_id, correct, created_at) VALUES (?, ?, ?, ?)",
            (word_id, session_id, 1 if correct else 0, current_time)
        )
        db.commit()
        review_id = cursor.lastrowid

        # Update study_session's end_time to the latest review time
        cursor.execute("UPDATE study_sessions SET end_time = ? WHERE id = ?", (current_time, session_id))
        db.commit()

        return jsonify({
            "message": "Word review recorded successfully.",
            "review_item_id": review_id,
            "word_id": word_id,
            "study_session_id": session_id,
            "correct": correct,
            "created_at": _format_datetime(current_time)
        }), 201
    except sqlite3.Error as e:
        db.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500


# --- Reset Endpoints ---

@app.route('/api/reset_history', methods=['POST'])
def reset_history():
    """
    POST /api/reset_history - Deletes all study sessions and word review items.
    """
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM word_review_items;")
        cursor.execute("DELETE FROM study_sessions;")
        db.commit()
        return jsonify({"message": "Study history reset successfully."}), 200
    except sqlite3.Error as e:
        db.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@app.route('/api/full_reset', methods=['POST'])
def full_reset():
    """
    POST /api/full_reset - Drops all tables and reinitializes the database with seed data.
    """
    try:
        init_db(app) # Reinitialize with seed data
        return jsonify({"message": "Full system reset completed successfully. Database reinitialized with seed data."}), 200
    except Exception as e:
        return jsonify({"error": f"Full reset failed: {str(e)}"}), 500


# --- Run the application ---
if __name__ == '__main__':
    # Initialize the database (this will drop existing tables and re-seed)
    # Pass the app instance to init_db for context
    init_db(app)

    # Terminate any existing ngrok tunnels to prevent conflicts
    ngrok.kill()

    # Retrieve the ngrok authtoken from Colab Secrets
    ngrok_authtoken = None
    try:
        ngrok_authtoken = userdata.get("NGROK_AUTH_TOKEN")
        if ngrok_authtoken:
            print(f"NGROK_AUTH_TOKEN successfully retrieved from Colab Secrets.")
        else:
            print("NGROK_AUTH_TOKEN not found in Colab Secrets.")
            print("Please ensure you've added 'NGROK_AUTH_TOKEN' to Colab Secrets and enabled 'Notebook access'.")
            exit() # Exit if authtoken is not found
    except Exception as e:
        print(f"Error accessing Colab Secrets: {e}")
        print("Please ensure you've enabled 'Notebook access' for your NGROK_AUTH_TOKEN secret.")
        exit() # Exit if there's an issue accessing secrets

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
    # use_reloader=False is important for Colab to prevent issues with multiple processes
    app.run(debug=False, port=5000, use_reloader=False)
