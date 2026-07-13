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

    # Modifică metodele din clasa ChromaVectorStore în utils/vector_store.py

    def add_documents(self, chunks: List[dict]):
        # Remove the old collection if it exists
        try:
            self.client.delete_collection(self.collection.name)
        except Exception:
            pass

        # Create a fresh collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name
        )

        documents = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        embeddings = self.embedding_model.encode(
            documents,
            batch_size=32,
            show_progress_bar=True
        ).tolist()

        ids = [str(uuid.uuid4()) for _ in documents]

        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

    def query(self, query: str, k: int = 5) -> List[dict]:
        query_embedding = self.embedding_model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        
        # Scoatem filtrarea rigidă 'if dist < DISTANCE_THRESHOLD'
        # Returnăm direct top K cele mai apropiate fragmente găsite
        return [
            {"text": doc, "metadata": meta}
            for doc, meta in zip(documents, metadatas)
        ]