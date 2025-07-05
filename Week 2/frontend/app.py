import streamlit as st
import os
import sys

# Add the project root to the system path to allow imports from backend
# This is needed because app.py runs as a script, not necessarily from project root
# Ensure the path is added only once if running cells out of order
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import backend modules
# Ensure this import works when app.py is run by Streamlit
try:
    from backend import transcript_fetcher
    from backend import data_structurer
    from backend import vector_store
    from backend import chatbot_rag # Import the RAG chatbot module
    # Import Chroma and HuggingFaceEmbeddings for potential direct use later (e.g., querying)
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
except ImportError as e:
    st.error(f"Failed to import backend modules. Make sure the file structure is correct. Error: {e}")
    st.stop() # Stop Streamlit if essential imports fail

# --- Streamlit App Frontend ---
st.set_page_config(
    page_title="YT Language Learning App",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("YouTube Language Learning App")

# Radio buttons for main functionality
feature_selection = st.sidebar.radio(
    "Choose a Feature:",
    [
        "1. YouTube Transcript Extraction",
        "2. Transcript Structuring + Vectorization",
        "3. Chatbot using RAG",
        "4. Interactive Learning Generator",
    ],
    index=0 # Default to the first option
)

# Initialize chat history if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

if feature_selection == "1. YouTube Transcript Extraction":
    st.header("1. YouTube Transcript Extraction")
    st.write("Paste a YouTube video URL below to extract its transcript and view basic statistics.")

    youtube_url = st.text_input("YouTube Video URL:", help="e.g., https://www.youtube.com/watch?v=isMpyCkKuDU")

    if st.button("Get Transcript"):
        if youtube_url:
            with st.spinner("Fetching transcript... This might take a moment."):
                transcript_data = transcript_fetcher.fetch_transcript(youtube_url)

                if transcript_data.get("success"):
                    st.session_state.current_transcript_data = transcript_data # Store for other modules
                    st.success("Transcript fetched successfully!")

                    st.subheader("Transcript Preview:")
                    st.text_area(
                        "Raw Transcript (Preview)",
                        transcript_data["transcript_preview"],
                        height=250,
                        help="First 1000 characters of the transcript."
                    )

                    st.subheader("Transcript Statistics:")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Word Count", transcript_data["word_count"])
                    with col2:
                        st.metric("Token Count (estimated)", transcript_data["token_count"])
                    with col3:
                        st.metric("Est. Reading Time", f"{transcript_data['estimated_reading_time_minutes']} mins")

                    st.info(f"Full transcript saved to: `{transcript_data['full_transcript_path']}`")
                    # Clear previous structuring/vectorization results and chat history if a new transcript is fetched
                    st.session_state.pop('structured_file_path', None)
                    st.session_state.pop('chroma_db_path', None)
                    st.session_state.messages = [] # Clear chat history

                else:
                    st.error(transcript_data.get("error", "An unknown error occurred during transcript fetching."))
                    st.session_state.pop('current_transcript_data', None) # Clear state on error
                    st.session_state.pop('structured_file_path', None)
                    st.session_state.pop('chroma_db_path', None)
                    st.session_state.messages = [] # Clear chat history on error
        else:
            st.warning("Please enter a YouTube video URL.")

# --- Transcript Structuring + Vectorization ---
elif feature_selection == "2. Transcript Structuring + Vectorization":
    st.header("2. Transcript Structuring + Vectorization")
    st.write("Process the raw transcript into structured chunks and create a vector database using a free embedding model.")

    if "current_transcript_data" not in st.session_state or not st.session_state.current_transcript_data.get("success"):
        st.warning("Please fetch a transcript first in '1. YouTube Transcript Extraction' section.")
    else:
        transcript_info = st.session_state.current_transcript_data
        st.info(f"Using transcript for video ID: `{transcript_info.get('video_id', 'N/A')}`")
        st.text_area("Transcript Preview:", transcript_info.get("transcript_preview", ""), height=150, disabled=True)


        if st.button("Process Transcript and Create Vector Store"):
            raw_transcript_path = transcript_info.get("full_transcript_path")
            video_id = transcript_info.get("video_id") # Get video_id here

            if raw_transcript_path and os.path.exists(raw_transcript_path) and video_id:
                # Step 1: Structure the transcript
                with st.spinner("Structuring transcript into chunks..."):
                    structuring_result = data_structurer.structure_transcript(video_id)

                if structuring_result.get("success"):
                    st.session_state.structured_file_path = structuring_result["structured_file_path"]
                    st.success("Transcript structured successfully!")
                    st.write(f"Number of chunks created: {structuring_result.get('num_chunks', 'N/A')}")
                    st.text_area("Sample Chunk Preview:", structuring_result.get('preview_chunk', ''), height=100, disabled=True)
                    st.info(f"Structured data saved to: `{structuring_result['structured_file_path']}`")

                    # Step 2: Create the vector store
                    with st.spinner("Creating vector store using Hugging Face embeddings..."):
                        # Call create_vector_store without openai_api_key
                        vector_store_result = vector_store.create_vector_store(video_id)

                    if vector_store_result.get("success"):
                        st.session_state.chroma_db_path = vector_store_result["db_path"] # Corrected key name
                        st.success("Vector store created successfully!")
                        st.write(f"Documents added to vector store: {vector_store_result.get('num_documents_added', 'N/A')}")
                        st.info(f"Vector database stored at: `{vector_store_result['db_path']}`") # Corrected key name
                        st.session_state.messages = [] # Clear chat history if a new vector store is created
                    else:
                        st.error(f"Error creating vector store: {vector_store_result.get('error', 'Unknown error')}")
                        st.session_state.pop('chroma_db_path', None) # Clear state on error
                        st.session_state.messages = [] # Clear chat history on error


                else:
                    st.error(f"Error structuring transcript: {structuring_result.get('error', 'Unknown error')}")
                    st.session_state.pop('structured_file_path', None) # Clear state on error
                    st.session_state.pop('chroma_db_path', None)
                    st.session_state.messages = [] # Clear chat history on error


            else:
                st.error(f"Raw transcript file not found at {raw_transcript_path} or Video ID is missing. Please re-fetch the transcript.")
                st.session_state.pop('current_transcript_data', None) # Clear state if file is missing
                st.session_state.pop('structured_file_path', None)
                st.session_state.pop('chroma_db_path', None)
                st.session_state.messages = [] # Clear chat history if file is missing


# --- Chatbot using RAG ---
elif feature_selection == "3. Chatbot using RAG":
    st.header("3. Chatbot using RAG")
    st.write("Ask questions about the video transcript.")

    # Check if vector store is available
    if "chroma_db_path" not in st.session_state or not os.path.exists(st.session_state.chroma_db_path):
        st.warning("Please process the transcript and create the vector store first in the 'Transcript Structuring + Vectorization' section.")
    else:
        st.success("Vector store is ready! You can now chat about the transcript.")
        chroma_db_path = st.session_state.chroma_db_path
        llm_model_name = "google/flan-t5-base" # Use the selected free LLM

        # Display chat messages from history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant" and message.get("source_info"):
                     with st.expander("Source Chunks"):
                         for source in message["source_info"]:
                             st.write(f"**Chunk ID:** {source['metadata'].get('chunk_id', 'N/A')}")
                             st.write(source['text'][:300] + "...") # Show preview
                             st.markdown("---")


        # Chat input
        if prompt := st.chat_input("Ask a question about the transcript..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)

            # Get assistant response
            with st.chat_message("assistant"):
                with st.spinner("Generating response..."):
                    rag_response = chatbot_rag.answer_question_rag(chroma_db_path, prompt, llm_model_name)

                    if rag_response.get("success"):
                        response_text = rag_response.get("response", "Could not generate an answer.")
                        source_info = rag_response.get("source_chunks", [])

                        st.markdown(response_text)

                        # Display source chunks in an expander
                        if source_info:
                             with st.expander("Source Chunks"):
                                 for source in source_info:
                                     st.write(f"**Chunk ID:** {source['metadata'].get('chunk_id', 'N/A')}")
                                     st.write(source['text'][:300] + "...") # Show preview
                                     st.markdown("---")


                        # Add assistant message to chat history
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response_text,
                            "source_info": source_info # Store source info in history
                        })
                    else:
                        error_message = rag_response.get("error", "An error occurred during RAG.")
                        st.error(f"Error: {error_message}")
                        st.session_state.messages.append({"role": "assistant", "content": f"Error: {error_message}"})


# --- Interactive Learning Generator ---
elif feature_selection == "4. Interactive Learning Generator":
    st.header("4. Interactive Learning Generator (Coming Soon!)")
    st.info("This section will feature interactive learning exercises based on the video transcript.")
    # Add checks for structured data and vector store existence in session state/disk
