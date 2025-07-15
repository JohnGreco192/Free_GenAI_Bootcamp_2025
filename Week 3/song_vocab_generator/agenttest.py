Current Working Directory: /content
sys.path: ['/content/song_vocab_generator', '/content/', '/content', '/env/python', '/usr/lib/python311.zip', '/usr/lib/python3.11', '/usr/lib/python3.11/lib-dynload', '', '/usr/local/lib/python3.11/dist-packages', '/usr/lib/python3/dist-packages', '/usr/local/lib/python3.11/dist-packages/IPython/extensions', '/usr/local/lib/python3.11/dist-packages/setuptools/_vendor', '/root/.ipython']

--- Testing Song-to-Vocab Agent (End-to-End) ---
Environment variables for API key and CSE ID set for testing.
Initializing SongToVocabAgent...
Database 'vocabulary.db' initialized and 'vocabulary' table ensured.
SongToVocabAgent initialized.

Attempting to process: 'Bohemian Rhapsody' by Queen

--- Agent Processing Request for 'Bohemian Rhapsody' by Queen ---
Step 1: Searching and retrieving lyrics...
Searching for lyrics with query: 'Bohemian Rhapsody lyrics Queen site:azlyrics.com OR site:lyricfind.com OR site:metrolyrics.com OR site:songlyrics.com OR site:lyrics.com'
Found 10 search results.
Attempting to retrieve lyrics from domain: azlyrics.com
  Attempting URL: https://www.azlyrics.com/lyrics/queen/bohemianrhapsody.html
  Page content fetched.
  An unexpected error occurred during parsing https://www.azlyrics.com/lyrics/queen/bohemianrhapsody.html: 'NoneType' object has no attribute 'find_next_sibling'
  Attempting URL: https://www.azlyrics.com/lyrics/pentatonix/bohemianrhapsody.html
  Page content fetched.
  An unexpected error occurred during parsing https://www.azlyrics.com/lyrics/pentatonix/bohemianrhapsody.html: 'NoneType' object has no attribute 'find_next_sibling'
  Attempting URL: https://www.azlyrics.com/lyrics/panicatthedisco/bohemianrhapsody.html
  Page content fetched.
  An unexpected error occurred during parsing https://www.azlyrics.com/lyrics/panicatthedisco/bohemianrhapsody.html: 'NoneType' object has no attribute 'find_next_sibling'
  Attempting URL: https://www.azlyrics.com/lyrics/imany/bohemianrhapsody.html
  Page content fetched.
  An unexpected error occurred during parsing https://www.azlyrics.com/lyrics/imany/bohemianrhapsody.html: 'NoneType' object has no attribute 'find_next_sibling'
  Attempting URL: https://www.azlyrics.com/lyrics/alexgoot/bohemianrhapsody.html
  Page content fetched.
  An unexpected error occurred during parsing https://www.azlyrics.com/lyrics/alexgoot/bohemianrhapsody.html: 'NoneType' object has no attribute 'find_next_sibling'
  Attempting URL: https://www.azlyrics.com/lyrics/queen/loveofmylife.html
  Page content fetched.
  An unexpected error occurred during parsing https://www.azlyrics.com/lyrics/queen/loveofmylife.html: 'NoneType' object has no attribute 'find_next_sibling'
  Attempting URL: https://www.azlyrics.com/lyrics/anthemlights/queenmedley.html
  Page content fetched.
  An unexpected error occurred during parsing https://www.azlyrics.com/lyrics/anthemlights/queenmedley.html: 'NoneType' object has no attribute 'find_next_sibling'
  Attempting URL: https://www.azlyrics.com/lyrics/dewa19/bohemianrhapsody.html
  Page content fetched.
  An unexpected error occurred during parsing https://www.azlyrics.com/lyrics/dewa19/bohemianrhapsody.html: 'NoneType' object has no attribute 'find_next_sibling'
Attempting to retrieve lyrics from domain: songlyrics.com
  Attempting URL: http://www.songlyrics.com/queen/bohemian-rhapsody-remastered-lyrics/
  Page content fetched.
  Extracted lyrics using general selector: div[class*="lyrics"]
Successfully retrieved and processed lyrics from http://www.songlyrics.com/queen/bohemian-rhapsody-remastered-lyrics/
Step 1: Lyrics retrieved successfully.
Step 2: Extracting vocabulary from lyrics using LLM...
Calling LLM for vocabulary extraction...
Vocabulary extracted successfully.
Step 2: Extracted 13 vocabulary items.
Step 3: Storing extracted vocabulary in the database...
Successfully stored 13 unique vocabulary items for 'Bohemian Rhapsody' by Queen.
Step 3: Vocabulary stored successfully.
--- Agent Process for 'Bohemian Rhapsody' by Queen Completed Successfully ---
Agent processing result for 'Bohemian Rhapsody': True
Retrieved 13 vocabulary items for 'Bohemian Rhapsody' by Queen.
Successfully retrieved 13 vocabulary items for 'Bohemian Rhapsody' from DB.
Test passed for successful song processing and DB storage.

Attempting to process: 'NonExistentSong12345' by ImaginaryArtist (expecting failure)

--- Agent Processing Request for 'NonExistentSong12345' by ImaginaryArtist ---
Step 1: Searching and retrieving lyrics...
Searching for lyrics with query: 'NonExistentSong12345 lyrics ImaginaryArtist site:azlyrics.com OR site:lyricfind.com OR site:metrolyrics.com OR site:songlyrics.com OR site:lyrics.com'
No search results found with a link.
Agent failed: Could not retrieve lyrics.
Agent processing result for 'NonExistentSong12345': False
Test passed: Agent correctly handled song not found scenario.

