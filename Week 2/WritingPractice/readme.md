**Concise Summary:** A Streamlit application for practicing Japanese sentence writing. It provides English sentences based on a vocabulary list and allows users to practice writing the corresponding Japanese sentence via mouse drawing or a multiple-choice option, with simulated grading.

## Setup and Running

This project can be run both in Google Colab and locally.

### Prerequisites

*   Python 3.7+
*   For running in Colab: Google API Key and ngrok Authentication Token added to Colab Secrets.
*   For running locally: Google API Key and ngrok Authentication Token added to the `env.txt` file in the project directory.

### Running in Google Colab

1.  **Upload Files:** Upload all project files (`app.py`, `env.txt`, `requirements.txt`, `simple_drawing_app.py`, `execute.py`, `colab_execute.py`, `readme.md`) to the `/content` directory in your Colab session.
2.  **Set Secrets:** Ensure your Google API Key (`GOOGLE_API_KEY`) and ngrok Authentication Token (`NGROK_AUTH_TOKEN`) are set in Colab's Secrets manager (accessed via the "🔑" icon in the left sidebar). These are used by `colab_execute.py`.
3.  **Install Dependencies:** Run the following command in a Colab code cell:

    (You may also need to install `streamlit`, `pyngrok`, `python-dotenv`, and `streamlit-drawable-canvas` if they are not included in `requirements.txt` or already installed).
4.  **Run the App:** In a Colab code cell, navigate to the project directory (`%cd /content` if needed) and run the `colab_execute.py` script:

