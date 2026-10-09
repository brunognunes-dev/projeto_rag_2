import numpy as np
from supabase import create_client, Client
from config import config

class DatabaseManager:
    def __init__(self):
        self.client: Client = None
        self._init_client()
        # In-memory backup cache to guarantee Top-K similarity retrieval if remote table isn't created via SQL migration
        self.vector_store = []

    def _init_client(self):
        if config.SUPABASE_URL and config.SUPABASE_KEY:
            try:
                self.client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
                print("[Database] Supabase client initialized.")
            except Exception as e:
                print(f"[Database] Connection error: {e}")

    def clear_documents(self):
        """Clear indexed documents."""
        self.vector_store = []
        if self.client:
            try:
                self.client.table("rag_documents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            except Exception as e:
                # If table doesn't exist yet, catch silently
                pass

    def save_chunk(self, doc_name: str, chunk_index: int, content: str, metadata: dict, embedding: list[float]):
        record = {
            "document_name": doc_name,
            "chunk_index": chunk_index,
            "content": content,
            "metadata": metadata,
            "embedding": embedding
        }
        # Always store in memory cache for instant similarity math
        self.vector_store.append(record)

        # Attempt remote Supabase insert
        if self.client:
            try:
                self.client.table("rag_documents").insert({
                    "document_name": doc_name,
                    "chunk_index": chunk_index,
                    "content": content,
                    "metadata": metadata,
                    "embedding": embedding
                }).execute()
            except Exception as e:
                # Table rag_documents might need creation or RPC setup
                print(f"[Database] Remote table sync notice: {str(e)[:100]}")

    def search_similar(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """Performs cosine similarity search over stored vectors and returns top_k candidates with scores."""
        if not self.vector_store:
            return []

        q_vec = np.array(query_embedding, dtype=np.float32)
        norm_q = np.linalg.norm(q_vec)
        if norm_q == 0:
            return []

        results = []
        for doc in self.vector_store:
            d_vec = np.array(doc["embedding"], dtype=np.float32)
            norm_d = np.linalg.norm(d_vec)
            if norm_d == 0:
                score = 0.0
            else:
                score = float(np.dot(q_vec, d_vec) / (norm_q * norm_d))
            
            results.append({
                "score": round(score, 4),
                "document_name": doc["document_name"],
                "chunk_index": doc["chunk_index"],
                "content": doc["content"],
                "metadata": doc["metadata"]
            })

        # Sort descending by score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

db_manager = DatabaseManager()
