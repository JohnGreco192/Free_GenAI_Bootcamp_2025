
# backend/lib/db.py
import sqlite3
import json
import os
from flask import g # Flask's 'g' object for request-specific global variables

class Db:
  """
  Database helper class for managing SQLite connections and operations.
  Uses Flask's `g` object to ensure a single database connection per request.
  """
  def __init__(self, database='lang_portal.db'):
    """
    Initializes the Db instance with the database file path.
    """
    self.database = database
    self.connection = None # Connection will be managed by Flask's g

  def get(self):
    """
    Gets the database connection for the current request context.
    If a connection doesn't exist in `g`, it creates one.
    """
    if 'db' not in g:
      g.db = sqlite3.connect(self.database)
      g.db.row_factory = sqlite3.Row  # Return rows as dictionary-like objects
    return g.db

  def commit(self):
    """
    Commits any pending transactions to the database.
    """
    self.get().commit()

  def cursor(self):
    """
    Returns a database cursor.
    """
    return self.get().cursor()

  def close(self):
    """
    Closes the database connection for the current request context.
    Called automatically by Flask's teardown_appcontext.
    """
    db_conn = g.pop('db', None)
    if db_conn is not None:
      db_conn.close()

  def sql(self, filepath):
    """
    Reads and returns the content of an SQL file.
    Assumes SQL files are in the 'sql/' directory relative to the project root.
    """
    # Construct the absolute path to the SQL file
    # Assuming 'backend' is the root, and 'lib' is inside 'backend'
    current_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(current_dir, '..')) # Go up one level from 'lib'
    sql_file_path = os.path.join(project_root, 'sql', filepath)
    
    with open(sql_file_path, 'r') as file:
      return file.read()

  def load_json(self, filepath):
    """
    Reads and returns the content of a JSON file.
    Assumes JSON files are in the 'seed/' directory relative to the project root.
    """
    # Construct the absolute path to the JSON file
    current_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(current_dir, '..')) # Go up one level from 'lib'
    json_file_path = os.path.join(project_root, 'seed', filepath)

    with open(json_file_path, 'r', encoding='utf-8') as file:
      return json.load(file)

  def setup_tables(self, cursor):
    """
    Executes all table creation SQL scripts.
    """
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
    """
    Imports words from a JSON file and links them to a group.
    """
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
    """
    Imports study activities from a JSON file.
    """
    activities_list = self.load_json(data_json_path)
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
