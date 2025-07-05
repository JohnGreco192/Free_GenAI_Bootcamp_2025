import os
import json
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

def create_vector_store(video_id: str) -> dict:
    """
    Loads structured transcript chunks, creates embeddings using Hugging Face,
    and stores them in ChromaDB.

    Args:
        video_id: The YouTube video ID.

    Returns:
        A dictionary indicating success/failure and relevant information.
    """
    # Assuming structured data is saved in a JSON file with this naming convention
    structured_data_path = f"yt_lang_app/data/structured/{video_id}_structured.json" # Match filename convention from data_structurer.py
    chroma_db_dir = "yt_lang_app/data/chroma_db"

    os.makedirs(chroma_db_dir, exist_ok=True)

    if not os.path.exists(structured_data_path):
        return {"success": False, "error": f"Structured data file not found for video ID: {video_id} at {structured_data_path}."}

    try:
        with open(structured_data_path, "r", encoding="utf-8") as f:
            structured_chunks = json.load(f)
    except json.JSONDecodeError:
        return {"success": False, "error": f"Error decoding JSON from structured data file: {structured_data_path}"}
    except Exception as e:
        return {"success": False, "error": f"Error reading structured data: {e}"}

    if not structured_chunks:
        return {"success": False, "error": f"No structured chunks found in the file: {structured_data_path}"}

    # Extract text content and prepare metadata
    texts = [chunk.get('text', '') for chunk in structured_chunks if chunk.get('text')] # Ensure text exists and is not empty
    metadatas = [
        {"video_id": chunk.get('video_id', video_id), "chunk_index": chunk.get('chunk_index', i)}
        for i, chunk in enumerate(structured_chunks) if chunk.get('text') # Ensure metadata aligns with valid texts
    ]

    if not texts:
         return {"success": False, "error": "No valid text content found in structured chunks after filtering."}


    try:
        # Initialize the Hugging Face embedding model
        # Using a common, relatively small and performant model
        embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"
        print(f"Initializing Hugging Face Embedding Model: {embedding_model_name}")
        embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)
        print("Embedding Model Initialized.")

        # Initialize the Chroma vector store
        # This will create or load the database at the specified path
        print(f"Creating/Updating ChromaDB at: {chroma_db_dir}")
        db = Chroma.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metadatas,
            persist_directory=chroma_db_dir
        )

        # Persist the database to disk (often done automatically with persist_directory)
        # db.persist() # Not strictly needed with persist_directory in from_texts

        print("ChromaDB created/updated.")

        return {
            "success": True,
            "video_id": video_id,
            "db_path": chroma_db_dir,
            "num_documents_added": len(texts),
            "message": f"Successfully created/updated ChromaDB for video ID {video_id}"
        }

    except Exception as e:
        return {"success": False, "error": f"Error creating or updating ChromaDB: {e}"}

# Example usage for independent testing (will be called from a separate test cell)
if __name__ == '__main__':
    # This block will be executed only when the script is run directly,
    # not when imported as a module in the test cell.
    # The independent test will be in a separate Colab cell.
    pass # Placeholder for the test block
