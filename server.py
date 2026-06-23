import os
import shutil
import jwt
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from utils.auth import init_db, register_user, verify_user
from utils.document_loader import load_documents
from utils.rag_pipeline import RAGPipeline

# ── Config ─────────────────────────────────────────────────────────────────────
JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 8
UPLOAD_DIR = "data/raw"

# ── App & shared state ─────────────────────────────────────────────────────────
app = FastAPI(title="Corporate RAG Server")
_rag: RAGPipeline | None = None


@app.on_event("startup")
def startup():
    global _rag
    init_db()
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    _rag = RAGPipeline()


def get_rag() -> RAGPipeline:
    return _rag


# ── JWT helpers ────────────────────────────────────────────────────────────────
def _create_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    return jwt.encode({"sub": username, "exp": expire}, JWT_SECRET, algorithm=JWT_ALGORITHM)


bearer_scheme = HTTPBearer()


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirat.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalid.")


# ── Schemas ────────────────────────────────────────────────────────────────────
class AuthRequest(BaseModel):
    username: str
    email: str = ""
    password: str


class QueryRequest(BaseModel):
    question: str


# ── Auth endpoints ─────────────────────────────────────────────────────────────
@app.post("/auth/register", status_code=201)
def register(body: AuthRequest):
    ok, message = register_user(body.username, body.email, body.password)
    if not ok:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}


@app.post("/auth/login")
def login(body: AuthRequest):
    ok, result = verify_user(body.username, body.password)
    if not ok:
        raise HTTPException(status_code=401, detail=result)
    return {"access_token": _create_token(result), "username": result}


# ── RAG endpoints ──────────────────────────────────────────────────────────────
@app.post("/query")
def query(body: QueryRequest, username: str = Depends(require_auth), rag: RAGPipeline = Depends(get_rag)):
    answer = rag.answer_query(body.question)
    return {"answer": answer}


@app.post("/documents/upload", status_code=201)
def upload_documents(
    files: list[UploadFile] = File(...),
    username: str = Depends(require_auth),
):
    saved = []
    for file in files:
        dest = os.path.join(UPLOAD_DIR, file.filename)
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
        saved.append(file.filename)
    return {"uploaded": saved}


@app.post("/documents/process")
def process_documents(username: str = Depends(require_auth), rag: RAGPipeline = Depends(get_rag)):
    documents = load_documents(UPLOAD_DIR)
    if not documents:
        raise HTTPException(status_code=400, detail="Nu există documente de procesat.")
    rag.vector_store.add_documents(documents)
    return {"processed": len(documents)}


@app.get("/health")
def health():
    return {"status": "ok"}
