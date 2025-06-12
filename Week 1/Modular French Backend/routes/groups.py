
# backend/routes/groups.py
from flask import request, jsonify, url_for
from flask_cors import cross_origin
import json
from lib.db import db
from lib.utils import _get_pagination_metadata, _format_datetime

def load(app):
  """
  Registers group-related API routes with the Flask application.
  """

  @app.route('/api/groups', methods=['GET'])
  @cross_origin()
  def get_groups():
    """
    Retrieves a paginated and sortable list of all word groups.
    Includes the cached word count for each group.
    """
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
    """
    Retrieves details for a specific group by its ID.
    """
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
    """
    Retrieves a paginated and sortable list of words belonging to a specific group.
    Includes review counts for each word.
    """
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
    """
    Retrieves a paginated list of study sessions associated with a specific group.
    """
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
    query = """
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
    """
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
