import os
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter

def structure_transcript(video_id: str) -> dict:
    """
    Loads raw transcript, splits it into chunks, and saves as a JSON file.

    Args:
        video_id: The YouTube video ID.

    Returns:
        A dictionary indicating success/failure and relevant information.
    """
    raw_transcript_path = f"yt_lang_app/data/transcripts/{video_id}.txt"
    structured_data_dir = "yt_lang_app/data/structured"
    structured_data_path = os.path.join(structured_data_dir, f"{video_id}_structured.json") # Changed filename convention

    os.makedirs(structured_data_dir, exist_ok=True)

    if not os.path.exists(raw_transcript_path):
         return {"success": False, "error": f"Raw transcript file not found for video ID: {video_id} at {raw_transcript_path}."}

    try:
        with open(raw_transcript_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
    except Exception as e:
        return {"success": False, "error": f"Error reading raw transcript file {raw_transcript_path}: {e}"}

    if not raw_text.strip():
         return {"success": False, "error": f"Raw transcript file {raw_transcript_path} is empty or contains only whitespace."}


    # Initialize the text splitter
    # Adjust chunk_size and chunk_overlap as needed based on experimentation
    # Using character splitting as a robust default
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, # Size of each chunk
        chunk_overlap=200, # Overlap between chunks to maintain context
        length_function=len, # Use character length
        is_separator_regex=False, # Use standard separators
        separators=["\\n\\n", "\\n", " ", ""] # List of separators
    )

    # Split the text
    chunks = text_splitter.split_text(raw_text)

    if not chunks:
         return {"success": False, "error": f"Text splitter did not produce any chunks from the raw transcript."}


    # Structure the data
    structured_chunks = []
    for i, chunk in enumerate(chunks):
        structured_chunks.append({
            "chunk_index": i,
            "text": chunk.strip(), # Strip leading/trailing whitespace from chunks
            "video_id": video_id,
            # Add other metadata here if needed, e.g., approximate timestamps if available from raw transcript structure
        })

    # Remove any empty chunks that might result from splitting/stripping
    structured_chunks = [chunk for chunk in structured_chunks if chunk["text"]]

    if not structured_chunks:
        return {"success": False, "error": f"No valid structured chunks were created after splitting and stripping."}


    try:
        with open(structured_data_path, "w", encoding="utf-8") as f:
            json.dump(structured_chunks, f, indent=2)

        # Get a preview of the first non-empty chunk
        preview_chunk_text = structured_chunks[0]['text'] if structured_chunks else "No chunks generated"
        preview_chunk_text = preview_chunk_text[:500] + "..." if len(preview_chunk_text) > 500 else preview_chunk_text


        return {
            "success": True,
            "video_id": video_id,
            "structured_file_path": structured_data_path,
            "num_chunks": len(structured_chunks),
            "preview_chunk": preview_chunk_text,
            "message": f"Successfully structured transcript for video ID {video_id}"
        }
    except Exception as e:
        return {"success": False, "error": f"Error saving structured data to {structured_data_path}: {e}"}

# Example usage for independent testing (will be called from a separate test cell)
if __name__ == '__main__':
    # This block will be executed only when the script is run directly,
    # not when imported as a module in the test cell.
    # The independent test will be in a separate Colab cell.
    pass # Placeholder for the test block
