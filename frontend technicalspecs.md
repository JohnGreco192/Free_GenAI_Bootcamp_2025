# Frontend TEchnical Spec

## Pages

### Dashboard /dashboard

This page contains the following coponents
- Last Study Session
    - shows last activity used
    - shows when last activity used
    - summarizes wrong vs correct from last activity
    - has a link to the group
- Study Progress
    - total words study eg. 3/124
        - across all study session show the total words studided out of all possible words in our database
    - display a mastery progress eg 0%
- Quick Stats
    - Success rate eg. 80%
    - total studdy sessions eg. 4
    - total active groups eg. 3
    - study streak eg. 4 days
- Start Studying Button
    - goes to study activities page 

    We will need the following API endpoints to power this page
    - GET /dashboard/last_study_session
    - GET /dashboard/study_progress
    - GET /dashboard/quick-stats
