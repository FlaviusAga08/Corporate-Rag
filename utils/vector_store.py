import uuid
from typing import List

import chromadb
from sentence_transformers import SentenceTransformer

DISTANCE_THRESHOLD = 1.2  # l2 distance — above this the chunk is considered irrelevant


class ChromaVectorStore:
    def __init__(self, collection_name: str = "rag_collection"):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(name=collection_name)
        self.embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    def add_documents(self, documents: List[str], metadatas: List[dict] = None):
        embeddings = self.embedding_model.encode(documents).tolist()
        ids = [str(uuid.uuid4()) for _ in documents]
        kwargs = dict(documents=documents, embeddings=embeddings, ids=ids)
        if metadatas:
            kwargs["metadatas"] = metadatas
        self.collection.add(**kwargs)

    def query(self, query: str, k: int = 5) -> List[str]:
        query_embedding = self.embedding_model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "distances"],
        )
        documents = results["documents"][0]
        distances = results["distances"][0]
        return [
            doc for doc, dist in zip(documents, distances)
            if dist < DISTANCE_THRESHOLD
        ]
