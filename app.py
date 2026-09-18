import os
import streamlit as st
import requests

# Page configuration
st.set_page_config(page_title="Hub API Chat", page_icon="🧠", layout="centered")

# Čita Docker adresu ili se vraća na localhost za lokalno pokretanje
API_STREAM_URL = os.getenv("API_STREAM_URL", "http://localhost:8000/api/v1/query-stream")

st.title("🧠 Hub Assistant")
st.caption("Ask a question and receive answers based on internal company documents.")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages from session memory
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User prompt input
if prompt := st.chat_input("Write your question here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        def stream_generator():
            try:
                response = requests.post(
                    API_STREAM_URL,
                    json={"question": prompt},
                    stream=True,
                    timeout=30
                )
                if response.status_code == 200:
                    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                        if chunk:
                            yield chunk
                else:
                    yield f"❌ Server error: {response.status_code}"
            except Exception as e:
                yield f"❌ Connection error: {str(e)}"

        # st.write_stream automatically renders word-by-word and returns the full response text
        full_response = st.write_stream(stream_generator())
        st.session_state.messages.append({"role": "assistant", "content": full_response})