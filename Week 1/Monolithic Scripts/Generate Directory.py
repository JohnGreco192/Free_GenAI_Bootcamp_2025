import os

# Define the base directory for the backend project
base_dir = "/content/backend"

# Your ngrok authentication token to be hardcoded in app.py
# IMPORTANT: Replace this with your actual token if it changes, or mask it before sharing!
# You requested it at the top of this script for easy masking later.
NGROK_TOKEN_TO_HARDCODE = "######"

# Define the directory structure and file contents
file_structure = {
    f"{base_dir}/app.py": f"""
# backend/app.py
import sqlite3
import json
import os
from flask import Flask, request, jsonify, g, url_for
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
from pyngrok import ngrok

# --- NGROK AUTH TOKEN (HARDCODED) ---
# This token is hardcoded for direct Colab execution as requested.
# For production environments, consider more secure environment variable management.
NGROK_AUTH_TOKEN_HARDCODED = "{NGROK_TOKEN_TO_HARDCODE}"

# Import database and utility modules
from lib.db import db
from lib.utils import _format_datetime, _get_pagination_metadata

# Import route modules
import routes.dashboard
import routes.study_activities
import routes.words
import routes.groups
import routes.study_sessions

# --- Configuration ---
DATABASE = 'lang_portal.db'
PER_PAGE = 100 # Default items per page for pagination

# --- Flask Application Factory ---
def create_app(test_config=None):
    \"\"\"
    Creates and configures the Flask application.
    \"\"\"
    app = Flask(__name__)

    # Apply configuration
    if test_config is None:
        app.config.from_mapping(
            DATABASE=DATABASE,
            PER_PAGE=PER_PAGE
        )
    else:
        app.config.update(test_config)

    # Database connection management: close connection after each request
    @app.teardown_appcontext
    def close_connection(exception):
        db.close()

    # Configure CORS to allow cross-origin requests for API endpoints
    CORS(app, resources={{
        r"/api/*": {{
            "origins": "*",  # Allows all origins for development. Restrict in production.
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }}
    }})

    # --- API Routes ---
    # Root API endpoint
    @app.route('/api')
    def api_root():
        return jsonify({{"message": "Welcome to the Quebec French Language Portal API!"}})

    # Load routes from respective modules
    routes.dashboard.load(app)
    routes.study_activities.load(app)
    routes.words.load(app)
    routes.groups.load(app)
    routes.study_sessions.load(app)
    
    return app

# --- Main Execution Block ---
if __name__ == '__main__':
    # Create the Flask application instance
    app = create_app()

    # Initialize the database and seed data
    print("Populating sample data (core vocabulary and study activities only)...")
    # Wrap db.init_db_and_seed_data(app) in app.app_context()
    # to ensure Flask's 'g' object is available during initialization.
    with app.app_context():
        db.init_db_and_seed_data(app)
    print("Sample data population complete.")

    # Terminate any existing ngrok tunnels to prevent conflicts
    ngrok.kill()

    # Set the ngrok authentication token from the hardcoded variable
    try:
        ngrok.set_auth_token(NGROK_AUTH_TOKEN_HARDCODED)
        print("ngrok authentication token set from hardcoded value.")
    except Exception as e:
        print(f"FATAL ERROR: Could not set ngrok authtoken with the hardcoded token: {{e}}")
        print("Please ensure your hardcoded NGROK_AUTH_TOKEN is valid. Exiting.")
        exit()

    # Establish ngrok tunnel and run Flask app
    public_url = ngrok.connect(5000)
    print(f" * Tunnel URL: {{public_url}}")
    print(" * Serving Flask app '__main__'")
    print(" * Debug mode: off")
    print(" * Running on http://127.0.0.1:5000")
    print("INFO:werkzeug:Press CTRL+C to quit")

    # Run the Flask application
    app.run(debug=False, port=5000, use_reloader=False)
""",
    f"{base_dir}/lib/db.py": """
# backend/lib/db.py
import sqlite3
import json
import os
from flask import g # Flask's 'g' object for request-specific global variables

class Db:
  \"\"\"
  Database helper class for managing SQLite connections and operations.
  Uses Flask's `g` object to ensure a single database connection per request.
  \"\"\"
  def __init__(self, database='lang_portal.db'):
    \"\"\"
    Initializes the Db instance with the database file path.
    \"\"\"
    self.database = database
    self.connection = None # Connection will be managed by Flask's g

  def get(self):
    \"\"\"
    Gets the database connection for the current request context.
    If a connection doesn't exist in `g`, it creates one.
    \"\"\"
    if 'db' not in g:
      g.db = sqlite3.connect(self.database)
      g.db.row_factory = sqlite3.Row  # Return rows as dictionary-like objects
    return g.db

  def commit(self):
    \"\"\"
    Commits any pending transactions to the database.
    \"\"\"
    self.get().commit()

  def cursor(self):
    \"\"\"
    Returns a database cursor.
    \"\"\"
    return self.get().cursor()

  def close(self):
    \"\"\"
    Closes the database connection for the current request context.
    Called automatically by Flask's teardown_appcontext.
    \"\"\"
    db_conn = g.pop('db', None)
    if db_conn is not None:
      db_conn.close()

  def sql(self, filepath):
    \"\"\"
    Reads and returns the content of an SQL file.
    Assumes SQL files are in the 'sql/' directory relative to the project root.
    \"\"\"
    # Construct the absolute path to the SQL file
    # Assuming 'backend' is the root, and 'lib' is inside 'backend'
    current_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(current_dir, '..')) # Go up one level from 'lib'
    sql_file_path = os.path.join(project_root, 'sql', filepath)
    
    with open(sql_file_path, 'r') as file:
      return file.read()

  def load_json(self, filepath):
    \"\"\"
    Reads and returns the content of a JSON file.
    Assumes JSON files are in the 'seed/' directory relative to the project root.
    \"\"\"
    # Construct the absolute path to the JSON file
    current_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(current_dir, '..')) # Go up one level from 'lib'
    json_file_path = os.path.join(project_root, 'seed', filepath)

    with open(json_file_path, 'r', encoding='utf-8') as file:
      return json.load(file)

  def setup_tables(self, cursor):
    \"\"\"
    Executes all table creation SQL scripts.
    \"\"\"
    cursor.execute(self.sql('setup/create_table_words.sql'))
    self.commit()
    cursor.execute(self.sql('setup/create_table_groups.sql'))
    self.commit()
    cursor.execute(self.sql('setup/create_table_words_groups.sql'))
    self.commit()
    cursor.execute(self.sql('setup/create_table_study_activities.sql'))
    self.commit()
    cursor.execute(self.sql('setup/create_table_study_sessions.sql'))
    self.commit()
    cursor.execute(self.sql('setup/create_table_word_review_items.sql'))
    self.commit()

  def import_words_data(self, cursor, group_name, data_json_path):
    \"\"\"
    Imports words from a JSON file and links them to a group.
    \"\"\"
    # Insert a new group
    cursor.execute('INSERT INTO groups (name) VALUES (?)', (group_name,))
    self.commit()

    # Get the ID of the newly inserted group
    cursor.execute('SELECT id FROM groups WHERE name = ?', (group_name,))
    group_id = cursor.fetchone()[0]

    # Load words from the specified JSON file
    words = self.load_json(data_json_path)

    for word in words:
      # Insert the word into the words table
      cursor.execute('''
        INSERT INTO words (french_word, quebec_pronunciation, english, parts)
        VALUES (?, ?, ?, ?)
      ''', (word['french_word'], word['quebec_pronunciation'], word['english'], json.dumps(word['parts'])))
      
      # Get the last inserted word's ID
      word_id = cursor.lastrowid

      # Insert the word-group relationship into word_groups table
      cursor.execute('''
        INSERT INTO words_groups (word_id, group_id) VALUES (?, ?)
      ''', (word_id, group_id))
    self.commit()

    # Update the words_count in the groups table by counting all words in the group
    cursor.execute('''
      UPDATE groups
      SET word_count = (
        SELECT COUNT(*) FROM words_groups WHERE group_id = ?
      )
      WHERE id = ?
    ''', (group_id, group_id))
    self.commit()

    print(f"Successfully added {len(words)} words to the '{group_name}' group.")
    return group_id

  def import_study_activities_data(self, cursor, data_json_path):
    \"\"\"
    Imports study activities from a JSON file.
    \"\"\"
    activities_list = self.load_json(data_json_path)
    for activity in activities_list:
      cursor.execute('''
      INSERT INTO study_activities (name, thumbnail_url, description, launch_url)
      VALUES (?, ?, ?, ?)
      ''', (activity['name'], activity['thumbnail_url'], activity['description'], activity['launch_url']))
    self.commit()
    print(f"Successfully added {len(activities_list)} study activities.")

  def init_db_and_seed_data(self, app_instance):
    \"\"\"
    Initializes the database by setting up tables and populating sample data.
    This method is called from the main app.py.
    \"\"\"
    cursor = self.cursor()

    # Drop all tables for a clean re-initialization (useful for development)
    cursor.execute("DROP TABLE IF EXISTS word_review_items;")
    cursor.execute("DROP TABLE IF EXISTS study_sessions;")
    cursor.execute("DROP TABLE IF EXISTS study_activities;")
    cursor.execute("DROP TABLE IF EXISTS words_groups;")
    cursor.execute("DROP TABLE IF EXISTS groups;")
    cursor.execute("DROP TABLE IF EXISTS words;")
    self.commit() # Commit after dropping tables

    # Setup new tables
    self.setup_tables(cursor)

    # Import words and groups from embedded data (now from JSON files)
    groups_map = {}
    groups_map['Basic Greetings'] = self.import_words_data(
        cursor=cursor,
        group_name='Basic Greetings',
        data_json_path='data_greetings.json'
    )
    groups_map['Common Phrases'] = self.import_words_data(
        cursor=cursor,
        group_name='Common Phrases',
        data_json_path='data_common_phrases.json'
    )
    groups_map['Quebecois Slang'] = self.import_words_data(
        cursor=cursor,
        group_name='Quebecois Slang',
        data_json_path='data_quebecois_slang.json'
    )
    groups_map['Quebecois Culture'] = self.import_words_data(
        cursor=cursor,
        group_name='Quebecois Culture',
        data_json_path='data_quebecois_culture.json'
    )
    groups_map['Everyday Objects'] = self.import_words_data(
        cursor=cursor,
        group_name='Everyday Objects',
        data_json_path='data_everyday_objects.json'
    )
    groups_map['Everyday Adjectives'] = self.import_words_data(
        cursor=cursor,
        group_name='Everyday Adjectives',
        data_json_path='data_everyday_adjectives.json'
    )

    self.import_study_activities_data(
        cursor=cursor,
        data_json_path='study_activities.json'
    )

    # Note: Study sessions and review items are NOT seeded here to mimic the
    # initial state of the Japanese backend. These tables will be empty
    # until new sessions are created via API calls.

    print("Core vocabulary and study activities populated. Study history tables are initialized but empty.")

# Instantiate the Db class with the default database name
# This instance will be imported and used across the application
db = Db('lang_portal.db')
""",
    f"{base_dir}/lib/utils.py": """
# backend/lib/utils.py
from datetime import datetime, timedelta, timezone
from flask import url_for # Used to generate URLs for pagination links

def _format_datetime(dt_str):
    \"\"\"
    Formats a datetime string to ISO 8601 with 'Z' for UTC.
    Handles both with and without microseconds.
    \"\"\"
    if not dt_str:
        return None
    try:
        # Try parsing with microseconds first
        dt_obj = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        # Fallback to parsing without microseconds
        dt_obj = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    
    # Ensure the datetime object is timezone-aware (UTC) before formatting
    return dt_obj.replace(tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z')


def _get_pagination_metadata(endpoint_name, total_items, current_page, per_page, **kwargs):
    \"\"\"
    Helper to generate pagination metadata, including next/prev page URLs.
    Args:
        endpoint_name (str): The name of the Flask endpoint for URL generation.
        total_items (int): Total number of items available.
        current_page (int): The current page number (1-indexed).
        per_page (int): Number of items per page.
        **kwargs: Additional keyword arguments to pass to url_for (e.g., group_id).
    Returns:
        dict: A dictionary containing pagination details.
    \"\"\"
    total_pages = (total_items + per_page - 1) // per_page # Calculate total pages, rounding up
    next_page = None
    prev_page = None

    # Generate URL for the next page if it exists
    if current_page < total_pages:
        next_page = url_for(endpoint_name, page=current_page + 1, limit=per_page, _external=True, **kwargs)
    
    # Generate URL for the previous page if it exists
    if current_page > 1:
        prev_page = url_for(endpoint_name, page=current_page - 1, limit=per_page, _external=True, **kwargs)

    return {
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": current_page,
        "items_per_page": per_page,
        "next_page": next_page,
        "prev_page": prev_page
    }
""",
    f"{base_dir}/routes/dashboard.py": """
# backend/routes/dashboard.py
from flask import jsonify, request
from flask_cors import cross_origin
from datetime import datetime, timedelta, timezone
from lib.db import db
from lib.utils import _format_datetime

def load(app):
    \"\"\"
    Registers dashboard-related API routes with the Flask application.
    \"\"\"

    @app.route('/api/dashboard/last_study_session', methods=['GET'])
    @cross_origin()
    def get_last_study_session():
        \"\"\"
        Retrieves details of the most recent study session.
        Includes group name, start/end times, and review counts.
        \"\"\"
        cursor = db.cursor()
        query = \"\"\"
            SELECT ss.id, g.name AS group_name, ss.created_at, ss.end_time,
                   SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END) AS correct_count,
                   SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END) AS incorrect_count,
                   COUNT(wri.id) AS total_words_reviewed
            FROM study_sessions ss
            JOIN groups g ON ss.group_id = g.id
            LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
            GROUP BY ss.id, g.name, ss.created_at, ss.end_time
            ORDER BY ss.created_at DESC LIMIT 1;
        \"\"\"
        last_session = cursor.execute(query).fetchone()
        
        if not last_session:
            return jsonify({"message": "No study sessions found."}), 404
        
        result = dict(last_session)
        # Ensure counts are integers, defaulting to 0 if NULL
        result['correct_count'] = int(result['correct_count'] or 0)
        result['incorrect_count'] = int(result['incorrect_count'] or 0)
        result['total_words_reviewed'] = int(result['total_words_reviewed'] or 0)
        # Format datetime strings
        result['created_at'] = _format_datetime(result['created_at'])
        result['end_time'] = _format_datetime(result['end_time'])
        
        return jsonify(result)

    @app.route('/api/dashboard/study_progress', methods=['GET'])
    @cross_origin()
    def get_study_progress():
        \"\"\"
        Provides overall study progress statistics, including total words studied
        and mastery percentage.
        \"\"\"
        cursor = db.cursor()
        
        # Get count of unique words that have been reviewed
        total_words_studied = cursor.execute("SELECT COUNT(DISTINCT word_id) FROM word_review_items;").fetchone()[0]
        
        # Get total number of words in the database
        total_vocabulary_in_db = cursor.execute("SELECT COUNT(*) FROM words;").fetchone()[0]
        
        # Calculate mastery percentage
        mastery_percentage = (total_words_studied / total_vocabulary_in_db) * 100 if total_vocabulary_in_db > 0 else 0.0
        
        return jsonify({
            "total_words_studied": total_words_studied,
            "total_vocabulary_in_db": total_vocabulary_in_db,
            "mastery_percentage": round(mastery_percentage, 2) # Round to 2 decimal places
        })

    @app.route('/api/dashboard/quick-stats', methods=['GET'])
    @cross_origin()
    def get_quick_stats():
        \"\"\"
        Returns quick statistics like overall success rate, total sessions,
        active groups, and current study streak.
        \"\"\"
        cursor = db.cursor()
        
        # Calculate overall success rate
        total_correct_reviews = cursor.execute("SELECT COUNT(*) FROM word_review_items WHERE correct = 1;").fetchone()[0]
        total_reviews = cursor.execute("SELECT COUNT(*) FROM word_review_items;").fetchone()[0]
        success_rate_percentage = (total_correct_reviews / total_reviews) * 100 if total_reviews > 0 else 0.0
        
        # Get total number of study sessions
        total_study_sessions = cursor.execute("SELECT COUNT(*) FROM study_sessions;").fetchone()[0]
        
        # Get number of unique groups that have had study sessions
        total_active_groups = cursor.execute("SELECT COUNT(DISTINCT group_id) FROM study_sessions;").fetchone()[0]

        # Calculate study streak (consecutive days with at least one session)
        study_streak_days = 0
        # Fetch distinct dates of study sessions, ordered descending
        session_dates_raw = cursor.execute("SELECT DISTINCT DATE(created_at) FROM study_sessions ORDER BY created_at DESC;").fetchall()
        # Convert raw dates to datetime.date objects and sort them
        session_dates = sorted([datetime.strptime(d[0], '%Y-%m-%d').date() for d in session_dates_raw], reverse=True)
        
        if session_dates:
            today = datetime.now(timezone.utc).date()
            # Determine the starting point for streak calculation: today or yesterday if today has no sessions
            current_day_for_streak = today
            if session_dates and session_dates[0] == today - timedelta(days=1):
                current_day_for_streak = today - timedelta(days=1)

            for date in session_dates:
                if date == current_day_for_streak:
                    study_streak_days += 1
                    current_day_for_streak -= timedelta(days=1) # Move to the previous day
                elif date < current_day_for_streak:
                    # If there's a gap, the streak is broken
                    break
        
        return jsonify({
            "success_rate_percentage": round(success_rate_percentage, 2),
            "total_study_sessions": total_study_sessions,
            "total_active_groups": total_active_groups,
            "study_streak_days": study_streak_days
        })
""",
    f"{base_dir}/routes/study_activities.py": """
# backend/routes/study_activities.py
from flask import jsonify, request, url_for
from flask_cors import cross_origin
import math
from lib.db import db
from lib.utils import _get_pagination_metadata, _format_datetime

def load(app):
    \"\"\"
    Registers study activity-related API routes with the Flask application.
    \"\"\"

    @app.route('/api/study_activities', methods=['GET'])
    @cross_origin()
    def get_study_activities():
        \"\"\"
        Retrieves a paginated list of all available study activities.
        \"\"\"
        cursor = db.cursor()
        
        # Get pagination parameters from query string
        page = request.args.get('page', 1, type=int)
        per_page = app.config['PER_PAGE'] # Use global PER_PAGE from app config
        offset = (page - 1) * per_page

        # Query to fetch study activities with pagination
        query = "SELECT id, name, thumbnail_url, description, launch_url FROM study_activities LIMIT ? OFFSET ?;"
        activities = cursor.execute(query, (per_page, offset)).fetchall()
        
        # Get total count of study activities for pagination metadata
        total_activities = cursor.execute("SELECT COUNT(*) FROM study_activities;").fetchone()[0]
        
        # Generate pagination metadata
        pagination = _get_pagination_metadata(
            endpoint_name='get_study_activities', 
            total_items=total_activities, 
            current_page=page, 
            per_page=per_page
        )
        
        # Format results
        result = [dict(activity) for activity in activities]
        
        return jsonify({"study_activities": result, "pagination": pagination})

    @app.route('/api/study_activities/<int:activity_id>', methods=['GET'])
    @cross_origin()
    def get_study_activity_by_id(activity_id):
        \"\"\"
        Retrieves details for a specific study activity by its ID.
        \"\"\"
        cursor = db.cursor()
        query = "SELECT id, name, thumbnail_url, description, launch_url FROM study_activities WHERE id = ?;"
        activity = cursor.execute(query, (activity_id,)).fetchone()
        
        if not activity:
            return jsonify({"error": "Study activity not found"}), 404
            
        return jsonify(dict(activity))

    @app.route('/api/study_activities/<int:activity_id>/study_sessions', methods=['GET'])
    @cross_origin()
    def get_study_sessions_for_activity(activity_id):
        \"\"\"
        Retrieves a paginated list of study sessions associated with a specific activity.
        \"\"\"
        cursor = db.cursor()
        
        # First, verify if the activity exists
        cursor.execute('SELECT id FROM study_activities WHERE id = ?', (activity_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Study activity not found'}), 404

        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = app.config['PER_PAGE']
        offset = (page - 1) * per_page

        # Get total count of sessions for this activity for pagination
        total_sessions_query = "SELECT COUNT(*) FROM study_sessions WHERE study_activity_id = ?;"
        total_sessions = cursor.execute(total_sessions_query, (activity_id,)).fetchone()[0]

        # Query to fetch paginated study sessions for the specific activity
        query = \"\"\"
            SELECT ss.id, g.name AS group_name, ss.created_at AS start_time, ss.end_time,
                   COUNT(wri.id) AS number_of_review_items
            FROM study_sessions ss 
            JOIN groups g ON ss.group_id = g.id
            LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
            WHERE ss.study_activity_id = ? 
            GROUP BY ss.id, g.name, ss.created_at, ss.end_time
            ORDER BY ss.created_at DESC 
            LIMIT ? OFFSET ?;
        \"\"\"
        study_sessions = cursor.execute(query, (activity_id, per_page, offset)).fetchall()
        
        # Generate pagination metadata
        pagination = _get_pagination_metadata(
            endpoint_name='get_study_sessions_for_activity', 
            total_items=total_sessions, 
            current_page=page, 
            per_page=per_page,
            activity_id=activity_id # Pass activity_id for correct URL generation
        )
        
        result = []
        for session in study_sessions:
            session_dict = dict(session)
            # Format datetime strings
            session_dict['start_time'] = _format_datetime(session_dict['start_time'])
            session_dict['end_time'] = _format_datetime(session_dict['end_time'])
            session_dict['number_of_review_items'] = int(session_dict['number_of_review_items'] or 0)
            result.append(session_dict)
        
        return jsonify({
            "study_activity_id": activity_id, 
            "study_activity_name": activity['name'], # Get activity name for context
            "study_sessions": result, 
            "pagination": pagination
        })

    @app.route('/api/study_activities', methods=['POST'])
    @cross_origin()
    def create_study_activity_session():
        \"\"\"
        Creates a new study session for a given group and study activity.
        Returns the session ID and a launch URL for the activity.
        \"\"\"
        cursor = db.cursor()
        data = request.get_json()
        
        group_id = data.get('group_id')
        study_activity_id = data.get('study_activity_id')
        
        # Validate required fields
        if not group_id or not study_activity_id:
            return jsonify({"error": "group_id and study_activity_id are required"}), 400
        
        # Verify if group and activity exist
        group = cursor.execute("SELECT 1 FROM groups WHERE id = ?", (group_id,)).fetchone()
        if not group: 
            return jsonify({"error": "Group not found"}), 404
        
        activity = cursor.execute("SELECT launch_url FROM study_activities WHERE id = ?", (study_activity_id,)).fetchone()
        if not activity: 
            return jsonify({"error": "Study activity not found"}), 404
        
        try:
            # Insert a new study session record
            cursor.execute("INSERT INTO study_sessions (group_id, study_activity_id) VALUES (?, ?)", 
                           (group_id, study_activity_id))
            db.commit() # Commit the transaction
            
            session_id = cursor.lastrowid # Get the ID of the newly created session
            
            # Construct the launch URL for the study activity, including the session ID
            launch_url = f"{activity['launch_url']}?session_id={session_id}"
            
            return jsonify({
                "message": "Study activity session launched successfully.",
                "study_session_id": session_id,
                "launch_url": launch_url
            }), 201 # 201 Created status code
        except sqlite3.Error as e:
            db.get().rollback() # Rollback transaction on error
            return jsonify({"error": f"Database error: {str(e)}"}), 500
""",
    f"{base_dir}/routes/words.py": """
# backend/routes/words.py
from flask import request, jsonify, url_for
from flask_cors import cross_origin
import json
from lib.db import db
from lib.utils import _get_pagination_metadata, _format_datetime # Import _format_datetime even if not used here, for consistency

def load(app):
  \"\"\"
  Registers word-related API routes with the Flask application.
  \"\"\"

  @app.route('/api/words', methods=['GET'])
  @cross_origin()
  def get_words():
    \"\"\"
    Retrieves a paginated and sortable list of all words in the database.
    Includes correct/wrong review counts for each word.
    \"\"\"
    cursor = db.cursor()

    # Get pagination parameters from query string (default to page 1, use app's PER_PAGE)
    page = int(request.args.get('page', 1))
    per_page = app.config['PER_PAGE']
    offset = (page - 1) * per_page

    # Get sorting parameters from the query string
    sort_by = request.args.get('sort_by', 'french_word')  # Default sort by French word
    order = request.args.get('order', 'asc').upper()      # Default ascending order

    # Validate sort_by field to prevent SQL injection and ensure valid column names
    valid_sort_fields = ['french_word', 'quebec_pronunciation', 'english', 'correct_count', 'wrong_count']
    if sort_by not in valid_sort_fields:
        return jsonify({"error": f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"}), 400
    
    # Validate order
    if order not in ['ASC', 'DESC']:
        return jsonify({"error": "Invalid order. Must be 'asc' or 'desc'"}), 400

    # Query to fetch words with sorting and pagination
    # Uses LEFT JOIN with word_review_items to get review counts,
    # and GROUP BY to aggregate counts per word.
    query = f\"\"\"
        SELECT w.id, w.french_word, w.quebec_pronunciation, w.english,
               SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END) AS correct_count,
               SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END) AS wrong_count
        FROM words w 
        LEFT JOIN word_review_items wri ON w.id = wri.word_id
        GROUP BY w.id, w.french_word, w.quebec_pronunciation, w.english
        ORDER BY {sort_by} {order} 
        LIMIT ? OFFSET ?;
    \"\"\"
    words = cursor.execute(query, (per_page, offset)).fetchall()

    # Query the total number of words for pagination metadata
    total_words = cursor.execute("SELECT COUNT(*) FROM words;").fetchone()[0]
    
    # Generate pagination metadata
    pagination = _get_pagination_metadata(
        endpoint_name='get_words', 
        total_items=total_words, 
        current_page=page, 
        per_page=per_page,
        sort_by=sort_by, # Pass sorting params for correct next/prev URLs
        order=order
    )

    # Format the response data
    result = []
    for word in words:
        word_dict = dict(word)
        # Ensure counts are integers, defaulting to 0 if NULL
        word_dict['correct_count'] = int(word_dict['correct_count'] or 0)
        word_dict['wrong_count'] = int(word_dict['wrong_count'] or 0)
        result.append(word_dict)

    return jsonify({"words": result, "pagination": pagination})

  @app.route('/api/words/<int:word_id>', methods=['GET'])
  @cross_origin()
  def get_word_by_id(word_id):
    \"\"\"
    Retrieves detailed information for a single word by its ID.
    Includes its parts (JSON parsed), study statistics, and associated groups.
    \"\"\"
    cursor = db.cursor()
    
    # Query to fetch the word details and aggregate review counts
    word_query = \"\"\"
        SELECT w.id, w.french_word, w.quebec_pronunciation, w.english, w.parts,
               SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END) AS correct_count,
               SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END) AS wrong_count
        FROM words w 
        LEFT JOIN word_review_items wri ON w.id = wri.word_id
        WHERE w.id = ? 
        GROUP BY w.id, w.french_word, w.quebec_pronunciation, w.english, w.parts;
    \"\"\"
    word = cursor.execute(word_query, (word_id,)).fetchone()
    
    if not word:
        return jsonify({"error": "Word not found"}), 404
    
    word_dict = dict(word)
    # Parse the 'parts' JSON string back into a Python object
    word_dict['parts'] = json.loads(word_dict['parts'])
    
    # Structure study statistics under a dedicated key
    word_dict['study_statistics'] = {
        "correct_count": int(word_dict['correct_count'] or 0),
        "wrong_count": int(word_dict['wrong_count'] or 0)
    }
    # Remove the raw correct_count and wrong_count from the top level
    del word_dict['correct_count']
    del word_dict['wrong_count']

    # Query to fetch all groups associated with this word
    groups_query = \"\"\"
        SELECT g.id, g.name 
        FROM groups g 
        JOIN words_groups wg ON g.id = wg.group_id 
        WHERE wg.word_id = ?;
    \"\"\"
    word_groups = cursor.execute(groups_query, (word_id,)).fetchall()
    word_dict['word_groups'] = [dict(g) for g in word_groups]
    
    return jsonify(word_dict)
""",
    f"{base_dir}/routes/groups.py": """
# backend/routes/groups.py
from flask import request, jsonify, url_for
from flask_cors import cross_origin
import json
from lib.db import db
from lib.utils import _get_pagination_metadata, _format_datetime

def load(app):
  \"\"\"
  Registers group-related API routes with the Flask application.
  \"\"\"

  @app.route('/api/groups', methods=['GET'])
  @cross_origin()
  def get_groups():
    \"\"\"
    Retrieves a paginated and sortable list of all word groups.
    Includes the cached word count for each group.
    \"\"\"
    cursor = db.cursor()

    # Get pagination parameters
    page = int(request.args.get('page', 1))
    per_page = app.config['PER_PAGE']
    offset = (page - 1) * per_page

    # Get sorting parameters
    sort_by = request.args.get('sort_by', 'name')  # Default to sorting by 'name'
    order = request.args.get('order', 'asc').upper()  # Default to ascending order

    # Validate sort_by and order
    valid_sort_fields = ['name', 'word_count']
    if sort_by not in valid_sort_fields:
      return jsonify({"error": f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"}), 400
    if order not in ['ASC', 'DESC']:
      return jsonify({"error": "Invalid order. Must be 'asc' or 'desc'"}), 400

    # Query to fetch groups with sorting and the cached word count
    query = f'''
      SELECT id, name, word_count FROM groups
      ORDER BY {sort_by} {order}
      LIMIT ? OFFSET ?;
    '''
    groups = cursor.execute(query, (per_page, offset)).fetchall()

    # Query the total number of groups for pagination metadata
    total_groups = cursor.execute('SELECT COUNT(*) FROM groups;').fetchone()[0]
    
    # Generate pagination metadata
    pagination = _get_pagination_metadata(
        endpoint_name='get_groups', 
        total_items=total_groups, 
        current_page=page, 
        per_page=per_page,
        sort_by=sort_by, 
        order=order
    )

    # Format the response
    result = [dict(group) for group in groups]

    return jsonify({"groups": result, "pagination": pagination})

  @app.route('/api/groups/<int:group_id>', methods=['GET'])
  @cross_origin()
  def get_group_by_id(group_id):
    \"\"\"
    Retrieves details for a specific group by its ID.
    \"\"\"
    cursor = db.cursor()

    # Get group details
    group = cursor.execute('''
      SELECT id, name, word_count AS total_word_count
      FROM groups
      WHERE id = ?;
    ''', (group_id,)).fetchone()
    
    if not group:
      return jsonify({"error": "Group not found"}), 404

    return jsonify(dict(group))

  @app.route('/api/groups/<int:group_id>/words', methods=['GET'])
  @cross_origin()
  def get_words_from_group(group_id):
    \"\"\"
    Retrieves a paginated and sortable list of words belonging to a specific group.
    Includes review counts for each word.
    \"\"\"
    cursor = db.cursor()
    
    # First, check if the group exists
    group = cursor.execute("SELECT id, name FROM groups WHERE id = ?", (group_id,)).fetchone()
    if not group:
      return jsonify({"error": "Group not found"}), 404

    # Get pagination parameters
    page = int(request.args.get('page', 1))
    per_page = app.config['PER_PAGE']
    offset = (page - 1) * per_page

    # Get sorting parameters
    sort_by = request.args.get('sort_by', 'french_word')
    order = request.args.get('order', 'asc').upper()

    # Validate sort parameters
    valid_sort_fields = ['french_word', 'quebec_pronunciation', 'english', 'correct_count', 'wrong_count']
    if sort_by not in valid_sort_fields:
      return jsonify({"error": f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"}), 400
    if order not in ['ASC', 'DESC']:
      return jsonify({"error": "Invalid order. Must be 'asc' or 'desc'"}), 400

    # Query to fetch words from the group with pagination and sorting
    query = f'''
      SELECT w.id, w.french_word, w.quebec_pronunciation, w.english,
             SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END) AS correct_count,
             SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END) AS wrong_count
      FROM words w
      JOIN words_groups wg ON w.id = wg.word_id
      LEFT JOIN word_review_items wri ON w.id = wri.word_id
      WHERE wg.group_id = ?
      GROUP BY w.id, w.french_word, w.quebec_pronunciation, w.english
      ORDER BY {sort_by} {order}
      LIMIT ? OFFSET ?;
    '''
    words = cursor.execute(query, (group_id, per_page, offset)).fetchall()

    # Get total words count for pagination from the cached count in the groups table
    total_words_in_group = cursor.execute("SELECT word_count FROM groups WHERE id = ?;", (group_id,)).fetchone()[0]
    
    # Generate pagination metadata
    pagination = _get_pagination_metadata(
        endpoint_name='get_words_from_group', 
        total_items=total_words_in_group, 
        current_page=page, 
        per_page=per_page,
        group_id=group_id, # Pass group_id for correct URL generation
        sort_by=sort_by, 
        order=order
    )

    # Format the response
    result = []
    for word in words:
      word_dict = dict(word)
      word_dict['correct_count'] = int(word_dict['correct_count'] or 0)
      word_dict['wrong_count'] = int(word_dict['wrong_count'] or 0)
      result.append(word_dict)

    return jsonify({
      "group_id": group_id, 
      "group_name": group['name'], # Include group name for context
      "words": result, 
      "pagination": pagination
    })

  @app.route('/api/groups/<int:group_id>/study_sessions', methods=['GET'])
  @cross_origin()
  def get_study_sessions_for_group(group_id):
    \"\"\"
    Retrieves a paginated list of study sessions associated with a specific group.
    \"\"\"
    cursor = db.cursor()
    
    # First, check if the group exists
    group = cursor.execute("SELECT id, name FROM groups WHERE id = ?", (group_id,)).fetchone()
    if not group:
      return jsonify({"error": "Group not found"}), 404

    # Get pagination parameters
    page = int(request.args.get('page', 1))
    per_page = app.config['PER_PAGE']
    offset = (page - 1) * per_page

    # Get total count of sessions for this group
    total_sessions_query = "SELECT COUNT(*) FROM study_sessions WHERE group_id = ?;"
    total_sessions = cursor.execute(total_sessions_query, (group_id,)).fetchone()[0]

    # Query to fetch paginated study sessions for the specific group
    query = \"\"\"
        SELECT ss.id, sa.name AS activity_name, g.name AS group_name,
               ss.created_at AS start_time, ss.end_time,
               COUNT(wri.id) AS number_of_review_items
        FROM study_sessions ss 
        JOIN study_activities sa ON ss.study_activity_id = sa.id
        JOIN groups g ON ss.group_id = g.id 
        LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
        WHERE ss.group_id = ? 
        GROUP BY ss.id, sa.name, g.name, ss.created_at, ss.end_time
        ORDER BY ss.created_at DESC 
        LIMIT ? OFFSET ?;
    \"\"\"
    study_sessions = cursor.execute(query, (group_id, per_page, offset)).fetchall()
    
    # Generate pagination metadata
    pagination = _get_pagination_metadata(
        endpoint_name='get_study_sessions_for_group', 
        total_items=total_sessions, 
        current_page=page, 
        per_page=per_page,
        group_id=group_id, # Pass group_id for correct URL generation
        sort_by=sort_by, 
        order=order
    )

    # Format the response
    result = []
    for session in study_sessions:
        session_dict = dict(session)
        # Format datetime strings
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
""",
    f"{base_dir}/routes/study_sessions.py": """
# backend/routes/study_sessions.py
from flask import request, jsonify, url_for
from flask_cors import cross_origin
from datetime import datetime, timedelta, timezone
import math
from lib.db import db
from lib.utils import _get_pagination_metadata, _format_datetime

def load(app):
  \"\"\"
  Registers study session-related API routes with the Flask application.
  \"\"\"

  @app.route('/api/study_sessions', methods=['GET'])
  @cross_origin()
  def get_all_study_sessions():
    \"\"\"
    Retrieves a paginated list of all study sessions.
    Includes associated activity and group names, and review item count.
    \"\"\"
    cursor = db.cursor()
    
    # Get pagination parameters
    page = int(request.args.get('page', 1))
    per_page = app.config['PER_PAGE']
    offset = (page - 1) * per_page

    # Get total count of all study sessions for pagination
    total_sessions = cursor.execute("SELECT COUNT(*) FROM study_sessions;").fetchone()[0]

    # Query to fetch paginated study sessions with joined data
    query = \"\"\"
        SELECT ss.id, sa.name AS activity_name, g.name AS group_name,
               ss.created_at AS start_time, ss.end_time,
               COUNT(wri.id) AS number_of_review_items
        FROM study_sessions ss 
        JOIN study_activities sa ON ss.study_activity_id = sa.id
        JOIN groups g ON ss.group_id = g.id 
        LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
        GROUP BY ss.id, sa.name, g.name, ss.created_at, ss.end_time
        ORDER BY ss.created_at DESC 
        LIMIT ? OFFSET ?;
    \"\"\"
    study_sessions = cursor.execute(query, (per_page, offset)).fetchall()
    
    # Generate pagination metadata
    pagination = _get_pagination_metadata(
        endpoint_name='get_all_study_sessions', 
        total_items=total_sessions, 
        current_page=page, 
        per_page=per_page
    )
    
    result = []
    for session in study_sessions:
        session_dict = dict(session)
        # Format datetime strings
        session_dict['start_time'] = _format_datetime(session_dict['start_time'])
        session_dict['end_time'] = _format_datetime(session_dict['end_time'])
        session_dict['number_of_review_items'] = int(session_dict['number_of_review_items'] or 0)
        result.append(session_dict)
    
    return jsonify({
        "study_sessions": result, 
        "pagination": pagination
    })

  @app.route('/api/study_sessions/<int:session_id>', methods=['GET'])
  @cross_origin()
  def get_study_session_by_id(session_id):
    \"\"\"
    Retrieves detailed information for a single study session by its ID.
    \"\"\"
    cursor = db.cursor()
    query = \"\"\"
        SELECT ss.id, sa.name AS activity_name, g.name AS group_name,
               ss.created_at AS start_time, ss.end_time,
               COUNT(wri.id) AS number_of_review_items
        FROM study_sessions ss 
        JOIN study_activities sa ON ss.study_activity_id = sa.id
        JOIN groups g ON ss.group_id = g.id 
        LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
        WHERE ss.id = ? 
        GROUP BY ss.id, sa.name, g.name, ss.created_at, ss.end_time;
    \"\"\"
    session = cursor.execute(query, (session_id,)).fetchone()
    
    if not session:
        return jsonify({"error": "Study session not found"}), 404
    
    session_dict = dict(session)
    # Format datetime strings
    session_dict['start_time'] = _format_datetime(session_dict['start_time'])
    session_dict['end_time'] = _format_datetime(session_dict['end_time'])
    session_dict['number_of_review_items'] = int(session_dict['number_of_review_items'] or 0)
    
    return jsonify(session_dict)

  @app.route('/api/study_sessions/<int:session_id>/words', methods=['GET'])
  @cross_origin()
  def get_words_from_study_session(session_id):
    \"\"\"
    Retrieves all word review items for a specific study session.
    Includes word details and whether the review was correct.
    \"\"\"
    cursor = db.cursor()
    
    # Verify if the study session exists and get its group name
    session_info = cursor.execute(
        "SELECT ss.id, g.name AS group_name FROM study_sessions ss JOIN groups g ON ss.group_id = g.id WHERE ss.id = ?",
        (session_id,)
    ).fetchone()
    if not session_info:
        return jsonify({"error": "Study session not found"}), 404
    
    # Query to fetch all word review items for the given session
    query = \"\"\"
        SELECT w.id AS word_id, w.french_word, w.quebec_pronunciation, w.english,
               wri.correct, wri.created_at
        FROM word_review_items wri 
        JOIN words w ON wri.word_id = w.id
        WHERE wri.study_session_id = ? 
        ORDER BY wri.created_at ASC;
    \"\"\"
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
  @cross_origin()
  def log_word_review_attempt(session_id, word_id):
    \"\"\"
    Logs a review attempt for a specific word within a study session.
    Updates the session's end_time.
    \"\"\"
    cursor = db.cursor()
    data = request.get_json()
    
    correct = data.get('correct')
    
    # Validate 'correct' field
    if correct is None: 
        return jsonify({"error": "Correct status is required"}), 400
    if not isinstance(correct, bool): 
        return jsonify({"error": "Correct status must be a boolean (true/false)"}), 400
    
    # Verify session and word existence
    session_exists = cursor.execute("SELECT 1 FROM study_sessions WHERE id = ?", (session_id,)).fetchone()
    if not session_exists: 
        return jsonify({"error": "Study session not found"}), 404
    
    word_exists = cursor.execute("SELECT 1 FROM words WHERE id = ?", (word_id,)).fetchone()
    if not word_exists: 
        return jsonify({"error": "Word not found"}), 404
    
    try:
        current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f') # Include microseconds
        
        # Insert the review item
        cursor.execute("INSERT INTO word_review_items (word_id, study_session_id, correct, created_at) VALUES (?, ?, ?, ?)",
                       (word_id, session_id, 1 if correct else 0, current_time))
        db.commit() # Commit the insertion
        
        review_id = cursor.lastrowid # Get the ID of the new review item
        
        # Update the study session's end_time to the current time
        cursor.execute("UPDATE study_sessions SET end_time = ? WHERE id = ?", (current_time, session_id))
        db.commit() # Commit the session update
        
        return jsonify({
            "message": "Word review recorded successfully.", 
            "review_item_id": review_id,
            "word_id": word_id, 
            "study_session_id": session_id, 
            "correct": correct,
            "created_at": _format_datetime(current_time)
        }), 201 # 201 Created status code
    except sqlite3.Error as e:
        db.get().rollback() # Rollback transaction on error
        return jsonify({"error": f"Database error: {str(e)}"}), 500

  @app.route('/api/reset_history', methods=['POST'])
  @cross_origin()
  def reset_history():
    \"\"\"
    Resets all study history by deleting all word review items and study sessions.
    \"\"\"
    cursor = db.cursor()
    try:
        # Delete review items first due to foreign key constraints
        cursor.execute("DELETE FROM word_review_items;")
        # Then delete study sessions
        cursor.execute("DELETE FROM study_sessions;")
        db.commit() # Commit the deletions
        return jsonify({"message": "Study history cleared successfully."}), 200
    except sqlite3.Error as e:
        db.get().rollback() # Rollback on error
        return jsonify({"error": f"Database error: {str(e)}"}), 500

  @app.route('/api/full_reset', methods=['POST'])
  @cross_origin()
  def full_reset():
    \"\"\"
    Performs a full system reset: deletes all data and reinitializes the database
    with seed data.
    \"\"\"
    try:
        db.init_db_and_seed_data(app) # Call the init_db_and_seed_data method from Db class
        return jsonify({"message": "Full system reset completed successfully. Database reinitialized with seed data."}), 200
    except Exception as e:
        return jsonify({"error": f"Full reset failed: {str(e)}"}), 500
""",
    f"{base_dir}/sql/setup/create_table_words.sql": """
CREATE TABLE IF NOT EXISTS words (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  french_word TEXT NOT NULL,
  quebec_pronunciation TEXT NOT NULL,
  english TEXT NOT NULL,
  parts TEXT NOT NULL  -- Store parts as JSON string
);
""",
    f"{base_dir}/sql/setup/create_table_groups.sql": """
CREATE TABLE IF NOT EXISTS groups (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  word_count INTEGER DEFAULT 0  -- Counter cache for the number of words in the group
);
""",
    f"{base_dir}/sql/setup/create_table_words_groups.sql": """
CREATE TABLE IF NOT EXISTS words_groups (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  word_id INTEGER NOT NULL,
  group_id INTEGER NOT NULL,
  FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE,
  FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
);
""",
    f"{base_dir}/sql/setup/create_table_study_activities.sql": """
CREATE TABLE IF NOT EXISTS study_activities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  thumbnail_url TEXT,
  description TEXT,
  launch_url TEXT NOT NULL
);
""",
    f"{base_dir}/sql/setup/create_table_study_sessions.sql": """
CREATE TABLE IF NOT EXISTS study_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  group_id INTEGER NOT NULL,
  study_activity_id INTEGER NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  end_time DATETIME, -- Nullable, can be updated later
  FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
  FOREIGN KEY (study_activity_id) REFERENCES study_activities(id) ON DELETE CASCADE
);
""",
    f"{base_dir}/sql/setup/create_table_word_review_items.sql": """
CREATE TABLE IF NOT EXISTS word_review_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  word_id INTEGER NOT NULL,
  study_session_id INTEGER NOT NULL,
  correct BOOLEAN NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE,
  FOREIGN KEY (study_session_id) REFERENCES study_sessions(id) ON DELETE CASCADE
);
""",
    f"{base_dir}/seed/data_greetings.json": """
[
  {"french_word": "Bonjour", "quebec_pronunciation": "bon-zhoor", "english": "Hello", "parts": {"notes": "Common greeting"}},
  {"french_word": "Bonsoir", "quebec_pronunciation": "bon-swar", "english": "Good evening", "parts": {"notes": "Evening greeting"}},
  {"french_word": "Bonne nuit", "quebec_pronunciation": "bon-nwee", "english": "Good night", "parts": {"notes": "Before sleeping"}},
  {"french_word": "Salut", "quebec_pronunciation": "sa-lyoo", "english": "Hi/Bye (informal)", "parts": {"notes": "Informal greeting/farewell"}},
  {"french_word": "Au revoir", "quebec_pronunciation": "oh ruh-vwahr", "english": "Goodbye", "parts": {"notes": "Common farewell"}}
]
""",
    f"{base_dir}/seed/data_common_phrases.json": """
[
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
""",
    f"{base_dir}/seed/data_quebecois_slang.json": """
[
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
""",
    f"{base_dir}/seed/data_quebecois_culture.json": """
[
  {"french_word": "Poutine", "quebec_pronunciation": "poo-teen", "english": "Poutine (dish)", "parts": {"notes": "Iconic Quebecois dish of fries, cheese curds, and gravy."}},
  {"french_word": "Cabane à sucre", "quebec_pronunciation": "ka-ban-a-syookr", "english": "Sugar shack", "parts": {"notes": "Place where maple syrup is produced and celebrated."}},
  {"french_word": "La p'tite bière", "quebec_pronunciation": "la-peet-byair", "english": "A little beer", "parts": {"notes": "Common informal term for a beer."}},
  {"french_word": "Blé d'Inde", "quebec_pronunciation": "blay daind", "english": "Corn", "parts": {"notes": "Quebecois specific term, standard French uses 'maïs'."}},
  {"french_word": "Tuque", "quebec_pronunciation": "tyook", "english": "Beanie/winter hat", "parts": {"gender": "feminine", "notes": "A common type of winter hat."}}
]
""",
    f"{base_dir}/seed/data_everyday_objects.json": """
[
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
""",
    f"{base_dir}/seed/data_everyday_adjectives.json": """
[
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
""",
    f"{base_dir}/seed/study_activities.json": """
[
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
""",
    f"{base_dir}/requirements.txt": """
flask
flask-cors
pyngrok
"""
}

# Create directories
print(f"Creating base directory: {base_dir}")
os.makedirs(f"{base_dir}/lib", exist_ok=True)
os.makedirs(f"{base_dir}/routes", exist_ok=True)
os.makedirs(f"{base_dir}/sql/setup", exist_ok=True)
os.makedirs(f"{base_dir}/seed", exist_ok=True)

# Create __init__.py files for packages
open(f"{base_dir}/__init__.py", "a").close()
open(f"{base_dir}/lib/__init__.py", "a").close()
open(f"{base_dir}/routes/__init__.py", "a").close()
open(f"{base_dir}/sql/__init__.py", "a").close() # For sql directory itself

# Write files
for file_path, content in file_structure.items():
    print(f"Writing file: {file_path}")
    with open(file_path, "w") as f:
        f.write(content)

# Install required packages using requirements.txt
print("\nInstalling required Python packages from requirements.txt...")
os.system(f"pip install -r {base_dir}/requirements.txt")

print("\nAll backend files and directories created successfully!")
print(f"\nTo run the Flask app, navigate to the '{base_dir}' directory and execute 'python app.py':")
print(f"cd {base_dir}")
print("python app.py")