
# backend/routes/study_activities.py
from flask import jsonify, request, url_for
from flask_cors import cross_origin
import math
from lib.db import db
from lib.utils import _get_pagination_metadata, _format_datetime

def load(app):
    """
    Registers study activity-related API routes with the Flask application.
    """

    @app.route('/api/study_activities', methods=['GET'])
    @cross_origin()
    def get_study_activities():
        """
        Retrieves a paginated list of all available study activities.
        """
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
        """
        Retrieves details for a specific study activity by its ID.
        """
        cursor = db.cursor()
        query = "SELECT id, name, thumbnail_url, description, launch_url FROM study_activities WHERE id = ?;"
        activity = cursor.execute(query, (activity_id,)).fetchone()
        
        if not activity:
            return jsonify({"error": "Study activity not found"}), 404
            
        return jsonify(dict(activity))

    @app.route('/api/study_activities/<int:activity_id>/study_sessions', methods=['GET'])
    @cross_origin()
    def get_study_sessions_for_activity(activity_id):
        """
        Retrieves a paginated list of study sessions associated with a specific activity.
        """
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
        query = """
            SELECT ss.id, g.name AS group_name, ss.created_at AS start_time, ss.end_time,
                   COUNT(wri.id) AS number_of_review_items
            FROM study_sessions ss 
            JOIN groups g ON ss.group_id = g.id
            LEFT JOIN word_review_items wri ON ss.id = wri.study_session_id
            WHERE ss.study_activity_id = ? 
            GROUP BY ss.id, g.name, ss.created_at, ss.end_time
            ORDER BY ss.created_at DESC 
            LIMIT ? OFFSET ?;
        """
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
        """
        Creates a new study session for a given group and study activity.
        Returns the session ID and a launch URL for the activity.
        """
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
