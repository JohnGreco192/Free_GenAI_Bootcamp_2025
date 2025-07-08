# OPEA Megaservice for LLM Inference with TGI

This project demonstrates setting up an **OPEA (Open Platform for Enterprise AI) Megaservice** specifically designed for serving a Large Language Model (LLM) efficiently. It leverages **Hugging Face's Text Generation Inference (TGI)** as the high-performance backend and is optimized for deployment in **Lightning AI Studios** with **NVIDIA L4 GPUs**.

---

## Project Overview

This setup orchestrates three main Python components to create a robust LLM serving pipeline:

### 1. TGI Server Launcher (`start_tgi.py`)
This script is responsible for launching and managing the **Hugging Face Text Generation Inference (TGI)** Docker container. TGI is the core engine that loads the LLM onto your GPU and handles the actual text generation.
* It spins up a TGI Docker container in detached mode (`-d`).
* It handles model downloading and caching using a Docker volume (`tgi_models`).
* It passes the Hugging Face token and configures TGI parameters (e.g., `max_new_tokens`, `dtype=float16`).
* It performs a basic health check to confirm the TGI server is ready.
* **Initial Model:** `andrijdavid/Llama3-1B-Base` (can be changed to `meta-llama/Llama-3-8B-Instruct` or others).

### 2. LLM Microservice (`llm_microservice_app.py`)
This component acts as an **OPEA-compliant Microservice**. Its primary role is to bridge communication between the higher-level Megaservice and the TGI server. It functions as a client to the TGI server, responsible for:
* Receiving LLM-related requests (following the `ChatCompletionRequest` protocol) from the Megaservice.
* Formatting these requests into a compatible payload for the TGI `/generate` API endpoint.
* Sending the formatted requests to the TGI server (defaulting to `http://127.0.0.1:8080`).
* Processing and returning the TGI's generated responses back to the Megaservice, including token usage information.
* **Exposed Endpoint:** `/v1/chat/completions` (to the Megaservice).

### 3. OPEA Megaservice (`appLLMonly.py`)
This is the **orchestrator service** and the primary public-facing component of this project. It exposes the main API endpoint for LLM interactions. It uses `comps.ServiceOrchestrator` to manage the flow to the `LLM Microservice`.
* It defines and exposes the public API endpoint (`/v1/chat/completions`).
* It receives incoming user requests (e.g., from `curl`).
* It forwards these requests to the `LLM Microservice` using the OPEA `ServiceOrchestrator.schedule` method.
* It processes the responses received from the `LLM Microservice` and formats them into an OpenAI-compatible `ChatCompletionResponse` before returning them to the end-user.

---

## Current Status and Environment

This setup has been successfully configured and tested, with all services communicating correctly. The TGI server is operational and ready for inference requests.

### Hardware Considerations
* This project is specifically configured for **Lightning AI Studios with an NVIDIA L4 GPU**.
* **NVIDIA L4 GPUs (with 24GB VRAM)** are essential for efficient LLM inference with TGI, as they provide significant acceleration over CPUs or lower-end GPUs (like T4s).
* **Attempting to run TGI with `--gpus all` on a CPU-only instance will result in an error.** Ensure your Lightning AI Studio has an L4 GPU allocated.

### Prerequisites
Before running this project, ensure you have the following:

* **Lightning AI Studio:** Access to a Lightning AI Studio environment with at least one **NVIDIA L4 GPU** allocated.
* **Docker:** Docker must be installed and running within your Lightning AI Studio. (This is typically pre-configured in Lightning AI environments).
* **Python Dependencies:** The necessary Python libraries (e.g., `comps`, `fastapi`, `uvicorn`, `requests`, `pydantic`) are generally managed and available through your `miniconda3/envs/cloudspace` environment within Lightning AI.
* **Hugging Face User Access Token:** A Hugging Face token with read access for gated models (like Llama 3). This token needs to be directly placed in `start_tgi.py`. **Do NOT hardcode tokens in production environments; use environment variables or a secrets manager for secure deployments.**

---

## Project Structure

Your project directory should be organized as follows within your Lightning AI Studio:
.lightning_studio/OPEA/megaservice/
├── start_tgi.py                 # Script to start the TGI Docker container
├── llm_microservice_app.py      # OPEA LLM Microservice (TGI client)
└── appLLMonly.py                # OPEA Megaservice (Orchestrator)

---

## Instructions to Run the Project

To run this project, you will need **at least three separate terminal windows or tabs** within your Lightning AI Studio. Each component will run in its own dedicated terminal.

### Step 1: Start the TGI Server

This step launches the TGI Docker container and initiates the download and loading of the LLM.

1.  **Open Terminal 1.**
2.  **Navigate to the project directory:**
    ```bash
    cd /teamspace/studios/this_studio/.lightning_studio/OPEA/megaservice/
    ```
