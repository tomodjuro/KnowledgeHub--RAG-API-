import streamlit as st
import requests

# Konfiguracija stranice
st.set_page_config(page_title="Hub Api Chat", page_icon="🧠", layout="centered")

API_QUERY_URL = "http://localhost:8000/api/v1/query"

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
    # Prikaz korisničkog pitanja u chatu
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Slaganje odgovora od strane API-ja
    with st.chat_message("assistant"):
        with st.spinner("Pretražujem dokumente i generiram odgovor..."):
            try:
                response = requests.post(
                    API_QUERY_URL,
                    json={"question": prompt},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "Nema odgovora.")
                    sources = data.get("sources", [])

                    # Oblikovanje konačnog odgovora s izvorima
                    full_response = answer
                    if sources:
                        full_response += "\n\n**Izvori:**\ degradation"
                        for src in sources:
                            full_response += f"\n* `{src}`"

                    st.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    error_msg = f"Greška poslužitelja (Status: {response.status_code})"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

            except requests.exceptions.ConnectionError:
                error_msg = "❌ Nije moguće uspostaviti vezu s DocuBrain API-jem. Provjerite je li FastAPI server pokrenut (`uvicorn main:app`)."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                error_msg = f"Došlo je do neočekivane greške: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})