#!/bin/bash
# This script is designed to be run directly in the Lightning AI terminal
# from the root directory of your project (where this opea.sh file is located).

echo "--- Starting OPEA ChatQnA NVIDIA GPU setup script (T4 auto-configured with Llama 2 7B) ---"

# Define base directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
OPEA_GENAI_EXAMPLES_DIR="${SCRIPT_DIR}/GenAIExamples"
NVIDIA_COMPOSE_DIR="${OPEA_GENAI_EXAMPLES_DIR}/ChatQnA/docker_compose/nvidia/gpu"

# --- 1. Clone GenAIExamples Repository ---
echo "--- Cloning GenAIExamples repository (if not already cloned) ---"
if [ ! -d "${OPEA_GENAI_EXAMPLES_DIR}" ]; then
  git clone https://github.com/opea-project/GenAIExamples.git || { echo "Failed to clone GenAIExamples. Exiting."; exit 1; }
else
  echo "GenAIExamples directory already exists. Skipping clone."
fi

# Go to the correct directory for the NVIDIA GPU setup
echo "--- Changing to Docker Compose directory for NVIDIA GPU: ${NVIDIA_COMPOSE_DIR} ---"
if [ ! -d "$NVIDIA_COMPOSE_DIR" ]; then
  echo "Error: NVIDIA Docker Compose directory not found at $NVIDIA_COMPOSE_DIR. Exiting."
  exit 1
fi
cd "$NVIDIA_COMPOSE_DIR" || { echo "Failed to change directory to $NVIDIA_COMPOSE_DIR. Exiting."; exit 1; }
echo "Current working directory: $(pwd)"

# --- 2. Source OPEA's default environment variables ---
# This typically sets EMBEDDING_MODEL_ID, RERANK_MODEL_ID, etc.
echo "--- Sourcing OPEA's default environment variables (if set_env.sh exists) ---"
if [ -f "./set_env.sh" ]; then
  source ./set_env.sh
  echo "set_env.sh sourced."
else
  echo "Warning: set_env.sh not found. Proceeding with hardcoded defaults."
fi

# --- 3. Set Custom Environment Variables for the shell and create .env for Docker Compose ---
echo "--- Setting Custom Environment Variables for shell and creating .env for Docker Compose ---"

# Define your Hugging Face Token (REQUIRED for Llama models)
# IMPORTANT: Ensure you have access to the selected Llama model on Hugging Face.
export HF_TOKEN="your token" # Replace with your actual token if different
export host_ip=$(hostname -I | awk '{print $1}')

# Define proxy settings if you are in a proxy environment (uncomment and set if needed)
# export http_proxy="Your_HTTP_Proxy"
# export https_proxy="Your_HTTPs_Proxy"

# Define no_proxy (add your internal services and host_ip here)
export no_proxy="localhost,127.0.0.1,${host_ip},chatqna-ui-server,chatqna-backend-server,dataprep-redis-service,tei-embedding-service,retriever,tei-reranking-service,tgi-service"

# Model ID changed to Llama 2 7B, which is more likely to fit on a T4 GPU (16GB VRAM)
export LLM_MODEL_ID="meta-llama/Llama-2-7b-chat-hf"
export EMBEDDING_MODEL_ID="${EMBEDDING_MODEL_ID:-BAAI/bge-base-en-v1.5}" # Use existing if sourced, else default
export RERANK_MODEL_ID="${RERANK_MODEL_ID:-BAAI/bge-reranker-base}"     # Use existing if sourced, else default
export INDEX_NAME="${INDEX_NAME:-rag-index}" # Default index name
export LOGFLAG="${LOGFLAG:-false}" # Default logging flag

# NGINX Port (default to 80 for easy access if not set)
export NGINX_PORT="${NGINX_PORT:-80}"

# Endpoints for UI to connect to backend services
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888"
export DATAPREP_SERVICE_ENDPOINT="http://${host_ip}:6007"


# Create a .env file in the current directory for Docker Compose
# This is crucial for Docker Compose to pick up these variables reliably.
cat << EOF > .env
HF_TOKEN="${HF_TOKEN}"
LLM_MODEL_ID="${LLM_MODEL_ID}"
EMBEDDING_MODEL_ID="${EMBEDDING_MODEL_ID}"
RERANK_MODEL_ID="${RERANK_MODEL_ID}"
INDEX_NAME="${INDEX_NAME}"
LOGFLAG="${LOGFLAG}"
host_ip="${host_ip}"
no_proxy="${no_proxy}"
NGINX_PORT="${NGINX_PORT}"
BACKEND_SERVICE_ENDPOINT="${BACKEND_SERVICE_ENDPOINT}"
DATAPREP_SERVICE_ENDPOINT="${DATAPREP_SERVICE_ENDPOINT}"
# If you are using proxies, uncomment and set them here:
# http_proxy="${http_proxy}"
# https_proxy="${https_proxy}"
EOF

echo ".env file created with necessary variables."

# --- AUTO-CONFIGURING TEI RERANKING SERVICE FOR T4 GPU ---
echo "--- Auto-configuring tei-reranking-service for NVIDIA T4 GPU (Compute Capacity 7.5) ---"
# This command replaces the default A100/A30 image with the T4-specific image.
sed -i 's|image: ghcr.io/huggingface/text-embeddings-inference:1.5|image: ghcr.io/huggingface/text-embeddings-inference:turing-1.5|g' compose.yaml || \
{ echo "Error: Failed to auto-configure tei-reranking-service image. Exiting."; exit 1; }
echo "tei-reranking-service image updated for T4."


# --- 4. Start the main GenAI example using Docker Compose ---
echo "--- Starting Docker Compose services ---"
# Check if compose.yaml exists before trying to run it
if [ ! -f "compose.yaml" ]; then
  echo "Error: 'compose.yaml' not found in current directory: $(pwd). Exiting."; exit 1;
fi
docker compose -f compose.yaml up -d || { echo "Failed to start Docker Compose services. Exiting."; exit 1; }

echo "--- OPEA ChatQnA NVIDIA GPU setup script finished ---"
echo " "
echo "You can monitor the service logs with: docker logs tgi-service"
echo "Wait for 'Connected' in the TGI logs before trying to consume services."
echo " "
echo "To access the UI, open http://${host_ip}:${NGINX_PORT} in your browser (default NGINX_PORT is 80)."
echo "For direct ChatQnA service interaction, use: curl http://${host_ip}:8888/v1/chatqna"
echo "Remember to restart your Lightning AI instance for full Docker permissions if this is your first time running Docker Compose."
