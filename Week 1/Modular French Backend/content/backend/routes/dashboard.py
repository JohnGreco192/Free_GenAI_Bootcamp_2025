
# backend/routes/dashboard.py
from flask import jsonify, request
from flask_cors import cross_origin
from datetime import datetime, timedelta, timezone
from lib.db import db
from lib.utils import _format_datetime

def load(app):
    """
    Registers dashboard-related API routes with the Flask application.
    """

    @app.route('/api/dashboard/last_study_session', methods=['GET'])
    @cross_origin()
    def get_last_study_session():
        """
        Retrieves details of the most recent study session.
        Includes group name, start/end times, and review counts.
        """
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
        """
        Provides overall study progress statistics, including total words studied
        and mastery percentage.
        """
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
        """
        Returns quick statistics like overall success rate, total sessions,
        active groups, and current study streak.
        """
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
