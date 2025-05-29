# !pip install Flask Flask-Cors pytest pytest-flask pyngrok
import unittest
import sqlite3
import json
from flask import Flask, request, jsonify, g, url_for
from datetime import datetime, timedelta, timezone
import math # Import math for ceil in pagination calculations

# --- Re-create necessary parts of your Flask app for testing ---
# This is a simplified version of your create_app and Db class,
# adapted to use an in-memory database for testing.

DATABASE = ':memory:' # Use in-memory database for testing
PER_PAGE = 10 # Reduced for easier pagination testing, original was 100

# --- Embedded SQL Schema Definitions (Copied from your backend) ---
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

# --- Database Helper Class (Adapted for testing) ---
class TestDb:
    def __init__(self, database_path):
        self.database = database_path
        self.connection = None

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
        db_conn = g.pop('db', None)
        if db_conn is not None:
            db_conn.close()

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
        return group_id

    def import_study_activities_data(self, cursor, activities_list):
        """Imports study activities from a Python list."""
        for activity in activities_list:
            cursor.execute('''
            INSERT INTO study_activities (name, thumbnail_url, description, launch_url)
            VALUES (?, ?, ?, ?)
            ''', (activity['name'], activity['thumbnail_url'], activity['description'], activity['launch_url']))
        self.commit()

    def init_db_and_seed_data(self, app_instance):
        """
        Initializes the database by setting up tables and populating sample data.
        This method is called from the main app.py.
        """
        # Removed `with app_instance.app_context():`
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

        # Seed data for testing
        # We'll use a mix of real and generated data for pagination tests
        FRENCH_WORDS_GREETINGS = [
            {"french_word": "Bonjour", "quebec_pronunciation": "bon-zhoor", "english": "Hello", "parts": {"notes": "Common greeting"}},
            {"french_word": "Bonsoir", "quebec_pronunciation": "bon-swar", "english": "Good evening", "parts": {"notes": "Evening greeting"}},
            {"french_word": "Bonne nuit", "quebec_pronunciation": "bon-nwee", "english": "Good night", "parts": {"notes": "Before sleeping"}}
        ]

        FRENCH_WORDS_COMMON_PHRASES = [
            {"french_word": "Merci", "quebec_pronunciation": "mer-see", "english": "Thank you", "parts": {"notes": "Common expression of gratitude"}},
            {"french_word": "De rien", "quebec_pronunciation": "duh ree-ahn", "english": "You're welcome", "parts": {"notes": "Response to thank you"}},
            {"french_word": "S'il vous plaît", "quebec_pronunciation": "seel voo pleh", "english": "Please (formal)", "parts": {"notes": "Polite request"}},
            {"french_word": "Oui", "quebec_pronunciation": "wee", "english": "Yes", "parts": {"notes": "Affirmative answer"}},
            {"french_word": "Non", "quebec_pronunciation": "noh", "english": "No", "parts": {"notes": "Negative answer"}}
        ]

        # Generate enough words for pagination testing (e.g., 2.5 pages worth)
        NUM_PAGINATION_WORDS = 25 # 2.5 pages if PER_PAGE is 10
        pagination_words = []
        for i in range(NUM_PAGINATION_WORDS):
            pagination_words.append({
                "french_word": f"Word{i:02d}",
                "quebec_pronunciation": f"pron{i:02d}",
                "english": f"English{i:02d}",
                "parts": {"test": "pagination"}
            })

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
            }
        ]

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
        groups_map['Pagination Test Group'] = self.import_words_data(
            cursor=cursor,
            group_name='Pagination Test Group',
            words_list=pagination_words
        )

        self.import_study_activities_data(
            cursor=cursor,
            activities_list=STUDY_ACTIVITIES_DATA
        )

        # Store group and activity IDs for easy access in tests
        app_instance.config['TEST_GROUP_GREETINGS_ID'] = groups_map['Basic Greetings']
        app_instance.config['TEST_GROUP_COMMON_PHRASES_ID'] = groups_map['Common Phrases']
        app_instance.config['TEST_GROUP_PAGINATION_ID'] = groups_map['Pagination Test Group']

        app_instance.config['TEST_ACTIVITY_FLASHCARDS_ID'] = cursor.execute("SELECT id FROM study_activities WHERE name = 'Flashcards'").fetchone()[0]
        app_instance.config['TEST_ACTIVITY_QUIZ_ID'] = cursor.execute("SELECT id FROM study_activities WHERE name = 'Quiz'").fetchone()[0]

        # Get a word ID from the pagination group for review testing
        app_instance.config['TEST_WORD_ID_PAGINATION'] = cursor.execute("SELECT id FROM words WHERE french_word = 'Word00'").fetchone()[0]
        app_instance.config['TEST_WORD_ID_GREETING'] = cursor.execute("SELECT id FROM words WHERE french_word = 'Bonjour'").fetchone()[0]


