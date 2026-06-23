import requests

_session = requests.Session()


class APIError(Exception):
    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class RAGClient:
    def __init__(self, base_url: str, token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _headers(self) -> dict:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def _raise(self, resp: requests.Response):
        if not resp.ok:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise APIError(detail)

    # ── Auth ───────────────────────────────────────────────────────────────────
    def register(self, username: str, email: str, password: str) -> str:
        resp = _session.post(
            f"{self.base_url}/auth/register",
            json={"username": username, "email": email, "password": password},
        )
        self._raise(resp)
        return resp.json()["message"]

    def login(self, username_or_email: str, password: str) -> tuple[str, str]:
        resp = _session.post(
            f"{self.base_url}/auth/login",
            json={"username": username_or_email, "email": "", "password": password},
        )
        self._raise(resp)
        data = resp.json()
        return data["access_token"], data["username"]

    # ── Documents ──────────────────────────────────────────────────────────────
    def upload_documents(self, files: list[tuple[str, bytes, str]]) -> list[str]:
        resp = _session.post(
            f"{self.base_url}/documents/upload",
            headers=self._headers(),
            files=[("files", (name, content, mime)) for name, content, mime in files],
        )
        self._raise(resp)
        return resp.json()["uploaded"]

    def process_documents(self) -> int:
        resp = _session.post(
            f"{self.base_url}/documents/process",
            headers=self._headers(),
        )
        self._raise(resp)
        return resp.json()["processed"]

    # ── Query ──────────────────────────────────────────────────────────────────
    def query(self, question: str) -> str:
        resp = _session.post(
            f"{self.base_url}/query",
            headers=self._headers(),
            json={"question": question},
        )
        self._raise(resp)
        return resp.json()["answer"]

    # ── Health ─────────────────────────────────────────────────────────────────
    def is_reachable(self) -> bool:
        try:
            resp = _session.get(f"{self.base_url}/health", timeout=3)
            return resp.ok
        except Exception:
            return False
