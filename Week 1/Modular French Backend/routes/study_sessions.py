
# backend/routes/study_sessions.py
from flask import request, jsonify, url_for
from flask_cors import cross_origin
from datetime import datetime, timedelta, timezone
import math
from lib.db import db
from lib.utils import _get_pagination_metadata, _format_datetime

def load(app):
  """
  Registers study session-related API routes with the Flask application.
  """

  @app.route('/api/study_sessions', methods=['GET'])
  @cross_origin()
  def get_all_study_sessions():
    """
    Retrieves a paginated list of all study sessions.
    Includes associated activity and group names, and review item count.
    """
    cursor = db.cursor()
    
    # Get pagination parameters
    page = int(request.args.get('page', 1))
    per_page = app.config['PER_PAGE']
    offset = (page - 1) * per_page

    # Get total count of all study sessions for pagination
    total_sessions = cursor.execute("SELECT COUNT(*) FROM study_sessions;").fetchone()[0]

    # Query to fetch paginated study sessions with joined data
    query = """
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
    """
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
    """
    Retrieves detailed information for a single study session by its ID.
    """
    cursor = db.cursor()
    query = """
        SELECT ss.id, sa.name AS activity_name, g.name AS group_name,
               ss.created_at AS start_time, ss.end_time,
               COUNT(wri.id) AS number_of_review_items
        FROM study_sessions ss 
        JOIN study_activities sa ON ss.study_activity_id = sa.id
        JOIN groups g ON ss.group_id = g.id 
        LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
        WHERE ss.id = ? 
        GROUP BY ss.id, sa.name, g.name, ss.created_at, ss.end_time;
    """
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
    """
    Retrieves all word review items for a specific study session.
    Includes word details and whether the review was correct.
    """
    cursor = db.cursor()
    
    # Verify if the study session exists and get its group name
    session_info = cursor.execute(
        "SELECT ss.id, g.name AS group_name FROM study_sessions ss JOIN groups g ON ss.group_id = g.id WHERE ss.id = ?",
        (session_id,)
    ).fetchone()
    if not session_info:
        return jsonify({"error": "Study session not found"}), 404
    
    # Query to fetch all word review items for the given session
    query = """
        SELECT w.id AS word_id, w.french_word, w.quebec_pronunciation, w.english,
               wri.correct, wri.created_at
        FROM word_review_items wri 
        JOIN words w ON wri.word_id = w.id
        WHERE wri.study_session_id = ? 
        ORDER BY wri.created_at ASC;
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
  @cross_origin()
  def log_word_review_attempt(session_id, word_id):
    """
    Logs a review attempt for a specific word within a study session.
    Updates the session's end_time.
    """
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
    """
    Resets all study history by deleting all word review items and study sessions.
    """
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
    """
    Performs a full system reset: deletes all data and reinitializes the database
    with seed data.
    """
    try:
        db.init_db_and_seed_data(app) # Call the init_db_and_seed_data method from Db class
        return jsonify({"message": "Full system reset completed successfully. Database reinitialized with seed data."}), 200
    except Exception as e:
        return jsonify({"error": f"Full reset failed: {str(e)}"}), 500
