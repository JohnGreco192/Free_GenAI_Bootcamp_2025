# Agentic Song Vocabulary Generator

## Business Goal
We aim to develop an intelligent agent that can find lyrics for a target song in a specific language from the internet and then process these lyrics to extract relevant vocabulary, which will then be imported into our database. The core idea is for the agent to autonomously manage the entire workflow from song identification to vocabulary storage.

## Technical Requirements
-   **Python:** The primary programming language for implementing the agent and its tools.
-   **LLM Model Server:** An easily compatible LLM (preferably Mistral 7B, or similar) suitable for agentic workflows within Google Colab environments. This LLM will be used for sophisticated text analysis and vocabulary extraction.
-   **SQLite3:** A lightweight, file-based database for storing the extracted vocabulary.
-   **Internet Search Capability:** Integration with search engines like Google or DuckDuckGo for efficiently finding song lyrics.

## Agentic Workflow Definition

Instead of separate endpoints, we will implement a single, cohesive agent responsible for orchestrating the entire process. This agent will leverage internal "tools" to achieve its goal.

### The Song-to-Vocab Agent

**Primary Function:**
The agent's main role is to receive a request for a song (by name and optionally artist) and then execute a sequence of internal steps (using its tools) to find the lyrics, extract vocabulary, and store it.

**Agent Invocation (Input):**
The agent will be invoked with the following parameters:

* `song_name` (str): (Required) The name of the song to process.
* `artist_name` (str): (Optional) The name of the artist for more accurate lyric search.

**Agent's Internal Tools:**

The agent will manage and call the following internal tools as part of its workflow:

1.  **Lyric Search & Retrieval Tool**
    * **Purpose:** To search the internet for the specified song's lyrics and retrieve them as plain text.
    * **Inputs:** `song_name` (str), `artist_name` (str, Optional).
    * **Action:**
        * Constructs a search query using the provided song and artist names (e.g., "\[song\_name] lyrics \[artist\_name]").
        * Utilizes a search engine (Google or DuckDuckGo) to find relevant lyric websites.
        * Employs a web Browse capability to fetch the content from the most promising lyric URL.
        * Parses and extracts the main lyrics text from the retrieved web page.
    * **Output:** `lyrics` (str) - The extracted lyrics in plain text format. If lyrics cannot be found or retrieved, this tool should indicate failure (e.g., return `None`).
    * **Dependencies:** Python's `Google Search` or `duckduckgo_search` libraries/APIs, and a web content retrieval/parsing mechanism (e.g., `Browse` tool, `BeautifulSoup`).

2.  **Vocabulary Extraction Tool**
    * **Purpose:** To analyze a given block of song lyrics and identify a list of vocabulary words along with their definitions.
    * **Inputs:** `lyrics_text` (str) - The raw lyrics content obtained from the Lyric Search & Retrieval Tool.
    * **Action:**
        * Feeds the `lyrics_text` to the designated LLM (`mistral 7b` or compatible).
        * Prompts the LLM to identify vocabulary words that might be unfamiliar to a language learner, focusing on contextually relevant terms.
        * Instructs the LLM to provide a concise definition for each identified word.
        * Ensures the LLM's output adheres strictly to the specified JSON format.
    * **Output:** `vocabulary_list` (List of JSON Objects) - A list of dictionaries, where each dictionary represents a vocabulary word and its definition.
        ```json
        [
            {
                "word": "melancholy",
                "definition": "a feeling of pensive sadness, typically with no obvious cause."
            },
            {
                "word": "serenade",
                "definition": "a piece of music sung or played in the open air, typically by a man to his beloved one."
            }
        ]
        ```
    * **Dependencies:** The chosen LLM model server (e.g., `mistral 7b` API).

3.  **Database Storage Tool**
    * **Purpose:** To persist the extracted vocabulary into the SQLite database.
    * **Inputs:**
        * `song_name` (str)
        * `artist_name` (str, Optional)
        * `vocabulary_list` (List of JSON Objects, as defined above).
    * **Action:**
        * Connects to the SQLite3 database (`vocabulary.db`).
        * For each word-definition pair in the `vocabulary_list`, it inserts or updates a record in a `vocabulary` table, linking it to the `song_name` and `artist_name`. The table should support `(song_name, artist_name, word)` as a unique key to prevent duplicate entries for the same song and word.
    * **Output:** Confirmation of successful storage or an error message.
    * **Dependencies:** `sqlite3` Python library.

**Agent's Overall Behavior:**
When invoked, the Song-to-Vocab Agent will:
1.  Attempt to use the **Lyric Search & Retrieval Tool** to get the lyrics.
2.  If lyrics are successfully retrieved, it will then pass them to the **Vocabulary Extraction Tool**.
3.  If vocabulary is successfully extracted, it will pass the vocabulary list, along with song details, to the **Database Storage Tool**.
4.  The agent will report the overall success or failure of the entire operation, potentially providing logs of its internal steps.