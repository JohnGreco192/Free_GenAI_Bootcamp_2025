# Final Week 1 version

## Modularized Backend, Built from Monolithic Script

This backend is part of the Free GenAI Bootcamp 2025 project. It provides a modularized API for a Quebec French language learning portal, supporting vocabulary, study activities, groups, and study sessions.

### Features

- RESTful API built with Flask
- Modular route structure (`dashboard`, `study_activities`, `words`, `groups`, `study_sessions`)
- SQLite database with automatic initialization and sample data seeding
- CORS enabled for frontend integration
- Designed for Codespaces development (runs on port 5000, no ngrok required)

### Project Structure

```
Week 1/Modular French Backend/
│
├── app.py                # Main Flask application entry point
├── requirements.txt      # Python dependencies
├── lang_portal.db        # SQLite database (auto-created)
├── lib/
│   ├── db.py             # Database connection and seeding logic
│   └── utils.py          # Utility functions
├── routes/
│   ├── dashboard.py      # Dashboard-related API routes
│   ├── study_activities.py # Study activities API routes
│   ├── words.py          # Vocabulary API routes
│   ├── groups.py         # Groups API routes
│   └── study_sessions.py # Study sessions API routes
└── Readme.md             # This documentation
```

### How to Run (in Codespaces or locally)

1. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

2. **Start the backend:**
   ```sh
   python app.py
   ```

3. **Access the API:**
   - In Codespaces, open the forwarded port (5000).
   - Visit:  
     [https://upgraded-parakeet-gp6p5pgjq7pfx99-5000.app.github.dev/api](https://upgraded-parakeet-gp6p5pgjq7pfx99-5000.app.github.dev/api)  
     or  
     `http://localhost:5000/api` (if running locally)

   - You should see:  
     `{"message": "Welcome to the Quebec French Language Portal API!"}`

### API Endpoints

- `/api` — Welcome message
- `/api/words` — Vocabulary endpoints
- `/api/groups` — Group endpoints
- `/api/study_activities` — Study activities endpoints
- `/api/study_sessions` — Study session endpoints
- `/api/dashboard` — Dashboard endpoints

*(See route modules for full details.)*

---

**This backend is designed to work with the Modular French Frontend.  
For full-stack integration, update the frontend API URL to match your Codespaces backend URL.**