import streamlit as st
import requests
import json

st.title("Vocab JSON Generator (Groq Llama 3)")

prompt = st.text_area(
    "Describe the vocab you want (e.g., '10 Quebec French food words')",
    value="Generate 10 Quebec French food words as a JSON array. Each object should have: \"french_word\", \"quebec_pronunciation\", \"english\", and \"parts\" (an object with at least a \"notes\" field)."
)

groq_api_key = "Your Groq Key here"
groq_url = "https://api.groq.com/openai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {groq_api_key}",
    "Content-Type": "application/json"
}

if st.button("Generate JSON"):
    if not groq_api_key or "YOUR_GROQ_API_KEY" in groq_api_key:
        st.error("Please set your Groq API key in the script.")
    elif prompt:
        data = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that only responds with valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1024,
            "temperature": 0.2
        }
        try:
            response = requests.post(groq_url, headers=headers, json=data, timeout=60)
            if response.ok:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                st.subheader("Raw JSON Output")
                st.code(content, language="json")
                try:
                    vocab = json.loads(content)
                    st.success("Valid JSON!")
                except Exception as e:
                    st.error(f"Response is not valid JSON: {e}")
            else:
                st.error(f"Groq API error: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Request failed: {e}")
    else:
        st.warning("Please enter a prompt.")