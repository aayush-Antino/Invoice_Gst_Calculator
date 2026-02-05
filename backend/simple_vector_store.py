import pickle
import os
import numpy as np

class SimpleVectorStore:
    def __init__(self, path: str):
        self.path = path
        self.data = {"documents": [], "embeddings": [], "ids": []}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "rb") as f:
                    self.data = pickle.load(f)
                print(f"Loaded vector store from {self.path} with {len(self.data['ids'])} documents.")
            except Exception as e:
                print(f"Error loading vector store: {e}")
                self.data = {"documents": [], "embeddings": [], "ids": []}
        else:
            print(f"Created new vector store at {self.path}")

    def _save(self):
        try:
            with open(self.path, "wb") as f:
                pickle.dump(self.data, f)
            print(f"Saved vector store to {self.path}")
        except Exception as e:
            print(f"Error saving vector store: {e}")

    def upsert(self, documents: list[str], embeddings: list[list[float]], ids: list[str]):
        # Simple implementation: overwrite if id exists, else append
        for doc, emb, doc_id in zip(documents, embeddings, ids):
            if doc_id in self.data["ids"]:
                # Update existing
                idx = self.data["ids"].index(doc_id)
                self.data["documents"][idx] = doc
                self.data["embeddings"][idx] = emb
            else:
                # Append new
                self.data["documents"].append(doc)
                self.data["embeddings"].append(emb)
                self.data["ids"].append(doc_id)
        self._save()

    def delete(self, ids: list[str]):
        for doc_id in ids:
            if doc_id in self.data["ids"]:
                idx = self.data["ids"].index(doc_id)
                self.data["documents"].pop(idx)
                self.data["embeddings"].pop(idx)
                self.data["ids"].pop(idx)
        self._save()

    def query(self, query_embeddings: list[list[float]], n_results: int = 3):
        results = {"ids": [], "documents": [], "distances": []}
        
        if not self.data["embeddings"]:
            return {"ids": [[]], "documents": [[]], "distances": [[]]}

        db_embeddings = np.array(self.data["embeddings"])
        
        for q_emb in query_embeddings:
            q_emb = np.array(q_emb)
            # Cosine similarity
            norm_q = np.linalg.norm(q_emb)
            norm_db = np.linalg.norm(db_embeddings, axis=1)
            
            # Avoid division by zero
            if norm_q == 0:
                # Should typically not happen with valid embeddings
                results["ids"].append([])
                results["documents"].append([])
                continue
                
            # Element-wise division for broadcasting, handle zero norms in DB
            with np.errstate(divide='ignore', invalid='ignore'):
                 similarities = np.dot(db_embeddings, q_emb) / (norm_db * norm_q)
            
            # Replace NaNs with -1 (least similar)
            similarities = np.nan_to_num(similarities, nan=-1.0)
            
            # Get top k indices
            # If we have fewer documents than n_results, return all
            k = min(n_results, len(self.data["ids"]))
            top_k_indices = np.argsort(similarities)[::-1][:k]
            
            results["ids"].append([self.data["ids"][i] for i in top_k_indices])
            results["documents"].append([self.data["documents"][i] for i in top_k_indices])
            # sim to dist not strictly needed but good for compatibility if we used it
            results["distances"].append([1 - similarities[i] for i in top_k_indices]) 
            
        return results