Cleaned up: Removed database file 'vocabulary.db'.
Reloaded vocabulary_extraction module.

--- Testing Song-to-Vocab Agent (End-to-End) ---
Environment variables for API key and CSE ID set for testing.
Initializing SongToVocabAgent...
Database 'vocabulary.db' initialized and 'vocabulary' table ensured.
SongToVocabAgent initialized.

Attempting to process: 'Bohemian Rhapsody' by Queen

--- Agent Processing Request for 'Bohemian Rhapsody' by Queen ---
Step 1: Searching and retrieving lyrics...
Searching for lyrics with query: 'Bohemian Rhapsody lyrics Queen site:azlyrics.com OR site:lyricfind.com OR site:metrolyrics.com OR site:songlyrics.com OR site:lyrics.com'
Found 10 search results.
Attempting to retrieve lyrics from domain: azlyrics.com
  Attempting URL: https://www.azlyrics.com/lyrics/queen/bohemianrhapsody.html
  Page content fetched.
  An unexpected error occurred during parsing https://www.azlyrics.com/lyrics/queen/bohemianrhapsody.html: 'NoneType' object has no attribute 'find_next_sibling'
  Attempting URL: https://www.azlyrics.com/lyrics/pentatonix/bohemianrhapsody.html
  Page content fetched.
  An unexpected error occurred during parsing https://www.azlyrics.com/lyrics/pentatonix/bohemianrhapsody.html: 'NoneType' object has no attribute 'find_next_sibling'
  Attempting URL: https://www.azlyrics.com/lyrics/panicatthedisco/bohemianrhapsody.html
  Page content fetched.
  An unexpected error occurred during parsing https://www.azlyrics.com/lyrics/panicatthedisco/bohemianrhapsody.html: 'NoneType' object has no attribute 'find_next_sibling'
  Attempting URL: https://www.azlyrics.com/lyrics/imany/bohemianrhapsody.html
  Page content fetched.
  An unexpected error occurred during parsing https://www.azlyrics.com/lyrics/imany/bohemianrhapsody.html: 'NoneType' object has no attribute 'find_next_sibling'
  Attempting URL: https://www.azlyrics.com/lyrics/alexgoot/bohemianrhapsody.html
  Page content fetched.
  An unexpected error occurred during parsing https://www.azlyrics.com/lyrics/alexgoot/bohemianrhapsody.html: 'NoneType' object has no attribute 'find_next_sibling'
  Attempting URL: https://www.azlyrics.com/lyrics/queen/loveofmylife.html
  Page content fetched.
  An unexpected error occurred during parsing https://www.azlyrics.com/lyrics/queen/loveofmylife.html: 'NoneType' object has no attribute 'find_next_sibling'
  Attempting URL: https://www.azlyrics.com/lyrics/anthemlights/queenmedley.html
  Page content fetched.
  An unexpected error occurred during parsing https://www.azlyrics.com/lyrics/anthemlights/queenmedley.html: 'NoneType' object has no attribute 'find_next_sibling'
  Attempting URL: https://www.azlyrics.com/lyrics/dewa19/bohemianrhapsody.html
  Page content fetched.
  An unexpected error occurred during parsing https://www.azlyrics.com/lyrics/dewa19/bohemianrhapsody.html: 'NoneType' object has no attribute 'find_next_sibling'
Attempting to retrieve lyrics from domain: songlyrics.com
  Attempting URL: http://www.songlyrics.com/queen/bohemian-rhapsody-remastered-lyrics/
  Page content fetched.
  Extracted lyrics using general selector: div[class*="lyrics"]
Successfully retrieved and processed lyrics from http://www.songlyrics.com/queen/bohemian-rhapsody-remastered-lyrics/
Step 1: Lyrics retrieved successfully.
Step 2: Extracting vocabulary from lyrics using LLM...
Calling LLM for vocabulary extraction...
Vocabulary extracted successfully.
Step 2: Extracted 12 vocabulary items.
Step 3: Storing extracted vocabulary in the database...
Successfully stored 12 unique vocabulary items for 'Bohemian Rhapsody' by Queen.
Step 3: Vocabulary stored successfully.
--- Agent Process for 'Bohemian Rhapsody' by Queen Completed Successfully ---
Agent processing result for 'Bohemian Rhapsody': True
Retrieved 12 vocabulary items for 'Bohemian Rhapsody' by Queen.
Successfully retrieved 12 vocabulary items for 'Bohemian Rhapsody' from DB.
Test passed for successful song processing and DB storage.

Attempting to process: 'NonExistentSong12345' by ImaginaryArtist (expecting failure)

--- Agent Processing Request for 'NonExistentSong12345' by ImaginaryArtist ---
Step 1: Searching and retrieving lyrics...
Searching for lyrics with query: 'NonExistentSong12345 lyrics ImaginaryArtist site:azlyrics.com OR site:lyricfind.com OR site:metrolyrics.com OR site:songlyrics.com OR site:lyrics.com'
No search results found with a link.
Agent failed: Could not retrieve lyrics.
Agent processing result for 'NonExistentSong12345': False
Test passed: Agent correctly handled song not found scenario.

Cleaned up: Removed database file 'vocabulary.db'.