
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
NGROK_AUTH_TOKEN_HARDCODED = "..."

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
    """
    Creates and configures the Flask application.
    """
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
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",  # Allows all origins for development. Restrict in production.
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # --- API Routes ---
    # Root API endpoint
    @app.route('/api')
    def api_root():
        return jsonify({"message": "Welcome to the Quebec French Language Portal API!"})

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
        print(f"FATAL ERROR: Could not set ngrok authtoken with the hardcoded token: {e}")
        print("Please ensure your hardcoded NGROK_AUTH_TOKEN is valid. Exiting.")
        exit()

    # Establish ngrok tunnel and run Flask app
    public_url = ngrok.connect(5000)
    print(f" * Tunnel URL: {public_url}")
    print(" * Serving Flask app '__main__'")
    print(" * Debug mode: off")
    print(" * Running on http://127.0.0.1:5000")
    print("INFO:werkzeug:Press CTRL+C to quit")

    # Run the Flask application
    app.run(debug=False, port=5000, use_reloader=False)
