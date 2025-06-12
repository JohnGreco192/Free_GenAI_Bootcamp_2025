# -*- coding: utf-8 -*-
"""
Quebec French Language Learning Portal Backend API (Monolithic & Clean Seed Version)

This Flask application consolidates all logic, database schema, and expanded French
seed data into a single Python script. It now strictly mimics the initial database
seeding approach of the Japanese backend.txt, meaning study history tables are
created but initially empty.

Designed for easy copy-pasting and execution in Google Colab, using Colab Secrets for ngrok authentication.
"""

import sqlite3
import json
import os
from flask import Flask, request, jsonify, g, url_for
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
from pyngrok import ngrok
from google.colab import userdata # For accessing Colab Secrets

# --- Configuration ---
DATABASE = 'lang_portal.db'
PER_PAGE = 100 # Default items per page for pagination as per new spec

# --- Embedded SQL Schema Definitions ---
SQL_CREATE_TABLE_WORDS = """
CREATE TABLE IF NOT EXISTS words (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  french_word TEXT NOT NULL,
  quebec_pronunciation TEXT NOT NULL,
  english TEXT NOT NULL,
  parts TEXT NOT NULL  -- Store parts as JSON string
);
"""

SQL_CREATE_TABLE_GROUPS = """
CREATE TABLE IF NOT EXISTS groups (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  word_count INTEGER DEFAULT 0  -- Counter cache for the number of words in the group
);
"""

SQL_CREATE_TABLE_WORDS_GROUPS = """
CREATE TABLE IF NOT EXISTS words_groups (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  word_id INTEGER NOT NULL,
  group_id INTEGER NOT NULL,
  FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE,
  FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
);
"""

SQL_CREATE_TABLE_STUDY_ACTIVITIES = """
CREATE TABLE IF NOT EXISTS study_activities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  thumbnail_url TEXT,
  description TEXT,
  launch_url TEXT NOT NULL
);
"""

SQL_CREATE_TABLE_STUDY_SESSIONS = """
CREATE TABLE IF NOT EXISTS study_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  group_id INTEGER NOT NULL,
  study_activity_id INTEGER NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  end_time DATETIME, -- Nullable, can be updated later
  FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
  FOREIGN KEY (study_activity_id) REFERENCES study_activities(id) ON DELETE CASCADE
);
"""

SQL_CREATE_TABLE_WORD_REVIEW_ITEMS = """
CREATE TABLE IF NOT EXISTS word_review_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  word_id INTEGER NOT NULL,
  study_session_id INTEGER NOT NULL,
  correct BOOLEAN NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE,
  FOREIGN KEY (study_session_id) REFERENCES study_sessions(id) ON DELETE CASCADE
);
"""

# --- Embedded JSON Seed Data (Expanded French Vocabulary) ---

FRENCH_WORDS_GREETINGS = [
  {"french_word": "Bonjour", "quebec_pronunciation": "bon-zhoor", "english": "Hello", "parts": {"notes": "Common greeting"}},
  {"french_word": "Bonsoir", "quebec_pronunciation": "bon-swar", "english": "Good evening", "parts": {"notes": "Evening greeting"}},
  {"french_word": "Bonne nuit", "quebec_pronunciation": "bon-nwee", "english": "Good night", "parts": {"notes": "Before sleeping"}},
  {"french_word": "Salut", "quebec_pronunciation": "sa-lyoo", "english": "Hi/Bye (informal)", "parts": {"notes": "Informal greeting/farewell"}},
  {"french_word": "Au revoir", "quebec_pronunciation": "oh ruh-vwahr", "english": "Goodbye", "parts": {"notes": "Common farewell"}}
]

FRENCH_WORDS_COMMON_PHRASES = [
  {"french_word": "Merci", "quebec_pronunciation": "mer-see", "english": "Thank you", "parts": {"notes": "Common expression of gratitude"}},
  {"french_word": "De rien", "quebec_pronunciation": "duh ree-ahn", "english": "You're welcome", "parts": {"notes": "Response to thank you"}},
  {"french_word": "S'il vous plaît", "quebec_pronunciation": "seel voo pleh", "english": "Please (formal)", "parts": {"notes": "Polite request"}},
  {"french_word": "S'il te plaît", "quebec_pronunciation": "seel tuh pleh", "english": "Please (informal)", "parts": {"notes": "Informal polite request"}},
  {"french_word": "Excusez-moi", "quebec_pronunciation": "ex-koo-zay-mwa", "english": "Excuse me (formal)", "parts": {"notes": "To apologize or get attention"}},
  {"french_word": "Pardon", "quebec_pronunciation": "par-don", "english": "Sorry/Pardon", "parts": {"notes": "General apology"}},
  {"french_word": "Oui", "quebec_pronunciation": "wee", "english": "Yes", "parts": {"notes": "Affirmative answer"}},
  {"french_word": "Non", "quebec_pronunciation": "noh", "english": "No", "parts": {"notes": "Negative answer"}},
  {"french_word": "Je suis", "quebec_pronunciation": "zhuh swee", "english": "I am", "parts": {"notes": "To introduce oneself"}},
  {"french_word": "Tu es", "quebec_pronunciation": "tyoo eh", "english": "You are (informal)", "parts": {"notes": "To address informally"}},
  {"french_word": "Comment ça va?", "quebec_pronunciation": "koh-mahn sah vah", "english": "How are you?", "parts": {"notes": "Informal greeting"}},
  {"french_word": "Ça va bien", "quebec_pronunciation": "sah vah byan", "english": "I'm fine", "parts": {"notes": "Response to 'how are you?'"}},
  {"french_word": "Parlez-vous anglais?", "quebec_pronunciation": "par-lay-voo-zahn-gleh", "english": "Do you speak English?", "parts": {"notes": "Asking about language"}}
]

