
# backend/routes/words.py
from flask import request, jsonify, url_for
from flask_cors import cross_origin
import json
from lib.db import db
from lib.utils import _get_pagination_metadata, _format_datetime # Import _format_datetime even if not used here, for consistency

def load(app):
  """
  Registers word-related API routes with the Flask application.
  """

  @app.route('/api/words', methods=['GET'])
  @cross_origin()
  def get_words():
    """
    Retrieves a paginated and sortable list of all words in the database.
    Includes correct/wrong review counts for each word.
    """
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
    query = f"""
        SELECT w.id, w.french_word, w.quebec_pronunciation, w.english,
               SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END) AS correct_count,
               SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END) AS wrong_count
        FROM words w 
        LEFT JOIN word_review_items wri ON w.id = wri.word_id
        GROUP BY w.id, w.french_word, w.quebec_pronunciation, w.english
        ORDER BY {sort_by} {order} 
        LIMIT ? OFFSET ?;
    """
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
    """
    Retrieves detailed information for a single word by its ID.
    Includes its parts (JSON parsed), study statistics, and associated groups.
    """
    cursor = db.cursor()
    
    # Query to fetch the word details and aggregate review counts
    word_query = """
        SELECT w.id, w.french_word, w.quebec_pronunciation, w.english, w.parts,
               SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END) AS correct_count,
               SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END) AS wrong_count
        FROM words w 
        LEFT JOIN word_review_items wri ON w.id = wri.word_id
        WHERE w.id = ? 
        GROUP BY w.id, w.french_word, w.quebec_pronunciation, w.english, w.parts;
    """
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
    groups_query = """
        SELECT g.id, g.name 
        FROM groups g 
        JOIN words_groups wg ON g.id = wg.group_id 
        WHERE wg.word_id = ?;
    """
    word_groups = cursor.execute(groups_query, (word_id,)).fetchall()
    word_dict['word_groups'] = [dict(g) for g in word_groups]
    
    return jsonify(word_dict)
