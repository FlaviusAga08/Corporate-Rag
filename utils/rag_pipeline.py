import os
import ollama
from utils.vector_store import ChromaVectorStore

MODEL_ID = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

_client = ollama.Client(host=OLLAMA_HOST)

_SYSTEM_PROMPT = """\
Ești un asistent specializat în analiza documentelor corporative în limba română.

REGULI STRICTE:
1. Răspunde EXCLUSIV pe baza fragmentelor de context numerotate de mai jos.
2. Dacă informația nu se regăsește în context, răspunde exact: "Această informație nu se află în documentele încărcate."
3. Nu folosi cunoștințe generale sau informații din afara contextului.
4. Răspunde întotdeauna în limba română.
5. Când citezi o informație, menționează din ce fragment provine (ex: "Conform fragmentului 2, ...").
6. Fii specific și concis — nu da răspunsuri vagi.\
"""


class RAGPipeline:
    def __init__(self):
        self.vector_store = ChromaVectorStore()

    def retrieve(self, query: str, k: int = 5) -> list[str]:
        return self.vector_store.query(query, k=k)

    def generate(self, query: str, chunks: list[str]) -> str:
        numbered = "\n\n".join(
            f"[Fragment {i + 1}]\n{chunk}" for i, chunk in enumerate(chunks)
        )
        user_message = (
            f"Fragmentele din documente:\n\n{numbered}\n\n"
            f"---\nÎntrebare: {query}"
        )
        response = _client.chat(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
        return response["message"]["content"]

    def answer_query(self, query: str) -> str:
        chunks = self.retrieve(query)
        return self.generate(query, chunks)