# Instantiate the TestDb class
test_db_instance = TestDb(DATABASE)

# --- Helper Functions for API Endpoints (Copied from your backend) ---

def _format_datetime(dt_str):
    """Formats a datetime string to ISO 8601 with 'Z' for UTC."""
    if not dt_str:
        return None
    # Handle potential microseconds if present, then format
    try:
        dt_obj = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        dt_obj = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    return dt_obj.replace(tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z')

def _get_pagination_metadata(base_url, total_items, current_page, per_page):
    """Helper to generate pagination metadata."""
    total_pages = math.ceil(total_items / per_page) if per_page > 0 else 0
    if total_items == 0: total_pages = 0 # Ensure 0 pages if no items

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

# --- Flask Application Factory (Adapted for testing) ---

def create_test_app(test_config=None):
    app = Flask(__name__)

    # Apply configuration
    app.config.from_mapping(
        DATABASE=DATABASE,
        PER_PAGE=PER_PAGE # Use the test PER_PAGE
    )
    if test_config:
        app.config.update(test_config)

    # Database connection management
    @app.teardown_appcontext
    def close_connection(exception):
        test_db_instance.close()

    # --- API Routes (Copied directly from your backend) ---

    @app.route('/api')
    def api_root():
        return jsonify({"message": "Welcome to the Quebec French Language Portal API!"})

    # Dashboard Endpoints
    @app.route('/api/dashboard/last_study_session', methods=['GET'])
    def get_last_study_session():
        cursor = test_db_instance.cursor()
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
        cursor = test_db_instance.cursor()
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
        cursor = test_db_instance.cursor()
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
            # Adjust today if the last session was yesterday, to start streak from yesterday
            if session_dates and session_dates[0] == today - timedelta(days=1):
                current_day_for_streak = today - timedelta(days=1)
            for date in session_dates:
                if date == current_day_for_streak:
                    study_streak_days += 1
                    current_day_for_streak -= timedelta(days=1)
                elif date < current_day_for_streak: # Break if there's a gap
                    break
        return jsonify({
            "success_rate_percentage": round(success_rate_percentage, 2),
            "total_study_sessions": total_study_sessions,
            "total_active_groups": total_active_groups,
            "study_streak_days": study_streak_days
        })

    # Study Activities Endpoints
    @app.route('/api/study_activities', methods=['GET'])
    def get_study_activities():
        cursor = test_db_instance.cursor()
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', app.config['PER_PAGE'], type=int)
        offset = (page - 1) * limit
        query = "SELECT id, name, thumbnail_url, description, launch_url FROM study_activities LIMIT ? OFFSET ?;"
        activities = cursor.execute(query, (limit, offset)).fetchall()
        total_activities = cursor.execute("SELECT COUNT(*) FROM study_activities;").fetchone()[0]
        pagination = _get_pagination_metadata(url_for('get_study_activities', _external=True), total_activities, page, limit)
        result = [dict(activity) for activity in activities]
        return jsonify({"study_activities": result, "pagination": pagination})

    @app.route('/api/study_activities/<int:activity_id>', methods=['GET'])
    def get_study_activity_by_id(activity_id):
        cursor = test_db_instance.cursor()
        activity = cursor.execute("SELECT id, name, thumbnail_url, description, launch_url FROM study_activities WHERE id = ?", (activity_id,)).fetchone()
        if not activity: return jsonify({"error": "Study activity not found"}), 404
        return jsonify(dict(activity))

    @app.route('/api/study_activities/<int:activity_id>/study_sessions', methods=['GET'])
    def get_study_sessions_for_activity(activity_id):
        cursor = test_db_instance.cursor()
        activity = cursor.execute("SELECT id, name FROM study_activities WHERE id = ?", (activity_id,)).fetchone()
        if not activity: return jsonify({"error": "Study activity not found"}), 404
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', app.config['PER_PAGE'], type=int)
        offset = (page - 1) * limit
        query = """
            SELECT ss.id, g.name AS group_name, ss.created_at AS start_time, ss.end_time,
                   COUNT(wri.id) AS number_of_review_items
            FROM study_sessions ss JOIN groups g ON ss.group_id = g.id
            LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
            WHERE ss.study_activity_id = ? GROUP BY ss.id, g.name, ss.created_at, ss.end_time
            ORDER BY ss.created_at DESC LIMIT ? OFFSET ?;
        """
        study_sessions = cursor.execute(query, (activity_id, limit, offset)).fetchall()
        total_sessions_query = "SELECT COUNT(*) FROM study_sessions WHERE study_activity_id = ?;"
        total_sessions = cursor.execute(total_sessions_query, (activity_id,)).fetchone()[0]
        pagination = _get_pagination_metadata(url_for('get_study_sessions_for_activity', activity_id=activity_id, _external=True),
                                          total_sessions, page, limit)
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
        cursor = test_db_instance.cursor()
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
            test_db_instance.commit()
            session_id = cursor.lastrowid
            launch_url = f"{activity['launch_url']}?session_id={session_id}"
            return jsonify({
                "message": "Study activity session launched successfully.",
                "study_session_id": session_id,
                "launch_url": launch_url
            }), 201
        except sqlite3.Error as e:
            test_db_instance.get().rollback() # Corrected rollback call
            return jsonify({"error": f"Database error: {str(e)}"}), 500

    # Words Endpoints
    @app.route('/api/words', methods=['GET'])
    def get_words():
        cursor = test_db_instance.cursor()
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', app.config['PER_PAGE'], type=int)
        sort_by = request.args.get('sort_by', 'french_word')
        order = request.args.get('order', 'asc').upper()
        valid_sort_fields = ['french_word', 'quebec_pronunciation', 'english', 'correct_count', 'wrong_count']
        if sort_by not in valid_sort_fields: return jsonify({"error": f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"}), 400
        if order not in ['ASC', 'DESC']: return jsonify({"error": "Invalid order. Must be 'asc' or 'desc'"}), 400
        offset = (page - 1) * limit
        query = f"""
            SELECT w.id, w.french_word, w.quebec_pronunciation, w.english,
                   SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END) AS correct_count,
                   SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END) AS wrong_count
            FROM words w LEFT JOIN word_review_items wri ON w.id = wri.word_id
            GROUP BY w.id, w.french_word, w.quebec_pronunciation, w.english
            ORDER BY {sort_by} {order} LIMIT ? OFFSET ?;
        """
        words = cursor.execute(query, (limit, offset)).fetchall()
        total_words = cursor.execute("SELECT COUNT(*) FROM words;").fetchone()[0]
        pagination = _get_pagination_metadata(url_for('get_words', _external=True), total_words, page, limit)
        result = []
        for word in words:
            word_dict = dict(word)
            word_dict['correct_count'] = int(word_dict['correct_count'] or 0)
            word_dict['wrong_count'] = int(word_dict['wrong_count'] or 0)
            result.append(word_dict)
        return jsonify({"words": result, "pagination": pagination})

    @app.route('/api/words/<int:word_id>', methods=['GET'])
    def get_word_by_id(word_id):
        cursor = test_db_instance.cursor()
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
        cursor = test_db_instance.cursor()
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', app.config['PER_PAGE'], type=int)
        sort_by = request.args.get('sort_by', 'name')
        order = request.args.get('order', 'asc').upper()
        valid_sort_fields = ['name', 'word_count']
        if sort_by not in valid_sort_fields: return jsonify({"error": f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"}), 400
        if order not in ['ASC', 'DESC']: return jsonify({"error": "Invalid order. Must be 'asc' or 'desc'"}), 400
        offset = (page - 1) * limit
        query = f"""
            SELECT id, name, word_count FROM groups ORDER BY {sort_by} {order} LIMIT ? OFFSET ?;
        """
        groups = cursor.execute(query, (limit, offset)).fetchall()
        total_groups = cursor.execute("SELECT COUNT(*) FROM groups;").fetchone()[0]
        pagination = _get_pagination_metadata(url_for('get_groups', _external=True), total_groups, page, limit)
        result = [dict(group) for group in groups]
        return jsonify({"groups": result, "pagination": pagination})

    @app.route('/api/groups/<int:group_id>', methods=['GET'])
    def get_group_by_id(group_id):
        cursor = test_db_instance.cursor()
        group = cursor.execute("SELECT id, name, word_count AS total_word_count FROM groups WHERE id = ?", (group_id,)).fetchone()
        if not group: return jsonify({"error": "Group not found"}), 404
        return jsonify(dict(group))

    @app.route('/api/groups/<int:group_id>/words', methods=['GET'])
    def get_words_from_group(group_id):
        cursor = test_db_instance.cursor()
        group = cursor.execute("SELECT id, name FROM groups WHERE id = ?", (group_id,)).fetchone()
        if not group: return jsonify({"error": "Group not found"}), 404
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', app.config['PER_PAGE'], type=int)
        sort_by = request.args.get('sort_by', 'french_word')
        order = request.args.get('order', 'asc').upper()
        valid_sort_fields = ['french_word', 'quebec_pronunciation', 'english', 'correct_count', 'wrong_count']
        if sort_by not in valid_sort_fields: return jsonify({"error": f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"}), 400
        if order not in ['ASC', 'DESC']: return jsonify({"error": "Invalid order. Must be 'asc' or 'desc'"}), 400
        offset = (page - 1) * limit
        query = f"""
            SELECT w.id, w.french_word, w.quebec_pronunciation, w.english,
                   SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END) AS correct_count,
                   SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END) AS wrong_count
            FROM words w JOIN words_groups wg ON w.id = wg.word_id
            LEFT JOIN word_review_items wri ON w.id = wri.word_id
            WHERE wg.group_id = ? GROUP BY w.id, w.french_word, w.quebec_pronunciation, w.english
            ORDER BY {sort_by} {order} LIMIT ? OFFSET ?;
        """
        words = cursor.execute(query, (group_id, limit, offset)).fetchall()
        total_words_in_group = cursor.execute("SELECT word_count FROM groups WHERE id = ?;", (group_id,)).fetchone()[0]
        pagination = _get_pagination_metadata(url_for('get_words_from_group', group_id=group_id, _external=True),
                                          total_words_in_group, page, limit)
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
        cursor = test_db_instance.cursor()
        group = cursor.execute("SELECT id, name FROM groups WHERE id = ?", (group_id,)).fetchone()
        if not group: return jsonify({"error": "Group not found"}), 404
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', app.config['PER_PAGE'], type=int)
        offset = (page - 1) * limit
        query = """
            SELECT ss.id, sa.name AS activity_name, g.name AS group_name,
                   ss.created_at AS start_time, ss.end_time,
                   COUNT(wri.id) AS number_of_review_items
            FROM study_sessions ss JOIN study_activities sa ON ss.study_activity_id = sa.id
            JOIN groups g ON ss.group_id = g.id LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
            WHERE ss.group_id = ? GROUP BY ss.id, sa.name, g.name, ss.created_at, ss.end_time
            ORDER BY ss.created_at DESC LIMIT ? OFFSET ?;
        """
        study_sessions = cursor.execute(query, (group_id, limit, offset)).fetchall()
        total_sessions_query = "SELECT COUNT(*) FROM study_sessions WHERE group_id = ?;"
        total_sessions = cursor.execute(total_sessions_query, (group_id,)).fetchone()[0]
        pagination = _get_pagination_metadata(url_for('get_study_sessions_for_group', group_id=group_id, _external=True),
                                          total_sessions, page, limit)
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
        cursor = test_db_instance.cursor()
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', app.config['PER_PAGE'], type=int)
        offset = (page - 1) * limit
        query = """
            SELECT ss.id, sa.name AS activity_name, g.name AS group_name,
                   ss.created_at AS start_time, ss.end_time,
                   COUNT(wri.id) AS number_of_review_items
            FROM study_sessions ss JOIN study_activities sa ON ss.study_activity_id = sa.id
            JOIN groups g ON ss.group_id = g.id LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
            GROUP BY ss.id, sa.name, g.name, ss.created_at, ss.end_time
            ORDER BY ss.created_at DESC LIMIT ? OFFSET ?;
        """
        study_sessions = cursor.execute(query, (limit, offset)).fetchall()
        total_sessions = cursor.execute("SELECT COUNT(*) FROM study_sessions;").fetchone()[0]
        pagination = _get_pagination_metadata(url_for('get_all_study_sessions', _external=True), total_sessions, page, limit)
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
        cursor = test_db_instance.cursor()
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
        cursor = test_db_instance.cursor()
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
        cursor = test_db_instance.cursor()
        data = request.get_json()
        correct = data.get('correct')
        if correct is None: return jsonify({"error": "Correct status is required"}), 400
        if not isinstance(correct, bool): return jsonify({"error": "Correct status must be a boolean (true/false)"}), 400
        session_exists = cursor.execute("SELECT 1 FROM study_sessions WHERE id = ?", (session_id,)).fetchone()
        if not session_exists: return jsonify({"error": "Study session not found"}), 404
        word_exists = cursor.execute("SELECT 1 FROM words WHERE id = ?", (word_id,)).fetchone()
        if not word_exists: return jsonify({"error": "Word not found"}), 404
        try:
            current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f') # Added microseconds for more unique timestamps
            cursor.execute("INSERT INTO word_review_items (word_id, study_session_id, correct, created_at) VALUES (?, ?, ?, ?)",
                           (word_id, session_id, 1 if correct else 0, current_time))
            test_db_instance.commit()
            review_id = cursor.lastrowid
            cursor.execute("UPDATE study_sessions SET end_time = ? WHERE id = ?", (current_time, session_id))
            test_db_instance.commit()
            return jsonify({
                "message": "Word review recorded successfully.", "review_item_id": review_id,
                "word_id": word_id, "study_session_id": session_id, "correct": correct,
                "created_at": _format_datetime(current_time)
            }), 201
        except sqlite3.Error as e:
            test_db_instance.get().rollback() # Corrected rollback call
            return jsonify({"error": f"Database error: {str(e)}"}), 500

    # Reset Endpoints
    @app.route('/api/reset_history', methods=['POST'])
    def reset_history():
        cursor = test_db_instance.cursor()
        try:
            cursor.execute("DELETE FROM word_review_items;")
            cursor.execute("DELETE FROM study_sessions;")
            test_db_instance.commit()
            return jsonify({"message": "Study history reset successfully."}), 200
        except sqlite3.Error as e:
            test_db_instance.get().rollback() # Corrected rollback call
            return jsonify({"error": f"Database error: {str(e)}"}), 500

    @app.route('/api/full_reset', methods=['POST'])
    def full_reset():
        try:
            test_db_instance.init_db_and_seed_data(app)
            return jsonify({"message": "Full system reset completed successfully. Database reinitialized with seed data."}), 200
        except Exception as e:
            return jsonify({"error": f"Full reset failed: {str(e)}"}), 500

    return app

# --- Unit Tests ---

class FrenchApiTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # This will be called once for all tests in this class
        cls.app = create_test_app()
        cls.client = cls.app.test_client()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        # Initialize and seed the database for the entire test class
        test_db_instance.init_db_and_seed_data(cls.app)

        # Store IDs from seeding for use in tests
        cls.group_greetings_id = cls.app.config['TEST_GROUP_GREETINGS_ID']
        cls.group_common_phrases_id = cls.app.config['TEST_GROUP_COMMON_PHRASES_ID']
        cls.group_pagination_id = cls.app.config['TEST_GROUP_PAGINATION_ID']
        cls.activity_flashcards_id = cls.app.config['TEST_ACTIVITY_FLASHCARDS_ID']
        cls.activity_quiz_id = cls.app.config['TEST_ACTIVITY_QUIZ_ID']
        cls.word_id_pagination = cls.app.config['TEST_WORD_ID_PAGINATION']
        cls.word_id_greeting = cls.app.config['TEST_WORD_ID_GREETING']

    @classmethod
    def tearDownClass(cls):
        # This will be called once after all tests in this class
        cls.app_context.pop()

    def setUp(self):
        # This runs before each test method.
        # We'll run a full reset to ensure a clean slate for each test.
        # This call will now operate within the existing app context and should correctly re-initialize the DB.
        with self.app.app_context(): # Ensure we are in the app context
            self.client.post('/api/full_reset')


    # Test Case 1: GET /api/words - Default pagination (page 1, PER_PAGE items)
    def test_1_get_words_default_pagination(self):
        response = self.client.get('/api/words')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIn('words', data)
        self.assertIn('pagination', data)
        self.assertEqual(len(data['words']), PER_PAGE)
        self.assertEqual(data['pagination']['current_page'], 1)
        self.assertEqual(data['pagination']['items_per_page'], PER_PAGE)
        self.assertIsNotNone(data['pagination']['next_page']) # Should have a next page

    # Test Case 2: GET /api/words - Second page
    def test_2_get_words_second_page(self):
        response = self.client.get(f'/api/words?page=2&limit={PER_PAGE}')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIn('words', data)
        self.assertIn('pagination', data)
        self.assertEqual(len(data['words']), PER_PAGE) # Should still get PER_PAGE items
        self.assertEqual(data['pagination']['current_page'], 2)
        self.assertIsNotNone(data['pagination']['prev_page'])
        # Depending on total words, next_page might be null or not
        total_words = test_db_instance.cursor().execute("SELECT COUNT(*) FROM words").fetchone()[0]
        if (2 * PER_PAGE) >= total_words:
            self.assertIsNone(data['pagination']['next_page'])
        else:
            self.assertIsNotNone(data['pagination']['next_page'])


    # Test Case 3: GET /api/words - Custom limit
    def test_3_get_words_custom_limit(self):
        custom_limit = 5
        response = self.client.get(f'/api/words?limit={custom_limit}')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(len(data['words']), custom_limit)
        self.assertEqual(data['pagination']['items_per_page'], custom_limit)

    # Test Case 4: GET /api/words - Page out of bounds
    def test_4_get_words_page_out_of_bounds(self):
        response = self.client.get(f'/api/words?page=999&limit={PER_PAGE}')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(len(data['words']), 0) # Should return empty list
        self.assertEqual(data['pagination']['current_page'], 999)
        self.assertIsNone(data['pagination']['next_page'])

    # Test Case 5: GET /api/words - Sorting by English in descending order
    def test_5_get_words_sorting(self):
        response = self.client.get('/api/words?sort_by=english&order=desc')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIn('words', data)
        # Verify sorting (check first two items)
        if len(data['words']) >= 2:
            self.assertGreaterEqual(data['words'][0]['english'], data['words'][1]['english'])

    # Test Case 6: GET /api/groups - Default pagination
    def test_6_get_groups_default_pagination(self):
        response = self.client.get('/api/groups')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIn('groups', data)
        self.assertIn('pagination', data)
        self.assertEqual(len(data['groups']), 3) # We seeded 3 groups
        self.assertEqual(data['pagination']['current_page'], 1)
        self.assertEqual(data['pagination']['items_per_page'], PER_PAGE)
        self.assertIsNone(data['pagination']['next_page']) # Should be no next page with 3 groups and PER_PAGE=10

    # Test Case 7: GET /api/groups - Page 2 (should be empty as we only have 3 groups)
    def test_7_get_groups_second_page_empty(self):
        response = self.client.get(f'/api/groups?page=2&limit={PER_PAGE}')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(len(data['groups']), 0)
        self.assertEqual(data['pagination']['current_page'], 2)
        self.assertIsNotNone(data['pagination']['prev_page'])
        self.assertIsNone(data['pagination']['next_page'])

    # Test Case 8: GET /api/groups/:id/words - Default for a specific group (pagination test group)
    def test_8_get_group_words_default_pagination(self):
        response = self.client.get(f'/api/groups/{self.group_pagination_id}/words')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIn('words', data)
        self.assertIn('pagination', data)
        self.assertEqual(len(data['words']), PER_PAGE)
        self.assertEqual(data['pagination']['current_page'], 1)
        self.assertEqual(data['pagination']['items_per_page'], PER_PAGE)
        self.assertIsNotNone(data['pagination']['next_page'])

    # Test Case 9: GET /api/groups/:id/words - Second page of a specific group
    def test_9_get_group_words_second_page(self):
        response = self.client.get(f'/api/groups/{self.group_pagination_id}/words?page=2&limit={PER_PAGE}')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIn('words', data)
        self.assertIn('pagination', data)
        self.assertEqual(len(data['words']), PER_PAGE)
        self.assertEqual(data['pagination']['current_page'], 2)
        self.assertIsNotNone(data['pagination']['prev_page'])
        self.assertIsNotNone(data['pagination']['next_page']) # Should still have a next page

    # Test Case 10: GET /api/groups/:id/words - Third page of a specific group (should have 5 items)
    def test_10_get_group_words_third_page(self):
        response = self.client.get(f'/api/groups/{self.group_pagination_id}/words?page=3&limit={PER_PAGE}')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIn('words', data)
        self.assertIn('pagination', data)
        self.assertEqual(len(data['words']), 5) # 25 total words, 10 per page -> 10, 10, 5
        self.assertEqual(data['pagination']['current_page'], 3)
        self.assertIsNotNone(data['pagination']['prev_page'])
        self.assertIsNone(data['pagination']['next_page'])

    # Test Case 11: GET /api/study_sessions - All sessions (should be empty initially)
    def test_11_get_all_study_sessions_empty(self):
        response = self.client.get('/api/study_sessions')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIn('study_sessions', data)
        self.assertEqual(len(data['study_sessions']), 0)
        self.assertEqual(data['pagination']['total_items'], 0)

    # Test Case 12: POST /api/study_activities - Create a study session
    def test_12_create_study_session(self):
        payload = {
            "group_id": self.group_greetings_id,
            "study_activity_id": self.activity_flashcards_id
        }
        response = self.client.post('/api/study_activities', json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertIn('study_session_id', data)
        self.assertIn('launch_url', data)
        self.assertIsInstance(data['study_session_id'], int)
        self.assertTrue(f"session_id={data['study_session_id']}" in data['launch_url'])

        # Verify session was created
        response_get = self.client.get(f'/api/study_sessions/{data["study_session_id"]}')
        self.assertEqual(response_get.status_code, 200)
        session_data = response_get.json
        self.assertEqual(session_data['group_name'], 'Basic Greetings')
        self.assertEqual(session_data['activity_name'], 'Flashcards')

    # Test Case 13: GET /api/dashboard/last_study_session - After creating a session
    def test_13_get_last_study_session_after_creation(self):
        # First, create a session
        payload = {
            "group_id": self.group_greetings_id,
            "study_activity_id": self.activity_flashcards_id
        }
        self.client.post('/api/study_activities', json=payload)

        response = self.client.get('/api/dashboard/last_study_session')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIn('id', data)
        self.assertEqual(data['group_name'], 'Basic Greetings')
        self.assertEqual(data['total_words_reviewed'], 0) # No reviews yet

    # Test Case 14: POST /api/study_sessions/:id/words/:word_id/review - Log a correct review
    def test_14_log_word_review_correct(self):
        # Create a session first
        session_payload = {
            "group_id": self.group_pagination_id,
            "study_activity_id": self.activity_quiz_id
        }
        session_response = self.client.post('/api/study_activities', json=session_payload)
        session_id = session_response.json['study_session_id']

        # Log a correct review
        review_payload = {"correct": True}
        review_response = self.client.post(f'/api/study_sessions/{session_id}/words/{self.word_id_pagination}/review', json=review_payload)
        self.assertEqual(review_response.status_code, 201)
        data = review_response.json
        self.assertIn('review_item_id', data)
        self.assertEqual(data['word_id'], self.word_id_pagination)
        self.assertEqual(data['study_session_id'], session_id)
        self.assertTrue(data['correct'])

        # Verify review count for the session
        session_detail_response = self.client.get(f'/api/study_sessions/{session_id}')
        self.assertEqual(session_detail_response.status_code, 200)
        session_detail_data = session_detail_response.json
        self.assertEqual(session_detail_data['number_of_review_items'], 1)
        self.assertIsNotNone(session_detail_data['end_time'])

    # Test Case 15: POST /api/study_sessions/:id/words/:word_id/review - Log an incorrect review
    def test_15_log_word_review_incorrect(self):
        # Create a session first
        session_payload = {
            "group_id": self.group_greetings_id,
            "study_activity_id": self.activity_flashcards_id
        }
        session_response = self.client.post('/api/study_activities', json=session_payload)
        session_id = session_response.json['study_session_id']

        # Log an incorrect review
        review_payload = {"correct": False}
        review_response = self.client.post(f'/api/study_sessions/{session_id}/words/{self.word_id_greeting}/review', json=review_payload)
        self.assertEqual(review_response.status_code, 201)
        data = review_response.json
        self.assertIn('review_item_id', data)
        self.assertEqual(data['word_id'], self.word_id_greeting)
        self.assertEqual(data['study_session_id'], session_id)
        self.assertFalse(data['correct'])

        # Verify review count for the session
        session_detail_response = self.client.get(f'/api/study_sessions/{session_id}')
        self.assertEqual(session_detail_response.status_code, 200)
        session_detail_data = session_detail_response.json
        self.assertEqual(session_detail_data['number_of_review_items'], 1)


    # Test Case 16: GET /api/dashboard/study_progress - After logging reviews
    def test_16_get_study_progress_after_reviews(self):
        # Log a few reviews across different words/sessions
        session1_id = self.client.post('/api/study_activities', json={"group_id": self.group_greetings_id, "study_activity_id": self.activity_flashcards_id}).json['study_session_id']
        session2_id = self.client.post('/api/study_activities', json={"group_id": self.group_common_phrases_id, "study_activity_id": self.activity_quiz_id}).json['study_session_id']

        self.client.post(f'/api/study_sessions/{session1_id}/words/{self.word_id_greeting}/review', json={"correct": True})
        self.client.post(f'/api/study_sessions/{session1_id}/words/{self.word_id_greeting}/review', json={"correct": False})
        self.client.post(f'/api/study_sessions/{session2_id}/words/{self.word_id_pagination}/review', json={"correct": True})

        response = self.client.get('/api/dashboard/study_progress')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertGreaterEqual(data['total_words_studied'], 2) # At least 2 unique words
        self.assertGreater(data['total_vocabulary_in_db'], 0)
        self.assertGreaterEqual(data['mastery_percentage'], 0.0)

    # Test Case 17: GET /api/dashboard/quick-stats - After logging reviews
    def test_17_get_quick_stats_after_reviews(self):
        # Log a few reviews and sessions to populate stats
        session1_id = self.client.post('/api/study_activities', json={"group_id": self.group_greetings_id, "study_activity_id": self.activity_flashcards_id}).json['study_session_id']
        session2_id = self.client.post('/api/study_activities', json={"group_id": self.group_common_phrases_id, "study_activity_id": self.activity_quiz_id}).json['study_session_id']
        session3_id = self.client.post('/api/study_activities', json={"group_id": self.group_pagination_id, "study_activity_id": self.activity_flashcards_id}).json['study_session_id']

        self.client.post(f'/api/study_sessions/{session1_id}/words/{self.word_id_greeting}/review', json={"correct": True})
        self.client.post(f'/api/study_sessions/{session1_id}/words/{self.word_id_greeting}/review', json={"correct": True})
        self.client.post(f'/api/study_sessions/{session2_id}/words/{self.word_id_pagination}/review', json={"correct": False})
        self.client.post(f'/api/study_sessions/{session3_id}/words/{self.word_id_pagination}/review', json={"correct": True})

        response = self.client.get('/api/dashboard/quick-stats')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertGreaterEqual(data['total_study_sessions'], 3)
        self.assertGreaterEqual(data['total_active_groups'], 3)
        self.assertGreaterEqual(data['success_rate_percentage'], 0.0)
        self.assertGreaterEqual(data['study_streak_days'], 1) # At least 1 day if sessions were logged today

    # Test Case 18: GET /api/words/:id - Get a specific word
    def test_18_get_specific_word(self):
        response = self.client.get(f'/api/words/{self.word_id_greeting}')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data['id'], self.word_id_greeting)
        self.assertEqual(data['french_word'], 'Bonjour')
        self.assertIn('study_statistics', data)
        self.assertIn('word_groups', data)
        self.assertIsInstance(data['word_groups'], list)
        self.assertGreater(len(data['word_groups']), 0)

    # Test Case 19: GET /api/words/:id - Word not found
    def test_19_get_non_existent_word(self):
        response = self.client.get('/api/words/99999')
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json)
        self.assertEqual(response.json['error'], 'Word not found')

    # Test Case 20: POST /api/reset_history
    def test_20_reset_history(self):
        # First, create some sessions and reviews to ensure there's data to reset
        session_id = self.client.post('/api/study_activities', json={"group_id": self.group_greetings_id, "study_activity_id": self.activity_flashcards_id}).json['study_session_id']
        self.client.post(f'/api/study_sessions/{session_id}/words/{self.word_id_greeting}/review', json={"correct": True})

        # Check that data exists
        response_sessions = self.client.get('/api/study_sessions')
        self.assertGreater(len(response_sessions.json['study_sessions']), 0)

        # Now, reset history
        response_reset = self.client.post('/api/reset_history')
        self.assertEqual(response_reset.status_code, 200)
        self.assertEqual(response_reset.json['message'], 'Study history reset successfully.')

        # Verify history is empty
        response_sessions_after_reset = self.client.get('/api/study_sessions')
        self.assertEqual(len(response_sessions_after_reset.json['study_sessions']), 0)
        self.assertEqual(response_sessions_after_reset.json['pagination']['total_items'], 0)

# Run the tests
if __name__ == '__main__':
    # This block will run the tests when the script is executed
    unittest.main(argv=['first-arg-is-ignored'], exit=False)