FRENCH_WORDS_QUEBECOIS_SLANG = [
  {"french_word": "Tabarnak", "quebec_pronunciation": "ta-bar-nak", "english": "Damn it (Quebecois swear word)", "parts": {"notes": "Very common Quebecois expletive. Use with caution!"}},
  {"french_word": "C'est plate", "quebec_pronunciation": "say plat", "english": "It's boring/lame", "parts": {"notes": "Informal way to say something is dull or disappointing."}},
  {"french_word": "Chum", "quebec_pronunciation": "chum", "english": "Boyfriend/Buddy", "parts": {"notes": "Can mean a close friend or a romantic partner."}},
  {"french_word": "Blonde", "quebec_pronunciation": "blond", "english": "Girlfriend", "parts": {"notes": "Informal term for a female partner."}},
  {"french_word": "Dépanneur", "quebec_pronunciation": "day-pan-ner", "english": "Convenience store", "parts": {"gender": "masculine", "notes": "Common term for a corner store in Quebec."}},
  {"french_word": "Frette", "quebec_pronunciation": "fret", "english": "Cold", "parts": {"notes": "Informal way to say it's cold."}},
  {"french_word": "Char", "quebec_pronunciation": "shar", "english": "Car", "parts": {"gender": "masculine", "notes": "Informal term for a car."}},
  {"french_word": "Tiguidou", "quebec_pronunciation": "tee-gee-doo", "english": "Alright/Okay", "parts": {"notes": "Used to express agreement or that something is fine."}},
  {"french_word": "Piasse", "quebec_pronunciation": "pyass", "english": "Buck (dollar)", "parts": {"notes": "Slang for a dollar."}},
  {"french_word": "Bienvenue", "quebec_pronunciation": "byen-vuh-noo", "english": "You're welcome", "parts": {"notes": "Also used as a response to thank you."}}
]

FRENCH_WORDS_QUEBECOIS_CULTURE = [
  {"french_word": "Poutine", "quebec_pronunciation": "poo-teen", "english": "Poutine (dish)", "parts": {"notes": "Iconic Quebecois dish of fries, cheese curds, and gravy."}},
  {"french_word": "Cabane à sucre", "quebec_pronunciation": "ka-ban-a-syookr", "english": "Sugar shack", "parts": {"notes": "Place where maple syrup is produced and celebrated."}},
  {"french_word": "La p'tite bière", "quebec_pronunciation": "la-peet-byair", "english": "A little beer", "parts": {"notes": "Common informal term for a beer."}},
  {"french_word": "Blé d'Inde", "quebec_pronunciation": "blay daind", "english": "Corn", "parts": {"notes": "Quebecois specific term, standard French uses 'maïs'."}},
  {"french_word": "Tuque", "quebec_pronunciation": "tyook", "english": "Beanie/winter hat", "parts": {"gender": "feminine", "notes": "A common type of winter hat."}}
]

FRENCH_WORDS_EVERYDAY_OBJECTS = [
  {"french_word": "Table", "quebec_pronunciation": "tabl", "english": "Table", "parts": {"gender": "feminine"}},
  {"french_word": "Chaise", "quebec_pronunciation": "shez", "english": "Chair", "parts": {"gender": "feminine"}},
  {"french_word": "Livre", "quebec_pronunciation": "leevr", "english": "Book", "parts": {"gender": "masculine"}},
  {"french_word": "Stylo", "quebec_pronunciation": "stee-lo", "english": "Pen", "parts": {"gender": "masculine"}},
  {"french_word": "Sac", "quebec_pronunciation": "sak", "english": "Bag", "parts": {"gender": "masculine"}},
  {"french_word": "Clé", "quebec_pronunciation": "klay", "english": "Key", "parts": {"gender": "feminine"}},
  {"french_word": "Téléphone", "quebec_pronunciation": "tay-lay-fon", "english": "Telephone", "parts": {"gender": "masculine"}},
  {"french_word": "Ordinateur", "quebec_pronunciation": "or-dee-na-tur", "english": "Computer", "parts": {"gender": "masculine"}},
  {"french_word": "Verre", "quebec_pronunciation": "ver", "english": "Glass", "parts": {"gender": "masculine"}},
  {"french_word": "Assiette", "quebec_pronunciation": "a-syet", "english": "Plate", "parts": {"gender": "feminine"}},
  {"french_word": "Fourchette", "quebec_pronunciation": "foor-shet", "english": "Fork", "parts": {"gender": "feminine"}}
]

