# Frontend TEchnical Spec

## Pages

### Dashboard '/dashboard'

#### Purpose
The purpose of this page is to provide a summary of learning and act as a default pag ewhen the user visists the web app

#### Components
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
#### Needed API Endpoints
    We will need the following API endpoints to power this page
    - GET /api/dashboard/last_study_session
    - GET /api/dashboard/study_progress
    - GET /api/dashboard/quick-stats


### Study Activities '/study_activities'

#### Purpose
The purpose of this page is to sow a collection of study activities with a thumbnail and its name, either to launch  or view the study activity

#### Components
- Study Activtiy Card
    - show a thumbnail of the study activity
    - the name of the study activity
    - a lanch button to take us to the launch page
    - the biew page to bie more information abou tpast study sessions for this study activity

#### Needed API Endpoints
- GET /api/study_activities

### Study Activity Show '/study_activities/:id'
#### Purpose
The purpose of this page is to show the details of a study activity and its past study sessions
#### Components
- Name of study activity
- Thubnail of study activity
- Description of study actvity
- Launch button
- Study Activities Paginated List
    - id
    - activity name
    - group name
    - start time
    - end time (inferred by the last word_review_item submitted)
    - number of review items
#### Needed API Endpoints
- GET /api/study_activites/:id
- GET /api/study_activites/:id/study_sessions