# start_tgi.py

import subprocess
import os
import time

# !!! WARNING: HARDCODING SENSITIVE INFORMATION IS NOT RECOMMENDED FOR PRODUCTION !!!
# For a secure deployment, use environment variables or a secrets manager.
HUGGING_FACE_HUB_TOKEN = "...YOUR HF TOKEN HERE..." # Replace with your actual Hugging Face token

# Configuration for the TGI server
MODEL_ID = "andrijdavid/Llama3-1B-Base" # Or "princeton-nlp/Sheared-LLaMA-2.7B-ShareGPT" if you prefer
TGI_PORT = 8080
VOLUME_NAME = "tgi_models" # This will create a docker volume or use an existing one

def start_tgi_server():
    print(f"--- Starting TGI Server for model: {MODEL_ID} ---")
    print(f"Model weights will be stored in Docker volume: {VOLUME_NAME}")

    # Ensure the Hugging Face token is available as an environment variable for Docker
    os.environ['HUGGING_FACE_HUB_TOKEN'] = HUGGING_FACE_HUB_TOKEN

    # Command to run the TGI Docker container
    # We're using `docker run -d` to run it in detached mode (background)
    # `-e HUGGING_FACE_HUB_TOKEN` passes the token to the container
    # `--mount type=volume,source=tgi_models,target=/data` creates/uses a Docker volume for persistence
    # Adjust --dtype based on your GPU capability and desired precision (float16 for L4 is good)
    docker_command = [
        "docker", "run", "-d",
        "--name", "tgi-server", # Give the container a name for easy management
        "--rm", # Automatically remove the container when it exits
        "--gpus", "all",
        "--shm-size", "1g",
        "-p", f"{TGI_PORT}:80", # Map host port to container port
        "--mount", f"type=volume,source={VOLUME_NAME},target=/data",
        "-e", f"HUGGING_FACE_HUB_TOKEN={HUGGING_FACE_HUB_TOKEN}", # Pass the token inside the container
        "ghcr.io/huggingface/text-generation-inference:latest", # TGI Docker image
        "--model-id", MODEL_ID,
        "--num-shard", "1",
        "--max-input-length", "1024",
        "--max-total-tokens", "2048",
        "--max-batch-total-tokens", "8192",
        "--dtype", "float16"
    ]

    try:
        # Check if a container with the same name already exists and is running
        check_command = ["docker", "ps", "-q", "-f", "name=tgi-server"]
        result = subprocess.run(check_command, capture_output=True, text=True, check=False)
        if result.stdout.strip():
            print("Container 'tgi-server' is already running. Skipping startup.")
            print(f"You can access TGI at http://127.0.0.1:{TGI_PORT}")
            return # Exit if already running

        # Check if a stopped container with the same name exists
        check_stopped_command = ["docker", "ps", "-aq", "-f", "name=tgi-server"]
        result_stopped = subprocess.run(check_stopped_command, capture_output=True, text=True, check=False)
        if result_stopped.stdout.strip():
            print("Stopped container 'tgi-server' found. Attempting to remove it...")
            subprocess.run(["docker", "rm", "tgi-server"], check=True)
            print("Removed existing stopped container.")

        # Execute the docker run command
        print(f"Running command: {' '.join(docker_command)}")
        process = subprocess.run(docker_command, check=True, capture_output=True, text=True)
        print("TGI Docker container started in detached mode.")
        print("It may take some time for the model to download and load.")
        print(f"You can check its logs with: docker logs {process.stdout.strip()}")
        print(f"TGI will be accessible at http://127.0.0.1:{TGI_PORT}")
        print("\n--- Waiting for TGI server to become ready (up to 120 seconds)... ---")

        # Basic health check: try to connect to the TGI endpoint
        start_time = time.time()
        while time.time() - start_time < 120: # Wait up to 2 minutes
            try:
                # Use requests for a quick HTTP check
                import requests
                response = requests.get(f"http://127.0.0.1:{TGI_PORT}/health", timeout=5)
                if response.status_code == 200:
                    print("\n--- TGI server is ready! ---")
                    return
            except requests.exceptions.ConnectionError:
                pass # Server not ready yet
            except Exception as e:
                print(f"Health check error: {e}")
            time.sleep(2) # Wait 2 seconds before retrying

        print("\n--- Warning: TGI server did not become ready within the timeout. ---")
        print("Please check Docker logs manually: `docker logs tgi-server`")
        print("And ensure the L4 GPU is allocated and working correctly.")

    except subprocess.CalledProcessError as e:
        print(f"Error starting TGI Docker container: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
    except FileNotFoundError:
        print("Error: 'docker' command not found. Please ensure Docker is installed and in your PATH.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    start_tgi_server()