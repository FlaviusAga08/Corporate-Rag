import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox

from utils.api_client import RAGClient, APIError

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

DEFAULT_SERVER = "http://192.168.0.137:8000"


# ── Register dialog ────────────────────────────────────────────────────────────

class RegisterDialog(ctk.CTkToplevel):
    def __init__(self, parent, client: RAGClient):
        super().__init__(parent)
        self.client = client
        self.title("Creare cont")
        self.geometry("400x460")
        self.resizable(False, False)
        self.after(100, self.grab_set)
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Cont nou", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(28, 16))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=36)

        ctk.CTkLabel(form, text="Nume utilizator", anchor="w").pack(fill="x")
        self._username = ctk.CTkEntry(form, placeholder_text="min. 3 caractere")
        self._username.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(form, text="Adresă email", anchor="w").pack(fill="x")
        self._email = ctk.CTkEntry(form, placeholder_text="adresa@email.com")
        self._email.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(form, text="Parolă", anchor="w").pack(fill="x")
        self._password = ctk.CTkEntry(form, show="•", placeholder_text="min. 8 caractere")
        self._password.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(form, text="Confirmă parola", anchor="w").pack(fill="x")
        self._confirm = ctk.CTkEntry(form, show="•")
        self._confirm.pack(fill="x", pady=(2, 10))

        self._error = ctk.CTkLabel(self, text="", text_color="red", wraplength=340)
        self._error.pack(pady=(4, 0))

        ctk.CTkButton(self, text="Crează cont", command=self._submit).pack(
            padx=36, pady=12, fill="x")

    def _submit(self):
        u = self._username.get().strip()
        e = self._email.get().strip()
        p = self._password.get()
        c = self._confirm.get()

        if not all([u, e, p, c]):
            self._error.configure(text="Completează toate câmpurile.")
            return
        if len(u) < 3:
            self._error.configure(text="Utilizatorul trebuie să aibă cel puțin 3 caractere.")
            return
        if len(p) < 8:
            self._error.configure(text="Parola trebuie să aibă cel puțin 8 caractere.")
            return
        if p != c:
            self._error.configure(text="Parolele nu coincid.")
            return

        try:
            msg = self.client.register(u, e, p)
            messagebox.showinfo("Cont creat", msg + "\nPoți să te autentifici acum.", parent=self)
            self.destroy()
        except APIError as ex:
            self._error.configure(text=ex.detail)
        except Exception:
            self._error.configure(text="Nu s-a putut conecta la server.")


# ── Login screen ───────────────────────────────────────────────────────────────

class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, on_login):
        super().__init__(master, fg_color="transparent")
        self._app = master
        self.on_login = on_login
        self._build()

    def _build(self):
        card = ctk.CTkFrame(self, width=400, corner_radius=16)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="📚", font=ctk.CTkFont(size=52)).grid(
            row=0, column=0, pady=(36, 4))
        ctk.CTkLabel(card, text="Corporate RAG",
                     font=ctk.CTkFont(size=26, weight="bold")).grid(row=1, column=0)
        ctk.CTkLabel(card, text="Autentifică-te pentru a continua",
                     text_color="gray").grid(row=2, column=0, pady=(4, 28))

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.grid(row=3, column=0, padx=36, sticky="ew")
        form.columnconfigure(0, weight=1)

        ctk.CTkLabel(form, text="Utilizator sau email", anchor="w").grid(
            row=0, column=0, sticky="w")
        self._identifier = ctk.CTkEntry(form)
        self._identifier.grid(row=1, column=0, sticky="ew", pady=(2, 12))

        ctk.CTkLabel(form, text="Parolă", anchor="w").grid(row=2, column=0, sticky="w")
        self._password = ctk.CTkEntry(form, show="•")
        self._password.grid(row=3, column=0, sticky="ew", pady=(2, 4))
        self._password.bind("<Return>", lambda _e: self._login())

        self._error = ctk.CTkLabel(card, text="", text_color="red", wraplength=340)
        self._error.grid(row=4, column=0, pady=6)

        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.grid(row=5, column=0, padx=36, sticky="ew", pady=(0, 8))
        btns.columnconfigure(0, weight=1)

        ctk.CTkButton(btns, text="Intră în cont", command=self._login).grid(
            row=0, column=0, sticky="ew", pady=(0, 6))
        ctk.CTkButton(btns, text="Crează cont", fg_color="transparent",
                      border_width=1, command=self._open_register).grid(
            row=1, column=0, sticky="ew")

        # Server URL
        srv = ctk.CTkFrame(card, fg_color="transparent")
        srv.grid(row=6, column=0, padx=36, sticky="ew", pady=(12, 28))
        srv.columnconfigure(1, weight=1)
        ctk.CTkLabel(srv, text="Server:", text_color="gray",
                     font=ctk.CTkFont(size=11)).grid(row=0, column=0, padx=(0, 6))
        self._server_entry = ctk.CTkEntry(srv, font=ctk.CTkFont(size=11), height=26)
        self._server_entry.insert(0, self._app.server_url)
        self._server_entry.grid(row=0, column=1, sticky="ew")

    def _client(self) -> RAGClient:
        url = self._server_entry.get().strip() or DEFAULT_SERVER
        self._app.server_url = url
        return RAGClient(url)

    def _login(self):
        identifier = self._identifier.get().strip()
        password = self._password.get()
        if not identifier or not password:
            self._error.configure(text="Completează toate câmpurile.")
            return
        try:
            token, username = self._client().login(identifier, password)
            self.on_login(username, token)
        except APIError as ex:
            self._error.configure(text=ex.detail)
        except Exception:
            self._error.configure(text="Nu s-a putut conecta la server.")

    def _open_register(self):
        RegisterDialog(self, self._client())


