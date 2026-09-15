import streamlit as st
import requests

# Konfiguracija stranice
st.set_page_config(page_title="Hub Api Chat", page_icon="🧠", layout="centered")

API_STREAM_URL = "http://localhost:8000/api/v1/query-stream"

st.title("🧠 Hub Assistant")
st.caption("Postavite pitanje i dobit ćete odgovor na temelju internih dokumenata iz tvrtke.")

# Inicijalizacija povijesti razgovora u session state-u
if "messages" not in st.session_state:
    st.session_state.messages = []

# Prikaz svih prethodnih poruka iz memorije sesije
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Unos novog pitanja od strane korisnika
if prompt := st.chat_input("Napišite vaše pitanje ovdje..."):
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
                    yield f"❌ Greška na poslužitelju: {response.status_code}"
            except Exception as e:
                yield f"❌ Greška u spajanju: {str(e)}"

        # st.write_stream automatski ispisuje riječ po riječ i vraća puni tekst
        full_response = st.write_stream(stream_generator())
        st.session_state.messages.append({"role": "assistant", "content": full_response})