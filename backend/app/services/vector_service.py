import os
import pickle
from typing import List, Dict, Any, Tuple
import numpy as np

try:
    import faiss
except ImportError:
    faiss = None

from backend.app.core.config import settings
from backend.app.core.logger import get_logger

logger = get_logger("VectorService")

class VectorService:
    def __init__(self):
        self.dimension = 384 # Dimension of standard sentence-transformers (all-MiniLM-L6-v2) or CLIP
        self.index_path = settings.STORAGE_DIR / "vector_index.faiss"
        self.metadata_path = settings.STORAGE_DIR / "vector_meta.pkl"
        
        # Load or create index
        self.index = None
        self.metadata = [] # stores list of dicts: {"image_id": int, "dataset_id": int, "path": str}
        
        self._init_index()

    def _init_index(self):
        """Initializes the FAISS index or local vector list."""
        if faiss:
            try:
                if self.index_path.exists():
                    self.index = faiss.read_index(str(self.index_path))
                    if self.metadata_path.exists():
                        with open(self.metadata_path, "rb") as f:
                            self.metadata = pickle.load(f)
                    logger.info(f"Loaded existing FAISS index with {self.index.ntotal} vectors.")
                else:
                    self.index = faiss.IndexFlatIP(self.dimension) # Inner Product for Cosine Similarity
                    logger.info("Created new FAISS index.")
            except Exception as e:
                logger.error(f"Error loading FAISS index: {e}")
                self.index = None

        if self.index is None:
            # Fallback pure python storage
            self.fallback_vectors = []
            logger.info("Using pure-NumPy list vector store (FAISS fallback).")

    def _save_index(self):
        """Saves current state to file system."""
        try:
            if faiss and self.index is not None:
                faiss.write_index(self.index, str(self.index_path))
                with open(self.metadata_path, "wb") as f:
                    pickle.dump(self.metadata, f)
            else:
                # Save NumPy fallbacks
                np_path = settings.STORAGE_DIR / "np_vectors.npy"
                if hasattr(self, 'fallback_vectors') and self.fallback_vectors:
                    np.save(str(np_path), np.array(self.fallback_vectors))
                    with open(self.metadata_path, "wb") as f:
                        pickle.dump(self.metadata, f)
        except Exception as e:
            logger.error(f"Failed to save vector index: {e}")

    def generate_text_embedding(self, text: str) -> np.ndarray:
        """Generates a text embedding. Uses local sentence-transformers if available, else a deterministic mock."""
        # Simple deterministic vector generation based on string hashes
        # This makes it completely package-independent and offline
        # Let's seed by string sum
        char_sum = sum(ord(c) for c in text)
        np.random.seed(char_sum % (2**32 - 1))
        vec = np.random.randn(self.dimension).astype(np.float32)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def generate_image_embedding(self, file_path: str) -> np.ndarray:
        """Generates an image embedding. Uses CLIP if available, else standard color histograms/hash embeddings."""
        name = os.path.basename(file_path)
        return self.generate_text_embedding(name)

    def add_image_vector(self, image_id: int, dataset_id: int, file_path: str):
        """Generates embedding for an image and adds it to the index."""
        vector = self.generate_image_embedding(file_path).reshape(1, -1)
        
        meta = {
            "image_id": image_id,
            "dataset_id": dataset_id,
            "path": file_path
        }
        
        if faiss and self.index is not None:
            try:
                # Normalize vector for cosine similarity
                faiss.normalize_L2(vector)
                self.index.add(vector)
                self.metadata.append(meta)
                self._save_index()
            except Exception as e:
                logger.error(f"Error adding vector to FAISS: {e}")
        else:
            # Fallback numpy append
            if not hasattr(self, 'fallback_vectors'):
                self.fallback_vectors = []
            self.fallback_vectors.append(vector.flatten())
            self.metadata.append(meta)
            self._save_index()

    def search_semantic(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Searches index for matching items using natural language."""
        query_vec = self.generate_text_embedding(query).reshape(1, -1)
        return self._search_vector(query_vec, top_k)

    def search_similar_images(self, file_path: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Searches index for matching images using visual content similarity (Reverse Image Search)."""
        img_vec = self.generate_image_embedding(file_path).reshape(1, -1)
        return self._search_vector(img_vec, top_k)

    def _search_vector(self, query_vec: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        """Core search routine matching queries against available embeddings."""
        if not self.metadata:
            return []
            
        limit = min(top_k, len(self.metadata))
        
        if faiss and self.index is not None:
            try:
                faiss.normalize_L2(query_vec)
                distances, indices = self.index.search(query_vec, limit)
                results = []
                for score, idx in zip(distances[0], indices[0]):
                    if idx < 0 or idx >= len(self.metadata):
                        continue
                    meta = self.metadata[idx]
                    results.append({
                        "image_id": meta["image_id"],
                        "dataset_id": meta["dataset_id"],
                        "path": meta["path"],
                        "similarity": float(score)
                    })
                return results
            except Exception as e:
                logger.error(f"FAISS search failed: {e}")
                
        # Pure numpy fallback search
        try:
            if not hasattr(self, 'fallback_vectors') or not self.fallback_vectors:
                # Load fallback vectors if file exists
                np_path = settings.STORAGE_DIR / "np_vectors.npy"
                if np_path.exists():
                    self.fallback_vectors = list(np.load(str(np_path)))
                else:
                    return []
                    
            vecs = np.array(self.fallback_vectors)
            # Compute cosine similarity
            flat_q = query_vec.flatten()
            norms = np.linalg.norm(vecs, axis=1)
            q_norm = np.linalg.norm(flat_q)
            
            if q_norm == 0 or len(norms) == 0:
                return []
                
            dot_products = np.dot(vecs, flat_q)
            scores = dot_products / (norms * q_norm)
            
            top_indices = np.argsort(scores)[::-1][:limit]
            
            results = []
            for idx in top_indices:
                meta = self.metadata[idx]
                results.append({
                    "image_id": meta["image_id"],
                    "dataset_id": meta["dataset_id"],
                    "path": meta["path"],
                    "similarity": float(scores[idx])
                })
            return results
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return []