FRENCH_WORDS_EVERYDAY_ADJECTIVES = [
    {"french_word": "Grand", "quebec_pronunciation": "gran", "english": "Big/Tall", "parts": {"gender": "masculine"}},
    {"french_word": "Grande", "quebec_pronunciation": "grand", "english": "Big/Tall", "parts": {"gender": "feminine"}},
    {"french_word": "Petit", "quebec_pronunciation": "puh-tee", "english": "Small", "parts": {"gender": "masculine"}},
    {"french_word": "Petite", "quebec_pronunciation": "puh-teet", "english": "Small", "parts": {"gender": "feminine"}},
    {"french_word": "Beau", "quebec_pronunciation": "bo", "english": "Beautiful/Handsome", "parts": {"gender": "masculine"}},
    {"french_word": "Belle", "quebec_pronunciation": "bel", "english": "Beautiful", "parts": {"gender": "feminine"}},
    {"french_word": "Nouveau", "quebec_pronunciation": "noo-vo", "english": "New", "parts": {"gender": "masculine"}},
    {"french_word": "Nouvelle", "quebec_pronunciation": "noo-vel", "english": "New", "parts": {"gender": "feminine"}},
    {"french_word": "Vieux", "quebec_pronunciation": "vyoo", "english": "Old", "parts": {"gender": "masculine"}},
    {"french_word": "Vieille", "quebec_pronunciation": "vyay", "english": "Old", "parts": {"gender": "feminine"}},
    {"french_word": "Bon", "quebec_pronunciation": "bon", "english": "Good", "parts": {"gender": "masculine"}},
    {"french_word": "Bonne", "quebec_pronunciation": "bon", "english": "Good", "parts": {"gender": "feminine"}},
    {"french_word": "Mauvais", "quebec_pronunciation": "mo-veh", "english": "Bad", "parts": {"gender": "masculine"}},
    {"french_word": "Mauvaise", "quebec_pronunciation": "mo-vez", "english": "Bad", "parts": {"gender": "feminine"}},
    {"french_word": "Facile", "quebec_pronunciation": "fa-seel", "english": "Easy", "parts": {"gender": "N/A"}},
    {"french_word": "Difficile", "quebec_pronunciation": "dee-fee-seel", "english": "Difficult", "parts": {"gender": "N/A"}},
    {"french_word": "Rapide", "quebec_pronunciation": "ra-peed", "english": "Fast", "parts": {"gender": "N/A"}},
    {"french_word": "Lent", "quebec_pronunciation": "lan", "english": "Slow", "parts": {"gender": "masculine"}},
    {"french_word": "Lente", "quebec_pronunciation": "lant", "english": "Slow", "parts": {"gender": "feminine"}},
    {"french_word": "Propre", "quebec_pronunciation": "propr", "english": "Clean", "parts": {"gender": "N/A"}},
    {"french_word": "Sale", "quebec_pronunciation": "sal", "english": "Dirty", "parts": {"gender": "N/A"}},
    {"french_word": "Heureux", "quebec_pronunciation": "uh-ruh", "english": "Happy", "parts": {"gender": "masculine"}},
    {"french_word": "Heureuse", "quebec_pronunciation": "uh-ruz", "english": "Happy", "parts": {"gender": "feminine"}},
    {"french_word": "Triste", "quebec_pronunciation": "treest", "english": "Sad", "parts": {"gender": "N/A"}},
    {"french_word": "Fort", "quebec_pronunciation": "for", "english": "Strong", "parts": {"gender": "masculine"}},
    {"french_word": "Forte", "quebec_pronunciation": "fort", "english": "Strong", "parts": {"gender": "feminine"}},
    {"french_word": "Faible", "quebec_pronunciation": "febl", "english": "Weak", "parts": {"gender": "N/A"}},
    {"french_word": "Cher", "quebec_pronunciation": "shehr", "english": "Expensive", "parts": {"gender": "masculine"}},
    {"french_word": "Chère", "quebec_pronunciation": "shehr", "english": "Expensive", "parts": {"gender": "feminine"}},
    {"french_word": "Bon marché", "quebec_pronunciation": "bon mar-shay", "english": "Cheap", "parts": {"notes": "Always masculine, even for feminine nouns."}},
    {"french_word": "Intéressant", "quebec_pronunciation": "an-tay-ray-san", "english": "Interesting", "parts": {"gender": "masculine"}},
    {"french_word": "Intéressante", "quebec_pronunciation": "an-tay-ray-sant", "english": "Interesting", "parts": {"gender": "feminine"}}
]


STUDY_ACTIVITIES_DATA = [
  {
    "name": "Flashcards",
    "thumbnail_url": "/thumbnails/flashcards.png",
    "description": "Practice words with interactive flashcards.",
    "launch_url": "/app/flashcards"
  },
  {
    "name": "Quiz",
    "thumbnail_url": "/thumbnails/quiz.png",
    "description": "Test your knowledge with a multiple-choice quiz.",
    "launch_url": "/app/quiz"
  },
  {
    "name": "Listening Practice",
    "thumbnail_url": "/thumbnails/listen.png",
    "description": "Improve your listening comprehension.",
    "launch_url": "/app/listen"
  },
  {
    "name": "Pronunciation Practice",
    "thumbnail_url": "/thumbnails/pronounce.png",
    "description": "Practice Quebecois pronunciation drills.",
    "launch_url": "/app/pronounce"
  }
]

# --- Database Helper Class (Integrated) ---

