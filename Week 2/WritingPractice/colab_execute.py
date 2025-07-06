from pyngrok import ngrok
import os
import subprocess
import threading
import time
from google.colab import userdata # Import userdata

# Retrieve Ngrok auth token from Colab secrets
NGROK_AUTH_TOKEN = userdata.get("NGROK_AUTH_TOKEN") # Use userdata.get()
# Retrieve Google API key from Colab secrets to pass as environment variable
# Assuming GOOGLE_API_KEY is still in Colab secrets for this original setup
GOOGLE_API_KEY = userdata.get("GOOGLE_API_KEY")


print(f"DEBUG: NGROK_AUTH_TOKEN retrieved from secrets: {NGROK_AUTH_TOKEN is not None}")
print(f"DEBUG: GOOGLE_API_KEY retrieved from secrets: {GOOGLE_API_KEY is not None}")


if not NGROK_AUTH_TOKEN:
    print("Error: NGROK_AUTH_TOKEN is not set in Colab secrets. Please configure it.")
elif not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY is not set in Colab secrets. Please configure it.")
else:
    # Authenticate Ngrok
    try:
        ngrok.set_auth_token(NGROK_AUTH_TOKEN)
        print("Ngrok authentication token set.")
    except Exception as e:
         print(f"Error authenticating Ngrok: {e}")
         print("Please check your NGROK_AUTH_TOKEN in Colab secrets.")
         pass


    # Set the GOOGLE_API_KEY environment variable in the current process
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    print(f"DEBUG: GOOGLE_API_KEY set as environment variable in main process: {os.environ.get('GOOGLE_API_KEY') is not None}")


    # Function to run Streamlit in a separate thread
    def run_streamlit():
        # Command to run Streamlit, assuming app.py is in /content
        cmd = ["streamlit", "run", "app.py", "--server.port", "8501", "--server.enableCORS", "false", "--server.enableXsrfProtection", "false"]
        # Explicitly set the working directory for the subprocess to /content
        streamlit_cwd = "/content"
        print(f"DEBUG: Running Streamlit command: {' '.join(cmd)} in directory: {streamlit_cwd}")

        # Use text=True for capturing output as text
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=os.environ, text=True, cwd=streamlit_cwd)

        # Read and print output from the Streamlit process
        stdout, stderr = process.communicate()
        if stdout:
            print(f"[Streamlit STDOUT]:\n{stdout.strip()}")
        if stderr:
            print(f"[Streamlit STDERR]:\n{stderr.strip()}")


        process.wait() # Wait for the process to terminate
        print("[Streamlit Process Exited]")


    # Start Streamlit in a new daemon thread
    streamlit_thread = threading.Thread(target=run_streamlit)
    streamlit_thread.daemon = True
    streamlit_thread.start()
    print("Streamlit app initiated in background on port 8501.")

    # Allow Streamlit server to start up
    time.sleep(10) # Keep sleep time


    # Establish Ngrok tunnel to the Streamlit port
    try:
         # Check if a tunnel is already running on this port
        tunnels = ngrok.get_tunnels()
        port = 8501 # Define port for clarity
        for tunnel in tunnels:
             tunnel_addr = tunnel.config.get('addr')
             if tunnel_addr and f":{tunnel_addr.split(':')[-1]}" == f":{port}":
                 print(f"Closing existing tunnel on port {port}: {tunnel.public_url}")
                 ngrok.disconnect(tunnel.public_url)
             elif tunnel.public_url.startswith(("http://", "https://")) and tunnel_addr and f":{tunnel_addr.split(':')[-1]}" == f":{port}":
                  print(f"Closing existing HTTP/S tunnel on port {port}: {tunnel.public_url}")
                  ngrok.disconnect(tunnel.public_url)

        # Re-establish the tunnel
        public_url = ngrok.connect(port)
        print(f"Ngrok tunnel established. Access your Streamlit app at: {public_url}")
    except Exception as e:
        print(f"Failed to establish Ngrok tunnel: {e}")
        print(f"Verify Streamlit is running on port {port} and your NGROK_AUTH_TOKEN in Colab secrets.")
        print("Also ensure app.py exists in the correct directory.")

# Keep the main thread alive if needed (usually not necessary in Colab for background processes)
# while streamlit_thread.is_alive():
#     time.sleep(1)
