# YouTube Language Learning App

## For Homework Submission: Quick Notes

*   **Project Status:** Successfully implemented and tested Phase 1 (Transcript Extraction), Phase 2 (Structuring + Vectorization), and Phase 3 (RAG Chatbot) of the application.
*   **Key Technologies:** Streamlit, LangChain, ChromaDB, Hugging Face Embeddings (`sentence-transformers/all-MiniLM-L6-v2`), Hugging Face LLM (`google/flan-t5-base` for RAG).
*   **Phase 4 (Interactive Learning Generator):** This phase is currently a placeholder. Significant challenges were encountered in getting smaller, free LLMs (like Flan-T5) to reliably generate structured multiple-choice questions with consistent formatting and plausible incorrect answers directly from transcript snippets. While the backend structure for question generation (`backend/question_generator.py`) was attempted, it is currently not functional, and the frontend section is a placeholder.
*   **Running the App:** Execute the provided Colab cells sequentially. The final launch cell will start the Streamlit app accessible via an Ngrok tunnel.

## Detailed Project Summary

### Project Goal
To create a Streamlit-based web application that allows users to extract YouTube video transcripts, process them for language learning (structuring, vectorization), interact with them via a RAG chatbot, and eventually generate interactive multiple-choice questions.

### Current Project Status

We have successfully built and tested the core pipeline from transcript extraction through the RAG chatbot.

### Completed Phases:

*   **Phase 0: Initial Google Colab Setup and Project Structure**
    *   Created the complete modular project folder structure.
    *   Installed all necessary Python dependencies, including `langchain-huggingface` for free model integration.
    *   Configured and verified secure access to `NGROK_AUTH_TOKEN` via Colab Secrets.
    *   Successfully transitioned away from requiring `OPENAI_API_KEY` for embeddings and RAG by using Hugging Face models.

*   **Phase 1: YouTube Transcript Extraction**
    *   Implemented and independently tested `backend/transcript_fetcher.py` to fetch raw YouTube transcripts, save them to disk, and provide metadata.
    *   Implemented the corresponding UI in `frontend/app.py`.
    *   **Verified in App:** Successfully tested transcript fetching via the Streamlit UI.

*   **Phase 2: Transcript Structuring + Vectorization**
    *   Implemented and independently tested `backend/data_structurer.py` to read raw transcripts, split them into chunks using LangChain, and save structured data as JSON files (`yt_lang_app/data/structured/`).
    *   Implemented and independently tested `backend/vector_store.py` to load structured chunks, generate embeddings using a **free Hugging Face embedding model (`sentence-transformers/all-MiniLM-L6-v2`)**, and store them in **ChromaDB** (`yt_lang_app/data/chroma_db/`). This successfully replaced the initial plan's reliance on OpenAI embeddings.
    *   Implemented the corresponding UI in `frontend/app.py`.
    *   **Verified in App:** Successfully tested structuring and vectorization via the Streamlit UI.

*   **Phase 3: Chatbot using RAG**
    *   Implemented and independently tested `backend/chatbot_rag.py` to load the ChromaDB vector store, use a **free Hugging Face LLM (`google/flan-t5-base`)** to answer user queries based on the retrieved transcript chunks (RAG). This successfully replaced the initial plan's reliance on OpenAI for the RAG LLM.
    *   Implemented the corresponding UI in `frontend/app.py`, including displaying chat history and source chunks.
    *   **Verified in App:** Successfully tested the RAG chatbot in the Streamlit UI, confirming it can answer questions based on the loaded transcript content.

### Status of Phase 4: Interactive Learning Generator

*   This phase was initiated but encountered significant challenges in automated question generation using available free Hugging Face models.
*   **Difficulties:** Getting smaller LLMs like Flan-T5 to consistently produce structured output (e.g., specific JSON format or "Question: ... Correct Answer: ..." lines) required for programmatic parsing proved difficult. Generating plausible incorrect multiple-choice options automatically from varied text snippets is also a complex task.
*   **Current State:** The `backend/question_generator.py` file exists but is currently a placeholder, returning a message indicating it's not fully implemented. The corresponding section in `frontend/app.py` is marked as "Coming Soon!" and does not contain functional question generation logic.

### Future Development for Phase 4

To make the Interactive Learning Generator functional, future work could involve:
*   Exploring alternative free LLMs specifically known for better instruction following or Q&A generation capabilities.
*   Implementing more sophisticated prompting strategies and robust output parsing in `backend/question_generator.py`.
*   Simplifying the question generation task for the LLM (e.g., only generating the question and correct answer, with incorrect options generated purely programmatically).
*   Considering template-based question generation if LLM generation remains unreliable.
*   Adding the UI logic in `frontend/app.py` to call the backend question generator and display the results interactively.

## Running Your App
To run the application and test the implemented features (Phase 1, 2, and 3):
1.  Open this Google Colab notebook.
2.  Go to `Runtime` -> `Restart runtime` (recommended for a clean start).
3.  Run all cells from the beginning, in order.
4.  The final launch cell will start the Streamlit app and provide an Ngrok public URL.
5.  Click the provided URL to access the app in your browser.
6.  Use the sidebar to navigate between the "YouTube Transcript Extraction", "Transcript Structuring + Vectorization", and "Chatbot using RAG" sections.

Keep the Colab cell running to keep the Streamlit app active.
