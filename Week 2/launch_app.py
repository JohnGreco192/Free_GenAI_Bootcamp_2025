
import os
import subprocess
import time
import sys
from pyngrok import ngrok

# Add the project root to sys.path to allow internal imports if needed
# The notebook cell will change directory to yt_lang_app, so the root is "."
project_root = "." # Corrected project root
sys.path.insert(0, os.path.abspath(project_root))

print("Starting Streamlit app and Ngrok tunnel...")

# Set NGROK_AUTH_TOKEN from environment variables (passed from the calling cell)
NGROK_AUTH_TOKEN = os.environ.get("NGROK_AUTH_TOKEN")
if not NGROK_AUTH_TOKEN:
    print("Error: NGROK_AUTH_TOKEN not found in environment variables. Please set it in the calling cell!")
    sys.exit(1)

try:
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)
    print("Ngrok authentication token set.")
except Exception as e:
    print(f"Error setting Ngrok auth token: {e}")
    sys.exit(1)

# --- Start Streamlit in Background ---
streamlit_port = 8501 # Fixed port for Streamlit
# App path is now relative to the yt_lang_app directory
app_path = os.path.join("frontend", "app.py")

# NO LONGER CHANGE DIRECTORY *INSIDE* THE SCRIPT
# os.chdir("yt_lang_app") # Removed this line

print(f"Attempting to launch Streamlit app at: {app_path} on port {streamlit_port}")

streamlit_cmd = [
    "streamlit", "run", app_path,
    "--server.port", str(streamlit_port),
    "--server.enableCORS", "false",
    "--server.enableXsrfProtection", "false",
    "--browser.gatherUsageStats", "false",
    "--server.headless", "true"
]

# Start the streamlit process
streamlit_process = subprocess.Popen(
    streamlit_cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    bufsize=1,
    universal_newlines=True
)

print("Streamlit process started. Waiting for it to become ready...")

# Give Streamlit some time to start up
time.sleep(15)

# --- Create Ngrok Tunnel ---
try:
    print("Creating ngrok tunnel...")
    # Use the tunnel manager to avoid issues with multiple tunnels
    from pyngrok import conf
    conf.get_default().monitor_thread = False # Disable monitor thread to avoid hang in Colab
    public_url = ngrok.connect(streamlit_port)
    print(f"🎉 Streamlit App is Live! Access it at: {public_url}")
    # Fixed the unterminated string literal by removing the newline
    print("\nClick the link above to open your app.")
    print("Keep this cell running to keep the app active.")

    print("\n--- Streamlit Process Output (for debugging) ---")
    # Continuously read output until the process terminates or is interrupted
    while True:
        stdout_line = streamlit_process.stdout.readline()
        stderr_line = streamlit_process.stderr.readline()
        if stdout_line:
            print(f"STDOUT: {stdout_line.strip()}")
        if stderr_line:
            print(f"STDERR: {stderr_line.strip()}")

        if streamlit_process.poll() is not None:
            print("Streamlit process terminated unexpectedly. Check previous STDOUT/STDERR for errors.")
            break

        if not stdout_line and not stderr_line:
             # Wait a bit before checking again if no output
             time.sleep(0.5)


except Exception as e:
    print(f"Error setting up Ngrok tunnel: {e}")
    if streamlit_process.poll() is None:
        streamlit_process.terminate()
        streamlit_process.wait()
        print("Streamlit process terminated.")
# The calling notebook cell will handle changing back to /content
# finally:
#     os.chdir("/content") # Removed this line from the script
#     print("Changed directory back to /content.")

print("Launch script finished (if reached).") # This line might not be reached if the process runs indefinitely
