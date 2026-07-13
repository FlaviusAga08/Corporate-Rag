import os
import ollama
from utils.vector_store import ChromaVectorStore

MODEL_ID = os.environ.get("OLLAMA_MODEL", "qwen3:8b")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

_client = ollama.Client(host=OLLAMA_HOST)

_SYSTEM_PROMPT = """
You are a knowledgeable AI assistant.

Your task is to answer the user's question using ONLY the information provided in the retrieved context.

Instructions:

1. Treat the retrieved context as the primary source of truth.
2. Do not use outside knowledge unless the user explicitly asks for general information.
3. If the retrieved context does not contain enough information, say:
   "The provided documents do not contain enough information to answer this question."
4. Never invent facts, numbers, dates, citations, or names.
5. If multiple retrieved documents disagree, explain the disagreement instead of choosing one.
6. Quote important passages when appropriate.
7. Be concise but complete.
8. If the answer requires multiple steps, organize it using headings and bullet points.
9. At the end of the answer, list the document(s) or source(s) that support each important claim.

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
            product = chunk["metadata"].get("product", "Nespecificat")
            header = f"[Fragment {i + 1} | Produs: {product} | Fișier: {source} | Pagina: {page}]"
            context_parts.append(f"{header}\n{chunk['text']}")
            
        numbered_context = "\n\n".join(context_parts)
        
        user_message = (
            f"Retrieved context:\n\n{numbered_context}\n\n"
            f"---\n"
            f"User question: {query}"
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
            return "This info was not found in the file."
        return self.generate(query, chunks)