class Db:
  def __init__(self, database_path):
    self.database = database_path
    self.connection = None # Connection will be managed by Flask's g

  def get(self):
    """Gets the database connection for the current request context."""
    if 'db' not in g:
      g.db = sqlite3.connect(self.database)
      g.db.row_factory = sqlite3.Row  # Return rows as dictionary-like objects
    return g.db

  def commit(self):
    """Commits any pending transactions to the database."""
    self.get().commit()

  def cursor(self):
    """Returns a database cursor."""
    return self.get().cursor()

  def close(self):
    """Closes the database connection for the current request context."""
    db = g.pop('db', None)
    if db is not None:
      db.close()

  def setup_tables(self, cursor):
    """Executes all table creation SQL scripts."""
    cursor.execute(SQL_CREATE_TABLE_WORDS)
    self.commit()
    cursor.execute(SQL_CREATE_TABLE_GROUPS)
    self.commit()
    cursor.execute(SQL_CREATE_TABLE_WORDS_GROUPS)
    self.commit()
    cursor.execute(SQL_CREATE_TABLE_STUDY_ACTIVITIES)
    self.commit()
    cursor.execute(SQL_CREATE_TABLE_STUDY_SESSIONS)
    self.commit()
    cursor.execute(SQL_CREATE_TABLE_WORD_REVIEW_ITEMS)
    self.commit()

  def import_words_data(self, cursor, group_name, words_list):
    """Imports words from a Python list and links them to a group."""
    cursor.execute('INSERT INTO groups (name) VALUES (?)', (group_name,))
    self.commit()
    
    cursor.execute('SELECT id FROM groups WHERE name = ?', (group_name,))
    group_id = cursor.fetchone()[0]

    for word in words_list:
      cursor.execute('''
        INSERT INTO words (french_word, quebec_pronunciation, english, parts)
        VALUES (?, ?, ?, ?)
      ''', (word['french_word'], word['quebec_pronunciation'], word['english'], json.dumps(word['parts'])))
      
      word_id = cursor.lastrowid

      cursor.execute('''
        INSERT INTO words_groups (word_id, group_id) VALUES (?, ?)
      ''', (word_id, group_id))
    self.commit()

    cursor.execute('''
      UPDATE groups
      SET word_count = (
        SELECT COUNT(*) FROM words_groups WHERE group_id = ?
      )
      WHERE id = ?
    ''', (group_id, group_id))
    self.commit()

    print(f"Successfully added {len(words_list)} words to the '{group_name}' group.")
    return group_id

  def import_study_activities_data(self, cursor, activities_list):
    """Imports study activities from a Python list."""
    for activity in activities_list:
      cursor.execute('''
      INSERT INTO study_activities (name, thumbnail_url, description, launch_url)
      VALUES (?, ?, ?, ?)
      ''', (activity['name'], activity['thumbnail_url'], activity['description'], activity['launch_url']))
    self.commit()
    print(f"Successfully added {len(activities_list)} study activities.")
    
  def init_db_and_seed_data(self, app_instance):
    """
    Initializes the database by setting up tables and populating sample data.
    This method is called from the main app.py.
    """
    # FIX: Removed `with app_instance.app_context():` as the call is already in an app context.
    # This caused a nested context issue, preventing tables from being recognized.
    cursor = self.cursor()

    # Drop all tables for a clean re-initialization
    cursor.execute("DROP TABLE IF EXISTS word_review_items;")
    cursor.execute("DROP TABLE IF EXISTS study_sessions;")
    cursor.execute("DROP TABLE IF EXISTS study_activities;")
    cursor.execute("DROP TABLE IF EXISTS words_groups;")
    cursor.execute("DROP TABLE IF EXISTS groups;")
    cursor.execute("DROP TABLE IF EXISTS words;")
    self.commit()

    self.setup_tables(cursor)

    # Import words and groups from embedded data
    groups_map = {}
    groups_map['Basic Greetings'] = self.import_words_data(
        cursor=cursor,
        group_name='Basic Greetings',
        words_list=FRENCH_WORDS_GREETINGS
    )
    groups_map['Common Phrases'] = self.import_words_data(
        cursor=cursor,
        group_name='Common Phrases',
        words_list=FRENCH_WORDS_COMMON_PHRASES
    )
    groups_map['Quebecois Slang'] = self.import_words_data(
        cursor=cursor,
        group_name='Quebecois Slang',
        words_list=FRENCH_WORDS_QUEBECOIS_SLANG
    )
    groups_map['Quebecois Culture'] = self.import_words_data(
        cursor=cursor,
        group_name='Quebecois Culture',
        words_list=FRENCH_WORDS_QUEBECOIS_CULTURE
    )
    groups_map['Everyday Objects'] = self.import_words_data(
        cursor=cursor,
        group_name='Everyday Objects',
        words_list=FRENCH_WORDS_EVERYDAY_OBJECTS
    )
    groups_map['Everyday Adjectives'] = self.import_words_data(
        cursor=cursor,
        group_name='Everyday Adjectives',
        words_list=FRENCH_WORDS_EVERYDAY_ADJECTIVES
    )

    self.import_study_activities_data(
        cursor=cursor,
        activities_list=STUDY_ACTIVITIES_DATA
    )
    
    # Note: Study sessions and review items are NOT seeded here to mimic the
    # initial state of the Japanese backend. These tables will be empty
    # until new sessions are created via API calls.

    print("Core vocabulary and study activities populated. Study history tables are initialized but empty.")

# Instantiate the Db class
db = Db(DATABASE)

# --- Helper Functions for API Endpoints ---

