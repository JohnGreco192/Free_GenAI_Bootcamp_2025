# Backend Server Technical specs



## Busines goal:
A language learning school wants to build porottype of learning portal which will act as three things:
- Inventory of possible vocabulary that can be leanred
- Act as learning record store, providing correct and wrong score on practice vocabulary
- A unified Launchpad to launch different learning apps

## TEchnical Reqs
- The backend will e built using flask
- The database will be SQLlite 3
- The API will be built using Flask
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
     - GET /api/dashboard/last_study_session
     - GET /api/dashboard/study_progress
     - GET /api/dashboard/quick-stats
     - GET /api/study_activites/:id
     - GET /api/study_activites/:id/study_sessions

     - POST /api/study_activities
            - required params: group_id, study_activity_id

     - GET /api/words
        - pagination with 100 items per page
     - GET /api/words/:id
     - GET /api/groups
        - pagination with 100 items per page
     - GET /api/groups/:id
     - GET /api/groups/:id//words
     - GET /api/groups/:id/study_sessions
     -GET /api/study_sessions
        - pagination with 100 items per page
    - GET /api/study_sessions/:id
    - GET /api/study_sessions/:id/words
    - POST /api/reset_history
    - POST /api/full_reset
    - POST /api/study_sessions/:id/words/:word_id/review
        - required parms: correct

## API Endpoints

### `GET /api/dashboard/last_study_session`

```json
{
  "id": 123,
  "group_name": "Common Phrases",
  "correct_count": 8,
  "incorrect_count": 2,
  "total_words_reviewed": 10,
  "created_at": "2024-05-25T10:30:00Z"
}
```

---

### `GET /api/dashboard/study_progress`

```json
{
  "total_words_studied": 500,
  "total_vocabulary_in_db": 1200,
  "mastery_percentage": 41.67
}
```

---

### `GET /api/dashboard/quick-stats`

```json
{
  "success_rate_percentage": 80.00,
  "total_study_sessions": 4,
  "total_active_groups": 3,
  "study_streak_days": 4
}
```

---

### `GET /api/study_activities/:id`

```json
{
  "id": 1,
  "name": "Flashcards",
  "thumbnail_url": "/thumbnails/flashcards.png",
  "description": "Practice words with interactive flashcards.",
  "launch_url": "/app/flashcards"
}
```

---

### `GET /api/study_activities/:id/study_sessions`

```json
{
  "study_activity_id": 1,
  "study_activity_name": "Flashcards",
  "study_sessions": [
    {
      "id": 123,
      "group_name": "Common Phrases",
      "start_time": "2024-05-25T10:30:00Z",
      "end_time": "2024-05-25T10:45:00Z",
      "number_of_review_items": 15
    }
  ],
  "pagination": {
    "total_items": 5,
    "total_pages": 1,
    "current_page": 1,
    "items_per_page": 100,
    "next_page": null,
    "prev_page": null
  }
}
```

---

### `POST /api/study_activities`

**Required Params**: `group_id`, `study_activity_id`

```json
{
  "message": "Study activity session launched successfully.",
  "study_session_id": 125,
  "launch_url": "/app/flashcards?session_id=125"
}
```

---

### `GET /api/words`

**Pagination**: 100 items per page

```json
{
  "words": [
    {
      "id": 1,
      "french_word": "Bonjour",
      "quebec_pronunciation": "bon-zhoor",
      "english": "Hello",
      "correct_count": 10,
      "wrong_count": 2
    },
    {
      "id": 2,
      "french_word": "Merci",
      "quebec_pronunciation": "mair-see",
      "english": "Thank you",
      "correct_count": 8,
      "wrong_count": 5
    }
  ],
  "pagination": {
    "total_items": 1200,
    "total_pages": 12,
    "current_page": 1,
    "items_per_page": 100,
    "next_page": "/api/words?page=2&limit=100",
    "prev_page": null
  }
}
```

---

### `GET /api/words/:id`

