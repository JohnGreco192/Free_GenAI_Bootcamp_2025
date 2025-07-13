# start_tgi.py

import subprocess
import os
import time

# !!! WARNING: HARDCODING SENSITIVE INFORMATION IS NOT RECOMMENDED FOR PRODUCTION !!!
# For a secure deployment, use environment variables or a secrets manager.
HUGGING_FACE_HUB_TOKEN = "yourtoken"

# Configuration for the TGI server - NOW USING A LARGER, INSTRUCT-TUNED MODEL
MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"
TGI_PORT = 8080
VOLUME_NAME = "tgi_models_llama3_8b" # Using a new volume for the larger model

def start_tgi_server():
    print(f"--- Starting TGI Server for model: {MODEL_ID} ---")
    print(f"Model weights will be stored in Docker volume: {VOLUME_NAME}")

    # Ensure the Hugging Face token is available as an environment variable for Docker
    os.environ['HUGGING_FACE_HUB_TOKEN'] = HUGGING_FACE_HUB_TOKEN

    # Command to run the TGI Docker container
    docker_command = [
        "docker", "run", "-d",
        "--name", "tgi-server-large", # New container name to avoid conflicts
        #"--rm",
        "--gpus", "all",
        "--shm-size", "1g",
        "-p", f"{TGI_PORT}:80",
        "--mount", f"type=volume,source={VOLUME_NAME},target=/data",
        "-e", f"HUGGING_FACE_HUB_TOKEN={HUGGING_FACE_HUB_TOKEN}",
        "ghcr.io/huggingface/text-generation-inference:latest",
        "--model-id", MODEL_ID,
        "--num-shard", "1",
        "--max-input-length", "1024",
        "--max-total-tokens", "2048",
        "--max-batch-total-tokens", "8192",
        "--dtype", "float16"
    ]

    try:
        # Check if a container with the new name already exists and is running
        check_command = ["docker", "ps", "-q", "-f", "name=tgi-server-large"]
        result = subprocess.run(check_command, capture_output=True, text=True, check=False)
        if result.stdout.strip():
            print("Container 'tgi-server-large' is already running. Stopping and removing it to start fresh.")
            subprocess.run(["docker", "stop", "tgi-server-large"], check=True)
            print("Stopped existing container.")


        # Execute the docker run command
        print(f"Running command: {' '.join(docker_command)}")
        process = subprocess.run(docker_command, check=True, capture_output=True, text=True)
        container_id = process.stdout.strip()
        print("TGI Docker container started in detached mode.")
        print(f"It may take some time for the model to download and load (Llama-3-8B is about 16GB).")
        print(f"You can check its logs with: docker logs {container_id}")
        print(f"TGI will be accessible at http://127.0.0.1:{TGI_PORT}")
        print("\n--- Waiting for TGI server to become ready (this can take several minutes)... ---")

        # Basic health check
        start_time = time.time()
        while time.time() - start_time < 300: # Wait up to 5 minutes for the larger model
            try:
                import requests
                response = requests.get(f"http://127.0.0.1:{TGI_PORT}/health", timeout=5)
                if response.status_code == 200:
                    print("\n--- TGI server is ready! ---")
                    return
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(5)

        print("\n--- Warning: TGI server did not become ready within the timeout. ---")
        print("Please check Docker logs manually: `docker logs tgi-server-large`")

    except subprocess.CalledProcessError as e:
        print(f"Error starting TGI Docker container: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
    except FileNotFoundError:
        print("Error: 'docker' command not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    start_tgi_server()