3.  **IMPORTANT: Before running, edit `start_tgi.py` and replace `"...YOUR HF TOKEN HERE..."` with your actual Hugging Face User Access Token.**
4.  **Run the TGI server launcher script:**
    ```bash
    python start_tgi.py
    ```
5.  **Wait for the confirmation message:**
    ```
    --- TGI server is ready! ---
    ```
    * **Note:** The first time you run this, it will download the TGI Docker image and the LLM weights (to the `tgi_models` Docker volume), which can take several minutes depending on the model size and your network speed. You can monitor its progress by opening a new terminal (Terminal 4) and running `docker logs tgi-server`.
    * TGI will be accessible internally at `http://127.0.0.1:8080`.
6.  **Keep this terminal running.**

### Step 2: Start the LLM Microservice

This service acts as the crucial bridge between your Megaservice and the TGI server.

1.  **Open Terminal 2.**
2.  **Navigate to the project directory:**
    ```bash
    cd /teamspace/studios/this_studio/.lightning_studio/OPEA/megaservice/
    ```
3.  **Run the LLM microservice:**
    ```bash
    python llm_microservice_app.py
    ```
4.  **Confirm it starts:** Look for output indicating it's listening on `http://0.0.0.0:9000`.
5.  **Keep this terminal running.**

### Step 3: Start the OPEA Megaservice

This is the main orchestrator service that exposes the public API endpoint for your LLM.

1.  **Open Terminal 3.**
2.  **Navigate to the project directory:**
    ```bash
    cd /teamspace/studios/this_studio/.lightning_studio/OPEA/megaservice/
    ```
3.  **Run the Megaservice:**
    ```bash
    python appLLMonly.py
    ```
4.  **Confirm it starts:** Look for output indicating it's listening on `http://0.0.0.0:7000`.
5.  **Keep this terminal running.**

### Step 4: Send a Request to the Megaservice

Once all three services are running in their respective terminals, you can send a test API request.

1.  **Open any available terminal** (e.g., Terminal 3 after `appLLMonly.py` has started, or a new Terminal 4).
2.  **Send the `curl` request:**
    ```bash
    curl -X POST \
      [http://0.0.0.0:7000/v1/chat/completions](http://0.0.0.0:7000/v1/chat/completions) \
      -H 'Content-Type: application/json' \
      -d '{
        "messages": [
          {"role": "user", "content": "Tell me a fun fact about cats."}
        ],
        "model": "your-llm-model-name",
        "stream": false
      }'
    ```
    * The `model` field in the `curl` request is primarily for logging/identification purposes in this setup; the actual model used is configured in `start_tgi.py`.
3.  **Observe the output:** Check the response in the terminal where you sent the `curl` command. Also, observe the logs in your `llm_microservice_app.py` and `tgi.py` terminals to see the request flow and TGI's generation process.

---

## Possible Next Steps and Considerations

The initial setup uses `andrijdavid/Llama3-1B-Base`, which is a base model. Base models are trained for raw text completion and often produce less coherent or "junk" output when given conversational instructions.

### 1. Using a Larger, Instruct-Tuned Model (Recommended)

To achieve coherent, conversational responses and actual "fun facts," you need to switch to an **instruct-tuned model**.

**Recommendation:** Switch to `meta-llama/Llama-3-8B-Instruct`. This model is explicitly fine-tuned for following instructions and chat, making it ideal for your `curl` query. Your **L4 GPU (24GB VRAM) is capable of handling this model effectively with TGI.**

**How to switch:**

1.  **Stop the `tgi.py` script** (usually by pressing `CTRL+C` in Terminal 1).
2.  **Edit `start_tgi.py`** and change the `MODEL_ID` parameter from `andrijdavid/Llama3-1B-Base` to `meta-llama/Llama-3-8B-Instruct`.
3.  **Save `start_tgi.py`.**
4.  **Restart `start_tgi.py`** in Terminal 1:
    ```bash
    python start_tgi.py
    ```
    This will trigger a new download and loading process for the larger 8B Instruct model, which will take longer than the 1B base model.
5.  **Once TGI is ready, re-send your `curl` request.**

### 2. Exploring Smaller Models (for specific use cases or resource constraints)

If `meta-llama/Llama-3-8B-Instruct` proves too resource-intensive for future needs or if you want to experiment, you could look for other smaller instruct-tuned models, perhaps in the 2-4 billion parameter range. However, for general utility and conversational quality, 8B instruct models usually offer a good balance of size and capability.

**Search criteria:** Look for models with "instruct," "chat," or "fine-tuned" in their names on Hugging Face that are based on Llama 3 or similar architectures.

### 3. Understanding Model Prompting

With an instruct-tuned model like Llama 3 Instruct, the `llm_microservice_app.py` can be further enhanced to format the messages correctly according to the model's specific chat template (e.g., using special tokens for user and assistant turns). While the current setup simply sends the user's content and often works for instruct models, explicit templating can often improve response quality and adherence to instructions.