```json
{
  "id": 5,
  "french_word": "Table",
  "quebec_pronunciation": "tabl",
  "english": "Table",
  "parts": ["furniture", "noun"],
  "study_statistics": {
    "correct_count": 15,
    "wrong_count": 3
  },
  "word_groups": [
    {
      "id": 10,
      "name": "Household Items"
    }
  ]
}
```

---

### `GET /api/groups`

**Pagination**: 100 items per page

```json
{
  "groups": [
    {
      "id": 1,
      "name": "Common Phrases",
      "word_count": 150
    }
  ],
  "pagination": {
    "total_items": 15,
    "total_pages": 1,
    "current_page": 1,
    "items_per_page": 100,
    "next_page": null,
    "prev_page": null
  }
}
```

---

### `GET /api/groups/:id`

```json
{
  "id": 1,
  "name": "Common Phrases",
  "total_word_count": 150
}
```

---

### `GET /api/groups/:id/words`

```json
{
  "group_id": 1,
  "group_name": "Common Phrases",
  "words": [
    {
      "id": 101,
      "french_word": "Bonjour",
      "quebec_pronunciation": "bon-zhoor",
      "english": "Hello",
      "correct_count": 10,
      "wrong_count": 2
    }
  ],
  "pagination": {
    "total_items": 150,
    "total_pages": 2,
    "current_page": 1,
    "items_per_page": 100,
    "next_page": "/api/groups/1/words?page=2&limit=100",
    "prev_page": null
  }
}
```

---

### `GET /api/groups/:id/study_sessions`

```json
{
  "group_id": 1,
  "group_name": "Common Phrases",
  "study_sessions": [
    {
      "id": 123,
      "activity_name": "Flashcards",
      "group_name": "Common Phrases",
      "start_time": "2024-05-25T10:30:00Z",
      "end_time": "2024-05-25T10:45:00Z",
      "number_of_review_items": 15
    }
  ],
  "pagination": {
    "total_items": 5,
    "total_pages": 1,
    "current_page": 1,
    "items_per_page": 100,
    "next_page": null,
    "prev_page": null
  }
}
```

---

### `GET /api/study_sessions`

**Pagination**: 100 items per page

```json
{
  "study_sessions": [
    {
      "id": 123,
      "activity_name": "Flashcards",
      "group_name": "Common Phrases",
      "start_time": "2024-05-25T10:30:00Z",
      "end_time": "2024-05-25T10:45:00Z",
      "number_of_review_items": 15
    }
  ],
  "pagination": {
    "total_items": 85,
    "total_pages": 1,
    "current_page": 1,
    "items_per_page": 100,
    "next_page": null,
    "prev_page": null
  }
}
```

---

### `GET /api/study_sessions/:id`

```json
{
  "id": 123,
  "activity_name": "Flashcards",
  "group_name": "Common Phrases",
  "start_time": "2024-05-25T10:30:00Z",
  "end_time": "2024-05-25T10:45:00Z",
  "number_of_review_items": 15
}
```

---

### `GET /api/study_sessions/:id/words`

```json
{
  "study_session_id": 123,
  "study_session_group_name": "Common Phrases",
  "word_review_items": [
    {
      "word_id": 101,
      "french_word": "Bonjour",
      "quebec_pronunciation": "bon-zhoor",
      "english": "Hello",
      "correct": true,
      "created_at": "2024-05-25T10:31:00Z"
    }
  ]
}
```

---

### `POST /api/reset_history`

```json
{
  "message": "Study history reset successfully."
}
```

---

### `POST /api/full_reset`

```json
{
  "message": "Full system reset completed successfully. Database reinitialized with seed data."
}
```

---

### `POST /api/study_sessions/:id/words/:word_id/review`

**Required Param**: `correct`

```json
{
  "message": "Word review recorded successfully.",
  "review_item_id": 789,
  "word_id": 101,
  "study_session_id": 123,
  "correct": true,
  "created_at": "2024-05-25T11:45:00Z"
}
```
