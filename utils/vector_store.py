import uuid
from typing import List

import chromadb
from sentence_transformers import SentenceTransformer


class ChromaVectorStore:
    def __init__(self, collection_name: str = "rag_collection"):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(name=collection_name)
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    def add_documents(self, documents: List[str], metadatas: List[dict] = None):
        embeddings = self.embedding_model.encode(documents).tolist()
        ids = [str(uuid.uuid4()) for _ in documents]
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas or [{} for _ in documents],
            ids=ids,
        )

    def query(self, query: str, k: int = 3) -> List[str]:
        query_embedding = self.embedding_model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
        )
        return results["documents"][0]
