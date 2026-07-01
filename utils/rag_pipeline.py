import os
import ollama
from utils.vector_store import ChromaVectorStore

MODEL_ID = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

_client = ollama.Client(host=OLLAMA_HOST)

_SYSTEM_PROMPT = """\
Ești un expert în audit și analiză de documente corporative. Misiunea ta este să oferi răspunsuri extrem de precise, bazate strict pe documentele puse la dispoziție.

REGULI OBLIGATORII:
1. Răspunde EXCLUSIV pe baza fragmentelor de context oferite mai jos.
2. Dacă informația solicitată nu se regăsește în mod explicit în context, răspunde exact cu textul: "Această informație nu se află în documentele încărcate." Nu încerca să inventezi sau să extrapolezi.
3. Răspunde direct, profesional și concis în limba română.
4. Pentru fiecare afirmație importantă din răspunsul tău, citează obligatoriu documentul sursă și pagina menționate în antetul fragmentului (ex: "[Sursa: contract.pdf, Pag. 3]").
"""

class RAGPipeline:
    def __init__(self):
        self.vector_store = ChromaVectorStore()

    def retrieve(self, query: str, k: int = 5) -> list[dict]:
        return self.vector_store.query(query, k=k)

    def generate(self, query: str, chunks: list[dict]) -> str:
        # Construim contextul îmbogățit cu metadatele reale ale fișierelor
        context_parts = []
        for i, chunk in enumerate(chunks):
            source = chunk["metadata"].get("source", "Necunoscut")
            page = chunk["metadata"].get("page", "-")
            header = f"[Fragment {i + 1} | Fișier: {source} | Pagina: {page}]"
            context_parts.append(f"{header}\n{chunk['text']}")
            
        numbered_context = "\n\n".join(context_parts)
        
        user_message = (
            f"Fragmentele autorizate din documente:\n\n{numbered_context}\n\n"
            f"---\nÎntrebare utilizator: {query}"
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
        if not chunks:
            return "Această informație nu se află în documentele încărcate."
        return self.generate(query, chunks)