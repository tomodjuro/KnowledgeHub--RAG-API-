import os
import streamlit as st
import requests

# Dynamic API host resolution (defaults to localhost for Windows, uses 'api' in Docker)
API_HOST = os.getenv("API_HOST", "localhost")
API_STREAM_URL = f"http://{API_HOST}:8000/api/v1/query-stream"
API_DOCS_URL = f"http://{API_HOST}:8000/api/v1/documents"
API_REINDEX_URL = f"http://{API_HOST}:8000/api/v1/reindex"

# Page configuration
st.set_page_config(page_title="Hub API Chat", page_icon="🧠", layout="centered")

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

        full_response = st.write_stream(stream_generator())
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# Sidebar - Knowledge Base Management
st.sidebar.title("Knowledge Base")

if st.sidebar.button("Show Loaded Documents"):
    try:
        response = requests.get(API_DOCS_URL, timeout=5)
        if response.status_code == 200:
            docs = response.json().get("documents", [])
            st.sidebar.write(f"**Total Documents ({len(docs)}):**")
            for doc in docs:
                st.sidebar.write(f"- `{doc}`")
        else:
            st.sidebar.error(f"API Error ({response.status_code}): {response.text}")
    except Exception as e:
        st.sidebar.error(f"Error details: {type(e).__name__} - {str(e)}")

st.sidebar.divider()
st.sidebar.caption("If a file you just added to `docs/` isn't showing up yet, force a full resync below (this doesn't require the folder watcher to be running).")

if st.sidebar.button("🔄 Reindex All Documents"):
    try:
        response = requests.post(API_REINDEX_URL, timeout=5)
        if response.status_code == 202:
            st.sidebar.success("Reindexing started in the background. Give it a few seconds, then check 'Show Loaded Documents' again.")
        else:
            st.sidebar.error(f"API Error ({response.status_code}): {response.text}")
    except Exception as e:
        st.sidebar.error(f"Error details: {type(e).__name__} - {str(e)}")