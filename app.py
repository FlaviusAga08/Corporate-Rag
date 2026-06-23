import re
import streamlit as st
from utils.api_client import RAGClient, APIError

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Corporate RAG",
    page_icon="📚",
    layout="centered",
)

# ── Session defaults ───────────────────────────────────────────────────────────
defaults = {
    "authenticated": False,
    "username": "",
    "token": "",
    "server_url": "http://localhost:8000",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Helpers ────────────────────────────────────────────────────────────────────
def _client() -> RAGClient:
    return RAGClient(st.session_state.server_url, st.session_state.token)


def _is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def _logout():
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.token = ""


# ── Auth page ──────────────────────────────────────────────────────────────────
def show_auth_page():
    st.markdown(
        "<h1 style='text-align:center; margin-bottom:0'>📚 Corporate RAG</h1>"
        "<p style='text-align:center; color:gray; margin-top:4px'>Sistem de răspuns la întrebări corporative</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # Server URL input
    with st.expander("Setări server", expanded=False):
        url = st.text_input("URL server", value=st.session_state.server_url)
        if url != st.session_state.server_url:
            st.session_state.server_url = url

        client = RAGClient(st.session_state.server_url)
        if client.is_reachable():
            st.success("Server accesibil.")
        else:
            st.error("Serverul nu este accesibil. Verifică URL-ul și asigură-te că serverul rulează.")

    tab_login, tab_register = st.tabs(["Autentificare", "Cont nou"])

    # ── Login ──────────────────────────────────────────────────────────────────
    with tab_login:
        with st.form("login_form"):
            identifier = st.text_input("Utilizator sau email")
            password = st.text_input("Parolă", type="password")
            submitted = st.form_submit_button("Intră în cont", use_container_width=True)

        if submitted:
            if not identifier or not password:
                st.error("Completează toate câmpurile.")
            else:
                try:
                    token, username = _client().login(identifier, password)
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.token = token
                    st.rerun()
                except APIError as e:
                    st.error(e.detail)
                except Exception:
                    st.error("Nu s-a putut conecta la server.")

    # ── Register ───────────────────────────────────────────────────────────────
    with tab_register:
        with st.form("register_form"):
            new_username = st.text_input("Nume utilizator")
            new_email = st.text_input("Adresă email")
            new_password = st.text_input("Parolă", type="password")
            confirm_password = st.text_input("Confirmă parola", type="password")
            submitted_reg = st.form_submit_button("Creează cont", use_container_width=True)

        if submitted_reg:
            if not all([new_username, new_email, new_password, confirm_password]):
                st.error("Completează toate câmpurile.")
            elif len(new_username) < 3:
                st.error("Numele de utilizator trebuie să aibă cel puțin 3 caractere.")
            elif not _is_valid_email(new_email):
                st.error("Adresa de email nu este validă.")
            elif len(new_password) < 8:
                st.error("Parola trebuie să aibă cel puțin 8 caractere.")
            elif new_password != confirm_password:
                st.error("Parolele nu coincid.")
            else:
                try:
                    message = _client().register(new_username, new_email, new_password)
                    st.success(message + " Poți să te autentifici acum.")
                except APIError as e:
                    st.error(e.detail)
                except Exception:
                    st.error("Nu s-a putut conecta la server.")


# ── Main app ───────────────────────────────────────────────────────────────────
def show_main_app():
    client = _client()

    st.sidebar.markdown(f"**Bun venit, {st.session_state.username}!**")
    st.sidebar.caption(f"Server: `{st.session_state.server_url}`")
    if st.sidebar.button("Deconectare"):
        _logout()
        st.rerun()

    st.sidebar.divider()
    st.sidebar.title("Încarcă documente")

    uploaded_files = st.sidebar.file_uploader(
        "PDF / DOCX",
        type=["pdf", "docx"],
        accept_multiple_files=True,
    )

    if uploaded_files and st.sidebar.button("Încarcă fișierele"):
        files = [(f.name, f.read(), f.type or "application/octet-stream") for f in uploaded_files]
        try:
            saved = client.upload_documents(files)
            st.sidebar.success(f"{len(saved)} fișier(e) încărcat(e).")
        except APIError as e:
            st.sidebar.error(e.detail)

    if st.sidebar.button("Procesează documentele"):
        with st.spinner("Procesare în curs..."):
            try:
                count = client.process_documents()
                st.sidebar.success(f"{count} document(e) procesate și stocate.")
            except APIError as e:
                st.sidebar.error(e.detail)

    # ── Query ──────────────────────────────────────────────────────────────────
    st.title("📚 Corporate RAG")
    st.write("Pune o întrebare pe baza documentelor încărcate.")

    query = st.text_input("Întrebarea ta:")
    if query:
        with st.spinner("Generez răspunsul..."):
            try:
                answer = client.query(query)
                st.markdown("**Răspuns:**")
                st.write(answer)
            except APIError as e:
                st.error(e.detail)
            except Exception:
                st.error("Eroare de comunicare cu serverul.")


# ── Router ─────────────────────────────────────────────────────────────────────
if st.session_state.authenticated:
    show_main_app()
else:
    show_auth_page()
