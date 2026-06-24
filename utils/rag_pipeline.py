import os
import ollama
from utils.vector_store import ChromaVectorStore

MODEL_ID = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

_client = ollama.Client(host=OLLAMA_HOST)

_SYSTEM_PROMPT = (
    "Ești un asistent AI pentru documente în limba română."
    "Reguli:"
    "- Răspunde întotdeauna în limba română."
    "- Nu folosi alte limbi decât româna."
    "- Pentru întrebări bazate pe documente, folosește doar contextul primit."
    "- Dacă informația nu există în context, spune clar că nu ai găsit informația."
    "- Nu inventa informații."
)


class RAGPipeline:
    def __init__(self):
        self.vector_store = ChromaVectorStore()

    def retrieve(self, query: str, k: int = 3) -> list[str]:
        return self.vector_store.query(query, k=k)

    def generate(self, query: str, context: str) -> str:
        response = _client.chat(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": f"Context:\n{context}\n\nÎntrebare: {query}"},
            ],
        )
        return response["message"]["content"]

    def answer_query(self, query: str) -> str:
        context = self.retrieve(query)
        return self.generate(query, context=" ".join(context))
