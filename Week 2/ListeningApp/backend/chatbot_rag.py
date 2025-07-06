import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import HuggingFacePipeline
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate

def answer_question_rag(db_path: str, query: str, llm_model_name: str = "google/flan-t5-base") -> dict:
    """
    Answers a question using RAG based on the ChromaDB vector store.

    Args:
        db_path: Path to the ChromaDB directory.
        query: The user's question.
        llm_model_name: The name of the Hugging Face LLM to use.

    Returns:
        A dictionary containing the response and source chunks or an error message.
    """
    if not os.path.exists(db_path):
        return {"success": False, "error": f"Vector database not found at {db_path}. Please process the transcript first."}

    try:
        # Initialize the embedding model (must match the one used for creating the DB)
        embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"
        embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)

        # Load the Chroma vector store
        print(f"Loading ChromaDB from: {db_path}")
        db = Chroma(persist_directory=db_path, embedding_function=embeddings)
        print("ChromaDB loaded.")

        # Initialize the Hugging Face LLM
        print(f"Initializing Hugging Face LLM for RAG with model: {llm_model_name}")
        llm = HuggingFacePipeline.from_model_id(
            model_id=llm_model_name,
            task="text2text-generation",
            pipeline_kwargs={"max_new_tokens": 200, "temperature": 0.1}, # Adjusted max_new_tokens for RAG response
        )
        print("Hugging Face LLM for RAG initialized.")

        # Create a retriever from the vector store
        retriever = db.as_retriever(search_kwargs={"k": 4}) # Retrieve top 4 relevant chunks

        # Define the RAG prompt template
        # This prompt instructs the LLM to answer based *only* on the provided context
        rag_prompt_template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

{context}

Question: {question}
Helpful Answer:"""
        RAG_PROMPT = PromptTemplate(template=rag_prompt_template, input_variables=["context", "question"])


        # Create the RetrievalQA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff", # 'stuff' chains put all retrieved documents into the prompt
            retriever=retriever,
            chain_type_kwargs={"prompt": RAG_PROMPT}, # Pass the custom prompt
            return_source_documents=True # Return the source chunks
        )

        # Run the RAG chain
        print(f"Running RAG chain with query: '{query}'")
        response = qa_chain.invoke({"query": query})
        print("RAG chain completed.")


        # Extract the answer and source documents
        answer = response.get("result", "Could not generate an answer.")
        source_documents = response.get("source_documents", [])

        # Format source information for the frontend
        source_info = []
        for doc in source_documents:
             source_info.append({
                 "text": doc.page_content,
                 "metadata": doc.metadata
             })


        return {
            "success": True,
            "response": answer,
            "source_chunks": source_info
        }

    except Exception as e:
        return {"success": False, "error": f"An error occurred during RAG processing: {e}"}


if __name__ == '__main__':
    # Example usage for independent testing
    # You need a ChromaDB directory created from Phase 2 first
    test_db_path = "yt_lang_app/data/chroma_db" # Replace with the actual path if different
    test_query = "What is the video about?" # Replace with a question about your transcript
    test_llm = "google/flan-t5-base" # Or the model you intend to use

    print(f"Testing RAG Chatbot with DB: {test_db_path} and Query: '{test_query}'")

    if not os.path.exists(test_db_path):
        print(f"Error: Test DB path not found at {test_db_path}. Please run Phase 2 first.")
    else:
        rag_result = answer_question_rag(test_db_path, test_query, test_llm)
        print("\nRAG Chatbot Result:")
        print(json.dumps(rag_result, indent=2))

        # Optional: Print source chunks if successful
        if rag_result.get("success") and rag_result.get("source_chunks"):
            print("\nSource Chunks:")
            for i, source in enumerate(rag_result["source_chunks"]):
                 print(f"--- Source Chunk {i+1} ---")
                 print(f"Metadata: {source['metadata']}")
                 print(f"Content: {source['text'][:300]}...") # Print preview
                 print("-" * 20)