# ── Main screen ────────────────────────────────────────────────────────────────

class MainFrame(ctk.CTkFrame):
    def __init__(self, master, client: RAGClient, username: str, on_logout):
        super().__init__(master, fg_color="transparent")
        self.client = client
        self.username = username
        self.on_logout = on_logout
        self._pending_files: list[str] = []
        self._build()

    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Top bar ────────────────────────────────────────────────────────────
        top = ctk.CTkFrame(self, height=50, corner_radius=0)
        top.grid(row=0, column=0, columnspan=2, sticky="ew")
        top.grid_propagate(False)
        top.columnconfigure(1, weight=1)

        ctk.CTkLabel(top, text="📚 Corporate RAG",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, padx=16, pady=14)
        ctk.CTkLabel(top, text=f"Conectat ca: {self.username}",
                     text_color="gray").grid(row=0, column=1, sticky="e", padx=8)
        ctk.CTkButton(top, text="Deconectare", width=120,
                      fg_color="transparent", border_width=1,
                      command=self._logout).grid(row=0, column=2, padx=16, pady=10)

        # ── Left sidebar — documents ───────────────────────────────────────────
        sidebar = ctk.CTkFrame(self, width=270, corner_radius=0)
        sidebar.grid(row=1, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.columnconfigure(0, weight=1)

        ctk.CTkLabel(sidebar, text="Documente",
                     font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, padx=16, pady=(20, 8), sticky="w")

        ctk.CTkButton(sidebar, text="+ Selectează fișiere",
                      command=self._pick_files).grid(
            row=1, column=0, padx=16, sticky="ew")

        self._file_list = ctk.CTkTextbox(sidebar, height=200, state="disabled",
                                         font=ctk.CTkFont(size=11))
        self._file_list.grid(row=2, column=0, padx=16, pady=(8, 4), sticky="ew")

        self._vectorize_btn = ctk.CTkButton(sidebar, text="Vectorizează",
                                            command=self._vectorize)
        self._vectorize_btn.grid(row=3, column=0, padx=16, pady=(4, 0), sticky="ew")

        self._doc_status = ctk.CTkLabel(sidebar, text="", text_color="gray",
                                        wraplength=230, font=ctk.CTkFont(size=11))
        self._doc_status.grid(row=4, column=0, padx=16, pady=6)

        # ── Right panel — chat ─────────────────────────────────────────────────
        chat = ctk.CTkFrame(self, fg_color="transparent")
        chat.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        chat.grid_columnconfigure(0, weight=1)
        chat.grid_rowconfigure(0, weight=1)

        self._chat_box = ctk.CTkTextbox(chat, state="disabled", wrap="word",
                                        font=ctk.CTkFont(size=13))
        self._chat_box.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 8))

        self._question = ctk.CTkEntry(chat, placeholder_text="Pune o întrebare…")
        self._question.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self._question.bind("<Return>", lambda _e: self._ask())

        self._ask_btn = ctk.CTkButton(chat, text="Trimite", width=100,
                                      command=self._ask)
        self._ask_btn.grid(row=1, column=1)

    # ── Document helpers ───────────────────────────────────────────────────────

    def _pick_files(self):
        paths = filedialog.askopenfilenames(
            title="Selectează documente",
            filetypes=[("Documente", "*.pdf *.docx"),
                       ("PDF", "*.pdf"), ("Word", "*.docx")],
        )
        if not paths:
            return
        self._pending_files = list(paths)
        self._file_list.configure(state="normal")
        self._file_list.delete("1.0", "end")
        for p in self._pending_files:
            self._file_list.insert("end", p.split("/")[-1] + "\n")
        self._file_list.configure(state="disabled")
        self._doc_status.configure(
            text=f"{len(paths)} fișier(e) selectate.", text_color="gray")

    def _vectorize(self):
        if not self._pending_files:
            self._doc_status.configure(text="Niciun fișier selectat.", text_color="red")
            return
        self._vectorize_btn.configure(state="disabled", text="Se procesează…")
        self._doc_status.configure(text="", text_color="gray")
        threading.Thread(target=self._vectorize_worker, daemon=True).start()

    def _vectorize_worker(self):
        try:
            files = []
            for path in self._pending_files:
                with open(path, "rb") as f:
                    content = f.read()
                name = path.split("/")[-1]
                mime = ("application/pdf" if name.endswith(".pdf")
                        else "application/vnd.openxmlformats-officedocument"
                             ".wordprocessingml.document")
                files.append((name, content, mime))
            self.client.upload_documents(files)
            count = self.client.process_documents()
            self.after(0, self._vectorize_done,
                       f"✓ {count} document(e) vectorizate.", "green")
        except APIError as ex:
            self.after(0, self._vectorize_done, ex.detail, "red")
        except Exception:
            self.after(0, self._vectorize_done, "Eroare de conexiune.", "red")

    def _vectorize_done(self, msg: str, color: str):
        self._doc_status.configure(text=msg, text_color=color)
        self._vectorize_btn.configure(state="normal", text="Vectorizează")

    # ── Chat helpers ───────────────────────────────────────────────────────────

    def _append_chat(self, label: str, text: str):
        self._chat_box.configure(state="normal")
        self._chat_box.insert("end", f"{label}\n{text}\n\n")
        self._chat_box.configure(state="disabled")
        self._chat_box.see("end")

    def _ask(self):
        question = self._question.get().strip()
        if not question:
            return
        self._question.delete(0, "end")
        self._ask_btn.configure(state="disabled")
        self._append_chat("Tu:", question)
        threading.Thread(target=self._ask_worker, args=(question,), daemon=True).start()

    def _ask_worker(self, question: str):
        try:
            answer = self.client.query(question)
            self.after(0, self._ask_done, answer)
        except APIError as ex:
            self.after(0, self._ask_done, f"[Eroare] {ex.detail}")
        except Exception:
            self.after(0, self._ask_done, "[Eroare] Nu s-a putut conecta la server.")

    def _ask_done(self, answer: str):
        self._append_chat("RAG:", answer)
        self._ask_btn.configure(state="normal")

    # ── Logout ─────────────────────────────────────────────────────────────────

    def _logout(self):
        if messagebox.askyesno("Deconectare",
                               "Ești sigur că vrei să te deconectezi?"):
            self.on_logout()


# ── App shell ──────────────────────────────────────────────────────────────────

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Corporate RAG")
        self.geometry("980x660")
        self.minsize(820, 560)
        self.server_url = DEFAULT_SERVER
        self._frame: ctk.CTkFrame | None = None
        self._show_login()

    def _swap(self, frame: ctk.CTkFrame):
        if self._frame:
            self._frame.destroy()
        self._frame = frame
        self._frame.pack(fill="both", expand=True)

    def _show_login(self):
        self._swap(LoginFrame(self, self._on_login))

    def _on_login(self, username: str, token: str):
        client = RAGClient(self.server_url, token)
        self._swap(MainFrame(self, client, username, self._show_login))


if __name__ == "__main__":
    App().mainloop()
