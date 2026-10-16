import numpy as np
from supabase import create_client, Client
from src.core.config import config

class DatabaseManager:
    def __init__(self):
        self.client: Client = None
        # Vector store in-memory cache for fast similarity computation
        self.vector_store = []
        self._init_client()
        # Automatically restore persisted chunks from Supabase on startup
        self.load_persisted_chunks()

    def _init_client(self):
        if config.SUPABASE_URL and config.SUPABASE_KEY:
            try:
                self.client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
                print("[Database] Supabase client initialized.")
            except Exception as e:
                print(f"[Database] Connection error: {e}")

    def load_persisted_chunks(self) -> int:
        """Loads all documents and vectors already saved in Supabase into vector_store cache."""
        if not self.client:
            return 0
        try:
            res = self.client.table("documents").select("*").execute()
            rows = res.data or []
            loaded = []
            for row in rows:
                meta = row.get("metadata") or {}
                # Restore chunk
                loaded.append({
                    "id": row.get("id"),
                    "document_name": meta.get("document_name", "document.pdf"),
                    "chunk_index": meta.get("chunk_index", 1),
                    "content": row.get("content", ""),
                    "metadata": meta.get("fields") or meta,
                    "embedding": meta.get("embedding", [])
                })
            self.vector_store = loaded
            print(f"[Database] Carregados {len(loaded)} chunks persistentes do Supabase.")
            return len(loaded)
        except Exception as e:
            print(f"[Database] Notice ao carregar chunks do Supabase: {e}")
            return 0

    def clear_documents(self):
        """Clear indexed documents both in memory and permanently in Supabase."""
        self.vector_store = []
        if self.client:
            try:
                self.client.table("documents").delete().neq("id", -1).execute()
                print("[Database] Tabela 'documents' limpa no Supabase.")
            except Exception as e:
                print(f"[Database] Notice ao limpar 'documents': {e}")

    def save_chunk(self, doc_name: str, chunk_index: int, content: str, metadata: dict, embedding: list[float]):
        record = {
            "document_name": doc_name,
            "chunk_index": chunk_index,
            "content": content,
            "metadata": metadata,
            "embedding": embedding
        }
        # In-memory cache for fast search
        self.vector_store.append(record)

        # Permanent persistence in Supabase table 'documents'
        if self.client:
            try:
                self.client.table("documents").insert({
                    "content": content,
                    "metadata": {
                        "document_name": doc_name,
                        "chunk_index": chunk_index,
                        "fields": metadata,
                        "embedding": embedding
                    }
                }).execute()
            except Exception as e:
                print(f"[Database] Supabase insert notice: {str(e)[:150]}")

    def upload_file_to_storage(self, file_name: str, file_bytes: bytes, content_type: str = "application/pdf") -> str:
        """Uploads document file permanently to Supabase Storage bucket 'documents'."""
        if not self.client:
            return ""
        try:
            bucket_name = "documents"
            # Ensure bucket exists
            try:
                self.client.storage.get_bucket(bucket_name)
            except Exception:
                try:
                    self.client.storage.create_bucket(bucket_name, options={"public": True})
                except Exception:
                    pass

            self.client.storage.from_(bucket_name).upload(
                path=file_name,
                file=file_bytes,
                file_options={"upsert": "true", "content-type": content_type}
            )
            # Retrieve public or storage URL
            public_url = self.client.storage.from_(bucket_name).get_public_url(file_name)
            print(f"[Database] Arquivo '{file_name}' salvo permanentemente no Supabase Storage: {public_url}")
            return public_url
        except Exception as e:
            print(f"[Database] Notice upload storage: {e}")
            return ""

    def search_similar(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """Performs cosine similarity search over stored vectors and returns top_k candidates with scores."""
        if not self.vector_store:
            # Try reloading from Supabase if cache was empty
            self.load_persisted_chunks()

        if not self.vector_store:
            return []

        q_vec = np.array(query_embedding, dtype=np.float32)
        norm_q = np.linalg.norm(q_vec)
        if norm_q == 0:
            return []

        results = []
        for doc in self.vector_store:
            raw_emb = doc.get("embedding")
            if not raw_emb:
                continue
            d_vec = np.array(raw_emb, dtype=np.float32)
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
                "metadata": doc.get("metadata", {})
            })

        # Sort descending by score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

db_manager = DatabaseManager()
