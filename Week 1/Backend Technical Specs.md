# Backend Server Technical specs



## Busines goal:
A language learning school wants to build porottype of learning portal which will act as three things:
- Inventory of possible vocabulary that can be leanred
- Act as learning record store, providing correct and wrong score on practice vocabulary
- A unified Launchpad to launch different learning apps

## TEchnical Reqs
- The backend will e built using Go?
- The database will be SQLlite 3
- The API will be built using GIN
- The API will always return JSON
- There will be no authenication or authroization. Everything will be treated as single user

## Database Schema

We have the following Tables:
- Words - stored vocabulary words
    - id integer
    - French Word string
    - Quebec Pronunciation string
    - English string
    - Parts json
- words_groups - join table for words and groups many-to-many
    - id integer
    - word_id integer
    - group_id integer
- groups - thematic group of words
    - id integer
    - name integer
- study sessions - records of study sessions grouping word_review_items
    - id integer
    - group_id integer
    - created_at datetime
    - study_activity_id integer
- study_activities - a specific study activity, linking study session to group
    - id integeer
    - study_session_id integer
    - group_id integer
    - created_at datetime
- word_review_items - a record of word practice, determining if the wor was correct or not
    - word_id integer
    - study_session_ID integer
    - correct boolean
    - created_at datetime

    ### API Endpoints
     - GET /dashboard/last_study_session
     - GET /dashboard/study_progress
     - GET /dashboard/quick-stats

     - GET /words
     - GET /words/:id
     - GET /groups
     - GET /groups/:id
     - GET /groups/:id//words