def _format_datetime(dt_str):
    """Formats a datetime string to ISO 8601 with 'Z' for UTC."""
    if not dt_str:
        return None
    # FIX: Added handling for microseconds if present (from test script)
    try:
        dt_obj = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        dt_obj = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    return dt_obj.replace(tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z')


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

# --- Flask Application Factory ---

def create_app(test_config=None):
    app = Flask(__name__)

    # Apply configuration
    if test_config is None:
        app.config.from_mapping(
            DATABASE=DATABASE,
            PER_PAGE=PER_PAGE
        )
    else:
        app.config.update(test_config)

    # Database connection management
    @app.teardown_appcontext
    def close_connection(exception):
        db.close()

    # Configure CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # --- API Routes ---

    @app.route('/api')
    def api_root():
        return jsonify({"message": "Welcome to the Quebec French Language Portal API!"})

    # Dashboard Endpoints
    @app.route('/api/dashboard/last_study_session', methods=['GET'])
    def get_last_study_session():
        cursor = db.cursor()
        query = """
            SELECT ss.id, g.name AS group_name, ss.created_at, ss.end_time,
                   SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END) AS correct_count,
                   SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END) AS incorrect_count,
                   COUNT(wri.id) AS total_words_reviewed
            FROM study_sessions ss
            JOIN groups g ON ss.group_id = g.id
            LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
            GROUP BY ss.id, g.name, ss.created_at, ss.end_time
            ORDER BY ss.created_at DESC LIMIT 1;
        """
        last_session = cursor.execute(query).fetchone()
        if not last_session: return jsonify({"message": "No study sessions found."}), 404
        result = dict(last_session)
        result['correct_count'] = int(result['correct_count'] or 0)
        result['incorrect_count'] = int(result['incorrect_count'] or 0)
        result['total_words_reviewed'] = int(result['total_words_reviewed'] or 0)
        result['created_at'] = _format_datetime(result['created_at'])
        result['end_time'] = _format_datetime(result['end_time'])
        return jsonify(result)

    @app.route('/api/dashboard/study_progress', methods=['GET'])
    def get_study_progress():
        cursor = db.cursor()
        total_words_studied = cursor.execute("SELECT COUNT(DISTINCT word_id) FROM word_review_items;").fetchone()[0]
        total_vocabulary_in_db = cursor.execute("SELECT COUNT(*) FROM words;").fetchone()[0]
        mastery_percentage = (total_words_studied / total_vocabulary_in_db) * 100 if total_vocabulary_in_db > 0 else 0.0
        return jsonify({
            "total_words_studied": total_words_studied,
            "total_vocabulary_in_db": total_vocabulary_in_db,
            "mastery_percentage": round(mastery_percentage, 2)
        })

    @app.route('/api/dashboard/quick-stats', methods=['GET'])
    def get_quick_stats():
        cursor = db.cursor()
        total_correct_reviews = cursor.execute("SELECT COUNT(*) FROM word_review_items WHERE correct = 1;").fetchone()[0]
        total_reviews = cursor.execute("SELECT COUNT(*) FROM word_review_items;").fetchone()[0]
        success_rate_percentage = (total_correct_reviews / total_reviews) * 100 if total_reviews > 0 else 0.0
        total_study_sessions = cursor.execute("SELECT COUNT(*) FROM study_sessions;").fetchone()[0]
        total_active_groups = cursor.execute("SELECT COUNT(DISTINCT group_id) FROM study_sessions;").fetchone()[0]

        study_streak_days = 0
        session_dates_raw = cursor.execute("SELECT DISTINCT DATE(created_at) FROM study_sessions ORDER BY created_at DESC;").fetchall()
        session_dates = sorted([datetime.strptime(d[0], '%Y-%m-%d').date() for d in session_dates_raw], reverse=True)
        if session_dates:
            today = datetime.now(timezone.utc).date()
            current_day_for_streak = today
            if session_dates and session_dates[0] == today - timedelta(days=1):
                current_day_for_streak = today - timedelta(days=1)
            for date in session_dates:
                if date == current_day_for_streak:
                    study_streak_days += 1
                    current_day_for_streak -= timedelta(days=1)
                elif date < current_day_for_streak: break
        return jsonify({
            "success_rate_percentage": round(success_rate_percentage, 2),
            "total_study_sessions": total_study_sessions,
            "total_active_groups": total_active_groups,
            "study_streak_days": study_streak_days
        })

    # Study Activities Endpoints
    @app.route('/api/study_activities', methods=['GET'])
    def get_study_activities():
        cursor = db.cursor()
        page = request.args.get('page', 1, type=int)
        offset = (page - 1) * app.config['PER_PAGE']
        query = "SELECT id, name, thumbnail_url, description, launch_url FROM study_activities LIMIT ? OFFSET ?;"
        activities = cursor.execute(query, (app.config['PER_PAGE'], offset)).fetchall()
        total_activities = cursor.execute("SELECT COUNT(*) FROM study_activities;").fetchone()[0]
        pagination = _get_pagination_metadata(url_for('get_study_activities', _external=True), total_activities, page, app.config['PER_PAGE'])
        result = [dict(activity) for activity in activities]
        return jsonify({"study_activities": result, "pagination": pagination})

    @app.route('/api/study_activities/<int:activity_id>', methods=['GET'])
    def get_study_activity_by_id(activity_id):
        cursor = db.cursor()
        activity = cursor.execute("SELECT id, name, thumbnail_url, description, launch_url FROM study_activities WHERE id = ?", (activity_id,)).fetchone()
        if not activity: return jsonify({"error": "Study activity not found"}), 404
        return jsonify(dict(activity))

    @app.route('/api/study_activities/<int:activity_id>/study_sessions', methods=['GET'])
    def get_study_sessions_for_activity(activity_id):
        cursor = db.cursor()
        activity = cursor.execute("SELECT id, name FROM study_activities WHERE id = ?", (activity_id,)).fetchone()
        if not activity: return jsonify({"error": "Study activity not found"}), 404
        page = request.args.get('page', 1, type=int)
        offset = (page - 1) * app.config['PER_PAGE']
        query = """
            SELECT ss.id, g.name AS group_name, ss.created_at AS start_time, ss.end_time,
                   COUNT(wri.id) AS number_of_review_items
            FROM study_sessions ss JOIN groups g ON ss.group_id = g.id
            LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
            WHERE ss.study_activity_id = ? GROUP BY ss.id, g.name, ss.created_at, ss.end_time
            ORDER BY ss.created_at DESC LIMIT ? OFFSET ?;
        """
        study_sessions = cursor.execute(query, (activity_id, app.config['PER_PAGE'], offset)).fetchall()
        total_sessions_query = "SELECT COUNT(*) FROM study_sessions WHERE study_activity_id = ?;"
        total_sessions = cursor.execute(total_sessions_query, (activity_id,)).fetchone()[0]
        pagination = _get_pagination_metadata(url_for('get_study_sessions_for_activity', activity_id=activity_id, _external=True),
                                          total_sessions, page, app.config['PER_PAGE'])
        result = []
        for session in study_sessions:
            session_dict = dict(session)
            session_dict['start_time'] = _format_datetime(session_dict['start_time'])
            session_dict['end_time'] = _format_datetime(session_dict['end_time'])
            session_dict['number_of_review_items'] = int(session_dict['number_of_review_items'] or 0)
            result.append(session_dict)
        return jsonify({
            "study_activity_id": activity_id, "study_activity_name": activity['name'],
            "study_sessions": result, "pagination": pagination
        })

    @app.route('/api/study_activities', methods=['POST'])
    def create_study_activity_session():
        cursor = db.cursor()
        data = request.get_json()
        group_id = data.get('group_id')
        study_activity_id = data.get('study_activity_id')
        if not group_id or not study_activity_id:
            return jsonify({"error": "group_id and study_activity_id are required"}), 400
        group = cursor.execute("SELECT 1 FROM groups WHERE id = ?", (group_id,)).fetchone()
        if not group: return jsonify({"error": "Group not found"}), 404
        activity = cursor.execute("SELECT launch_url FROM study_activities WHERE id = ?", (study_activity_id,)).fetchone()
        if not activity: return jsonify({"error": "Study activity not found"}), 404
        try:
            cursor.execute("INSERT INTO study_sessions (group_id, study_activity_id) VALUES (?, ?)", (group_id, study_activity_id))
            db.commit()
            session_id = cursor.lastrowid
            launch_url = f"{activity['launch_url']}?session_id={session_id}"
            return jsonify({
                "message": "Study activity session launched successfully.",
                "study_session_id": session_id,
                "launch_url": launch_url
            }), 201
        except sqlite3.Error as e:
            db.get().rollback() # FIX: Changed from db.rollback() to db.get().rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500

    # Words Endpoints
    @app.route('/api/words', methods=['GET'])
    def get_words():
        cursor = db.cursor()
        page = request.args.get('page', 1, type=int)
        sort_by = request.args.get('sort_by', 'french_word')
        order = request.args.get('order', 'asc').upper()
        valid_sort_fields = ['french_word', 'quebec_pronunciation', 'english', 'correct_count', 'wrong_count']
        if sort_by not in valid_sort_fields: return jsonify({"error": f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"}), 400
        if order not in ['ASC', 'DESC']: return jsonify({"error": "Invalid order. Must be 'asc' or 'desc'"}), 400
        offset = (page - 1) * app.config['PER_PAGE']
        query = f"""
            SELECT w.id, w.french_word, w.quebec_pronunciation, w.english,
                   SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END) AS correct_count,
                   SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END) AS wrong_count
            FROM words w LEFT JOIN word_review_items wri ON w.id = wri.word_id
            GROUP BY w.id, w.french_word, w.quebec_pronunciation, w.english
            ORDER BY {sort_by} {order} LIMIT ? OFFSET ?;
        """
        words = cursor.execute(query, (app.config['PER_PAGE'], offset)).fetchall()
        total_words = cursor.execute("SELECT COUNT(*) FROM words;").fetchone()[0]
        pagination = _get_pagination_metadata(url_for('get_words', _external=True), total_words, page, app.config['PER_PAGE'])
        result = []
        for word in words:
            word_dict = dict(word)
            word_dict['correct_count'] = int(word_dict['correct_count'] or 0)
            word_dict['wrong_count'] = int(word_dict['wrong_count'] or 0)
            result.append(word_dict)
        return jsonify({"words": result, "pagination": pagination})

    @app.route('/api/words/<int:word_id>', methods=['GET'])
    def get_word_by_id(word_id):
        cursor = db.cursor()
        word_query = """
            SELECT w.id, w.french_word, w.quebec_pronunciation, w.english, w.parts,
                   SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END) AS correct_count,
                   SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END) AS wrong_count
            FROM words w LEFT JOIN word_review_items wri ON w.id = wri.word_id
            WHERE w.id = ? GROUP BY w.id, w.french_word, w.quebec_pronunciation, w.english, w.parts;
        """
        word = cursor.execute(word_query, (word_id,)).fetchone()
        if not word: return jsonify({"error": "Word not found"}), 404
        word_dict = dict(word)
        word_dict['parts'] = json.loads(word_dict['parts'])
        word_dict['study_statistics'] = {
            "correct_count": int(word_dict['correct_count'] or 0),
            "wrong_count": int(word_dict['wrong_count'] or 0)
        }
        del word_dict['correct_count']
        del word_dict['wrong_count']
        groups_query = """
            SELECT g.id, g.name FROM groups g JOIN words_groups wg ON g.id = wg.group_id WHERE wg.word_id = ?;
        """
        word_groups = cursor.execute(groups_query, (word_id,)).fetchall()
        word_dict['word_groups'] = [dict(g) for g in word_groups]
        return jsonify(word_dict)

    # Groups Endpoints
    @app.route('/api/groups', methods=['GET'])
    def get_groups():
        cursor = db.cursor()
        page = request.args.get('page', 1, type=int)
        sort_by = request.args.get('sort_by', 'name')
        order = request.args.get('order', 'asc').upper()
        valid_sort_fields = ['name', 'word_count']
        if sort_by not in valid_sort_fields: return jsonify({"error": f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"}), 400
        if order not in ['ASC', 'DESC']: return jsonify({"error": "Invalid order. Must be 'asc' or 'desc'"}), 400
        offset = (page - 1) * app.config['PER_PAGE']
        query = f"""
            SELECT id, name, word_count FROM groups ORDER BY {sort_by} {order} LIMIT ? OFFSET ?;
        """
        groups = cursor.execute(query, (app.config['PER_PAGE'], offset)).fetchall()
        total_groups = cursor.execute("SELECT COUNT(*) FROM groups;").fetchone()[0]
        pagination = _get_pagination_metadata(url_for('get_groups', _external=True), total_groups, page, app.config['PER_PAGE'])
        result = [dict(group) for group in groups]
        return jsonify({"groups": result, "pagination": pagination})

    @app.route('/api/groups/<int:group_id>', methods=['GET'])
    def get_group_by_id(group_id):
        cursor = db.cursor()
        group = cursor.execute("SELECT id, name, word_count AS total_word_count FROM groups WHERE id = ?", (group_id,)).fetchone()
        if not group: return jsonify({"error": "Group not found"}), 404
        return jsonify(dict(group))

    @app.route('/api/groups/<int:group_id>/words', methods=['GET'])
    def get_words_from_group(group_id):
        cursor = db.cursor()
        group = cursor.execute("SELECT id, name FROM groups WHERE id = ?", (group_id,)).fetchone()
        if not group: return jsonify({"error": "Group not found"}), 404
        page = request.args.get('page', 1, type=int)
        sort_by = request.args.get('sort_by', 'french_word')
        order = request.args.get('order', 'asc').upper()
        valid_sort_fields = ['french_word', 'quebec_pronunciation', 'english', 'correct_count', 'wrong_count']
        if sort_by not in valid_sort_fields: return jsonify({"error": f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"}), 400
        if order not in ['ASC', 'DESC']: return jsonify({"error": "Invalid order. Must be 'asc' or 'desc'"}), 400
        offset = (page - 1) * app.config['PER_PAGE']
        query = f"""
            SELECT w.id, w.french_word, w.quebec_pronunciation, w.english,
                   SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END) AS correct_count,
                   SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END) AS wrong_count
            FROM words w JOIN words_groups wg ON w.id = wg.word_id
            LEFT JOIN word_review_items wri ON w.id = wri.word_id
            WHERE wg.group_id = ? GROUP BY w.id, w.french_word, w.quebec_pronunciation, w.english
            ORDER BY {sort_by} {order} LIMIT ? OFFSET ?;
        """
        words = cursor.execute(query, (group_id, app.config['PER_PAGE'], offset)).fetchall()
        total_words_in_group = cursor.execute("SELECT word_count FROM groups WHERE id = ?;", (group_id,)).fetchone()[0]
        pagination = _get_pagination_metadata(url_for('get_words_from_group', group_id=group_id, _external=True),
                                          total_words_in_group, page, app.config['PER_PAGE'])
        result = []
        for word in words:
            word_dict = dict(word)
            word_dict['correct_count'] = int(word_dict['correct_count'] or 0)
            word_dict['wrong_count'] = int(word_dict['wrong_count'] or 0)
            result.append(word_dict)
        return jsonify({
            "group_id": group_id, "group_name": group['name'],
            "words": result, "pagination": pagination
        })

    @app.route('/api/groups/<int:group_id>/study_sessions', methods=['GET'])
    def get_study_sessions_for_group(group_id):
        cursor = db.cursor()
        group = cursor.execute("SELECT id, name FROM groups WHERE id = ?", (group_id,)).fetchone()
        if not group: return jsonify({"error": "Group not found"}), 404
        page = request.args.get('page', 1, type=int)
        offset = (page - 1) * app.config['PER_PAGE']
        query = """
            SELECT ss.id, sa.name AS activity_name, g.name AS group_name,
                   ss.created_at AS start_time, ss.end_time,
                   COUNT(wri.id) AS number_of_review_items
            FROM study_sessions ss JOIN study_activities sa ON ss.study_activity_id = sa.id
            JOIN groups g ON ss.group_id = g.id LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
            WHERE ss.group_id = ? GROUP BY ss.id, sa.name, g.name, ss.created_at, ss.end_time
            ORDER BY ss.created_at DESC LIMIT ? OFFSET ?;
        """
        study_sessions = cursor.execute(query, (group_id, app.config['PER_PAGE'], offset)).fetchall()
        total_sessions_query = "SELECT COUNT(*) FROM study_sessions WHERE group_id = ?;"
        total_sessions = cursor.execute(total_sessions_query, (group_id,)).fetchone()[0]
        pagination = _get_pagination_metadata(url_for('get_study_sessions_for_group', group_id=group_id, _external=True),
                                          total_sessions, page, app.config['PER_PAGE'])
        result = []
        for session in study_sessions:
            session_dict = dict(session)
            session_dict['start_time'] = _format_datetime(session_dict['start_time'])
            session_dict['end_time'] = _format_datetime(session_dict['end_time'])
            session_dict['number_of_review_items'] = int(session_dict['number_of_review_items'] or 0)
            result.append(session_dict)
        return jsonify({
            "group_id": group_id, "group_name": group['name'],
            "study_sessions": result, "pagination": pagination
        })

    # Study Sessions Endpoints
    @app.route('/api/study_sessions', methods=['GET'])
    def get_all_study_sessions():
        cursor = db.cursor()
        page = request.args.get('page', 1, type=int)
        offset = (page - 1) * app.config['PER_PAGE']
        query = """
            SELECT ss.id, sa.name AS activity_name, g.name AS group_name,
                   ss.created_at AS start_time, ss.end_time,
                   COUNT(wri.id) AS number_of_review_items
            FROM study_sessions ss JOIN study_activities sa ON ss.study_activity_id = sa.id
            JOIN groups g ON ss.group_id = g.id LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
            GROUP BY ss.id, sa.name, g.name, ss.created_at, ss.end_time
            ORDER BY ss.created_at DESC LIMIT ? OFFSET ?;
        """
        study_sessions = cursor.execute(query, (app.config['PER_PAGE'], offset)).fetchall()
        total_sessions = cursor.execute("SELECT COUNT(*) FROM study_sessions;").fetchone()[0]
        pagination = _get_pagination_metadata(url_for('get_all_study_sessions', _external=True), total_sessions, page, app.config['PER_PAGE'])
        result = []
        for session in study_sessions:
            session_dict = dict(session)
            session_dict['start_time'] = _format_datetime(session_dict['start_time'])
            session_dict['end_time'] = _format_datetime(session_dict['end_time'])
            session_dict['number_of_review_items'] = int(session_dict['number_of_review_items'] or 0)
            result.append(session_dict)
        return jsonify({
            "study_sessions": result, "pagination": pagination
        })

    @app.route('/api/study_sessions/<int:session_id>', methods=['GET'])
    def get_study_session_by_id(session_id):
        cursor = db.cursor()
        query = """
            SELECT ss.id, sa.name AS activity_name, g.name AS group_name,
                   ss.created_at AS start_time, ss.end_time,
                   COUNT(wri.id) AS number_of_review_items
            FROM study_sessions ss JOIN study_activities sa ON ss.study_activity_id = sa.id
            JOIN groups g ON ss.group_id = g.id LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
            WHERE ss.id = ? GROUP BY ss.id, sa.name, g.name, ss.created_at, ss.end_time;
        """
        session = cursor.execute(query, (session_id,)).fetchone()
        if not session: return jsonify({"error": "Study session not found"}), 404
        session_dict = dict(session)
        session_dict['start_time'] = _format_datetime(session_dict['start_time'])
        session_dict['end_time'] = _format_datetime(session_dict['end_time'])
        session_dict['number_of_review_items'] = int(session_dict['number_of_review_items'] or 0)
        return jsonify(session_dict)

    @app.route('/api/study_sessions/<int:session_id>/words', methods=['GET'])
    def get_words_from_study_session(session_id):
        cursor = db.cursor()
        session_info = cursor.execute(
            "SELECT ss.id, g.name AS group_name FROM study_sessions ss JOIN groups g ON ss.group_id = g.id WHERE ss.id = ?",
            (session_id,)
        ).fetchone()
        if not session_info: return jsonify({"error": "Study session not found"}), 404
        query = """
            SELECT w.id AS word_id, w.french_word, w.quebec_pronunciation, w.english,
                   wri.correct, wri.created_at
            FROM word_review_items wri JOIN words w ON wri.word_id = w.id
            WHERE wri.study_session_id = ? ORDER BY wri.created_at ASC;
        """
        review_items = cursor.execute(query, (session_id,)).fetchall()
        result = []
        for item in review_items:
            item_dict = dict(item)
            item_dict['correct'] = bool(item_dict['correct'])
            item_dict['created_at'] = _format_datetime(item_dict['created_at'])
            result.append(item_dict)
        return jsonify({
            "study_session_id": session_id, "study_session_group_name": session_info['group_name'],
            "word_review_items": result
        })

    @app.route('/api/study_sessions/<int:session_id>/words/<int:word_id>/review', methods=['POST'])
    def log_word_review_attempt(session_id, word_id):
        cursor = db.cursor()
        data = request.get_json()
        correct = data.get('correct')
        if correct is None: return jsonify({"error": "Correct status is required"}), 400
        if not isinstance(correct, bool): return jsonify({"error": "Correct status must be a boolean (true/false)"}), 400
        session_exists = cursor.execute("SELECT 1 FROM study_sessions WHERE id = ?", (session_id,)).fetchone()
        if not session_exists: return jsonify({"error": "Study session not found"}), 404
        word_exists = cursor.execute("SELECT 1 FROM words WHERE id = ?", (word_id,)).fetchone()
        if not word_exists: return jsonify({"error": "Word not found"}), 404
        try:
            current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f') # Updated to include microseconds for consistency
            cursor.execute("INSERT INTO word_review_items (word_id, study_session_id, correct, created_at) VALUES (?, ?, ?, ?)",
                           (word_id, session_id, 1 if correct else 0, current_time))
            db.commit()
            review_id = cursor.lastrowid
            cursor.execute("UPDATE study_sessions SET end_time = ? WHERE id = ?", (current_time, session_id))
            db.commit()
            return jsonify({
                "message": "Word review recorded successfully.", "review_item_id": review_id,
                "word_id": word_id, "study_session_id": session_id, "correct": correct,
                "created_at": _format_datetime(current_time)
            }), 201
        except sqlite3.Error as e:
            db.get().rollback() # FIX: Changed from db.rollback() to db.get().rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500

    # Reset Endpoints
    @app.route('/api/reset_history', methods=['POST'])
    def reset_history():
        cursor = db.cursor()
        try:
            cursor.execute("DELETE FROM word_review_items;")
            cursor.execute("DELETE FROM study_sessions;")
            db.commit()
            return jsonify({"message": "Study history reset successfully."}), 200
        except sqlite3.Error as e:
            db.get().rollback() # FIX: Changed from db.rollback() to db.get().rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500

    @app.route('/api/full_reset', methods=['POST'])
    def full_reset():
        try:
            db.init_db_and_seed_data(app)
            return jsonify({"message": "Full system reset completed successfully. Database reinitialized with seed data."}), 200
        except Exception as e:
            return jsonify({"error": f"Full reset failed: {str(e)}"}), 500

    return app

# --- Main Execution Block ---
if __name__ == '__main__':
    app = create_app()

    # Initialize the database and seed data
    print("Populating sample data (core vocabulary and study activities only)...")
    # FIX: Wrapped db.init_db_and_seed_data(app) in app.app_context()
    # to ensure Flask's 'g' object is available during initialization.
    with app.app_context():
        db.init_db_and_seed_data(app)
    print("Sample data population complete.")

    # Terminate any existing ngrok tunnels
    ngrok.kill()

    # Retrieve ngrok authtoken from Colab Secrets
    ngrok_authtoken = None
    try:
        ngrok_authtoken = userdata.get("NGROK_AUTH_TOKEN")
        if ngrok_authtoken:
            print(f"NGROK_AUTH_TOKEN successfully retrieved from Colab Secrets.")
        else:
            print("NGROK_AUTH_TOKEN not found in Colab Secrets.")
            print("Please ensure you've added 'NGROK_AUTH_TOKEN' to Colab Secrets and enabled 'Notebook access'.")
            exit()
    except Exception as e:
        print(f"Error accessing Colab Secrets: {e}")
        print("Please ensure you've enabled 'Notebook access' for your NGROK_AUTH_TOKEN secret.")
        exit()

    try:
        ngrok.set_auth_token(ngrok_authtoken)
    except Exception as e:
        print(f"Error setting ngrok authtoken: {e}")
        print("Please ensure your NGROK_AUTH_TOKEN is valid.")
        exit()

    # Establish ngrok tunnel and run Flask app
    public_url = ngrok.connect(5000)
    print(f" * Tunnel URL: {public_url}")
    print(" * Serving Flask app '__main__'")
    print(" * Debug mode: off")
    print(" * Running on http://127.0.0.1:5000")
    print("INFO:werkzeug:Press CTRL+C to quit")
    
    app.run(debug=False, port=5000, use_reloader=False)
