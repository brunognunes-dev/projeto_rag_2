import numpy as np
from fastembed import TextEmbedding
from src.core.config import config

class EmbeddingService:
    def __init__(self):
        # Initialize FastEmbed TextEmbedding model
        print(f"[FastEmbed] Initializing model: {config.EMBEDDING_MODEL_NAME}...")
        self.model = TextEmbedding(model_name=config.EMBEDDING_MODEL_NAME)
        # Dynamic dimension check
        test_embed = list(self.model.embed(["teste conexao FastEmbed"]))[0]
        self.dimension = len(test_embed)
        print(f"[FastEmbed] Model loaded successfully! Vector dimension: {self.dimension}")

    def generate_embedding(self, text: str) -> list[float]:
        if not text or not text.strip():
            return [0.0] * self.dimension
        embeddings = list(self.model.embed([text]))
        return embeddings[0].tolist()

    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        embeddings = list(self.model.embed(texts))
        return [emb.tolist() for emb in embeddings]

# Singleton instance
embedding_service = EmbeddingService()
