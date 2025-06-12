
CREATE TABLE IF NOT EXISTS study_activities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  thumbnail_url TEXT,
  description TEXT,
  launch_url TEXT NOT NULL
);
