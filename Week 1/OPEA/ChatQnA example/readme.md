# OPEA ChatQnA Application Setup for NVIDIA T4 GPU

This `opea.sh` script automates the setup and deployment of a **Retrieval-Augmented Generation (RAG) based ChatQnA application** within a **Lightning AI terminal** environment, specifically optimized for **NVIDIA T4 GPUs**.

It leverages the [OPEA (Open Platform for Enterprise AI) project](https://github.com/opea-project/OPEA) and its [GenAIExamples repository](https://github.com/opea-project/GenAIExamples) to provide a ready-to-use solution for building chatbots that can answer questions based on external knowledge.

## Features

* **Automated Setup:** Handles cloning necessary repositories, configuring environment variables, and starting services.
* **RAG Architecture:** Deploys a full RAG pipeline including:
    * **Large Language Model (LLM):** Utilizes `meta-llama/Llama-2-7b-chat-hf` (7 Billion parameters), suitable for T4 GPUs.
    * **Embedding Model:** `BAAI/bge-base-en-v1.5` for converting text to numerical representations.
    * **Reranking Model:** `BAAI/bge-reranker-base` for improving the relevance of retrieved information.
    * **Retrieval Components:** For searching and fetching relevant data.
    * **Backend & UI Services:** For managing the application logic and providing a web interface.
* **Docker Compose:** Orchestrates all interdependent services using `docker compose` for simplified deployment and management.
* **GPU Optimization:** Automatically configures the Text Embeddings Inference (TEI) reranking service image for NVIDIA Turing architecture (T4 GPU compatibility).
* **Lightning AI Integration:** Designed to run directly within a Lightning AI Studio terminal.

## Prerequisites

* **Lightning AI Studio:** Access to a Lightning AI Studio instance.
* **NVIDIA T4 GPU:** Ensure your Lightning AI Studio has an NVIDIA T4 GPU allocated. The `Llama-2-7b-chat-hf` model is selected to fit within the T4's 16GB VRAM.
* **Docker:** Docker must be installed and running within your Lightning AI Studio environment (usually pre-configured).
* **Hugging Face Token:** A Hugging Face User Access Token with read access for gated models (like Llama 2). You will need to replace the placeholder token in the script with your own. You can generate one from your [Hugging Face settings](https://huggingface.co/settings/tokens).

## How to Run

1.  **Open a Terminal in Lightning AI Studio:** Navigate to the root directory of your project where you've placed this `opea.sh` script.

2.  **Make the Script Executable:**
    ```bash
    chmod +x opea.sh
    ```

3.  **Execute the Script:**
    ```bash
    ./opea.sh
    ```

    The script will perform the following actions:
    * Clone the `opea-project/GenAIExamples` repository if it doesn't already exist.
    * Change into the appropriate Docker Compose directory for NVIDIA GPU setup (`GenAIExamples/ChatQnA/docker_compose/nvidia/gpu`).
    * Source `set_env.sh` if present (for OPEA's default environment variables).
    * Set custom environment variables, including your **Hugging Face Token**, `host_ip`, model IDs, and service endpoints.
    * Create a `.env` file in the current directory for Docker Compose to pick up these variables.
    * **Crucially**, it will modify the `compose.yaml` file to use a T4-optimized Text Embeddings Inference (TEI) reranking service image (`turing-1.5`).
    * Start all required services (LLM, embedding, reranking, retriever, backend, UI) using `docker compose up -d`.

4.  **Monitor Services (Optional but Recommended):**
    After running the script, you can monitor the logs of the Text Generation Inference (TGI) service (which hosts the LLM) to ensure it's ready:
    ```bash
    docker logs tgi-service
    ```
    Wait for a "Connected" or similar ready message in the TGI logs.

## Accessing the Application

Once the services are running:

* **ChatQnA UI:** Open your web browser and navigate to:
    ```
    http://<Your_Host_IP_Address>:<NGINX_PORT>
    ```
    (The `NGINX_PORT` defaults to `80`, so usually `http://<Your_Host_IP_Address>`)

    The `Your_Host_IP_Address` will be displayed in the terminal output when the script finishes.

* **Direct ChatQnA Service API Interaction:**
    You can also interact directly with the backend API using `curl`:
    ```bash
    curl http://<Your_Host_IP_Address>:8888/v1/chatqna \
      -H 'Content-Type: application/json' \
      -d '{
        "query": "What is the capital of France?",
        "num_retrieval": 1
      }'
    ```
    Replace `<Your_Host_IP_Address>` with the actual IP.

## Important Notes

* **Hugging Face Token:** Remember to replace `your token` in the script with your actual Hugging Face token. Without it, the Llama 2 model download will fail.
* **First-Time Docker Compose:** If this is your first time running Docker Compose in your Lightning AI instance, you might need to restart your Lightning AI instance for full Docker permissions to take effect if you encounter any issues.
* **Model Size and GPU:** The `Llama-2-7b-chat-hf` model is chosen specifically for its compatibility with the 16GB VRAM of a T4 GPU. Attempting to run larger models on a T4 might lead to out-of-memory errors.
* **Troubleshooting:** If services fail to start, check the `docker logs <service_name>` for individual service logs.