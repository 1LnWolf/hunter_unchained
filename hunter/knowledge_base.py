from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import numpy as np

class KnowledgeBase:
    def __init__(self, config):
        self.config = config
        self.client = PersistentClient(path=config["knowledge"]["vector_store_path"])
        self.embedder = SentenceTransformer(config["knowledge"]["embedding_model"])
        self.collection = self.client.get_or_create_collection("security_knowledge")
        self.hybrid_weight = config["knowledge"].get("hybrid_weight", 0.5)
        self._build_bm25_index()

    def _build_bm25_index(self):
        all_docs = self.collection.get()["documents"]
        self.corpus = all_docs
        tokenized_corpus = [doc.lower().split() for doc in all_docs]
        self.bm25 = BM25Okapi(tokenized_corpus) if tokenized_corpus else None

    def add_documents(self, docs, metadatas=None):
        if not docs:
            return
        embeddings = self.embedder.encode(docs).tolist()
        ids = [str(hash(d)) for d in docs]
        self.collection.add(embeddings=embeddings, documents=docs, metadatas=metadatas, ids=ids)
        self._build_bm25_index()

    def retrieve_relevant(self, query, k=5):
        query_emb = self.embedder.encode([query]).tolist()
        dense_results = self.collection.query(query_embeddings=query_emb, n_results=k)
        dense_docs = dense_results.get("documents", [[]])[0]
        dense_distances = dense_results.get("distances", [[]])[0]

        if self.bm25 and self.corpus:
            tokenized_query = query.lower().split()
            sparse_scores = self.bm25.get_scores(tokenized_query)
            sparse_top_indices = np.argsort(sparse_scores)[::-1][:k]
            sparse_docs = [self.corpus[i] for i in sparse_top_indices]
            sparse_score_values = [sparse_scores[i] for i in sparse_top_indices]
        else:
            sparse_docs, sparse_score_values = [], []

        dense_sims = [1 - (d / 2) for d in dense_distances] if dense_distances else []
        max_dense = max(dense_sims) if dense_sims else 1
        dense_norm = [s / max_dense for s in dense_sims]

        max_sparse = max(sparse_score_values) if sparse_score_values else 1
        sparse_norm = [s / max_sparse for s in sparse_score_values]

        doc_weights = {}
        for doc, score in zip(dense_docs, dense_norm):
            doc_weights[doc] = doc_weights.get(doc, 0) + self.hybrid_weight * score
        for doc, score in zip(sparse_docs, sparse_norm):
            doc_weights[doc] = doc_weights.get(doc, 0) + (1 - self.hybrid_weight) * score

        sorted_docs = sorted(doc_weights.items(), key=lambda x: x[1], reverse=True)[:k]
        return "\n".join([doc for doc, _ in sorted_docs])

    async def close(self):
        pass